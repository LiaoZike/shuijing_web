import csv
import json
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.db import OperationalError
from django.db.models import Q

from .models import Pond, PondSensor, WaterThreshold, SensorReading, WaterSimulationCron, PondAerator, PondAeratorStateLog, ArFeedLeaderboardEntry
from .simulator import run_simulation_round
from .aerators import evaluate_aerator_operations, resolve_cron_ponds
from .utils import METRIC_DEFINITIONS, default_thresholds, reading_status, calculate_stability, check_metrics_status


def visible_ponds_for(user):
    if not user.is_authenticated:
        return Pond.objects.filter(is_public_viewer=True).distinct().order_by("name")
    if user.is_staff or user.is_superuser:
        return Pond.objects.all().distinct().order_by("name")

    return Pond.objects.filter(Q(owners=user) | Q(viewers=user) | Q(is_public_viewer=True)).distinct().order_by("name")


def can_manage_pond(user, pond):
    if not pond or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    return pond.owners.filter(pk=user.pk).exists()


def can_delete_pond(user, pond):
    if not pond or not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if pond.creator:
        return pond.creator == user
    first_owner = pond.owners.order_by("id").first()
    return first_owner == user if first_owner else False


def user_display_name(user, fallback="訪客"):
    if not user or not user.is_authenticated:
        return fallback
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return full_name or user.username or user.email or fallback


def get_pond_owner_for_thresholds(pond):
    if not pond:
        return None
    if pond.creator:
        return pond.creator
    return pond.owners.order_by("id").first()


def simulation_cron_config():
    config, _ = WaterSimulationCron.objects.get_or_create(
        pk=1,
        defaults={"name": "Water simulation"},
    )
    return config


def cron_next_run_at(config):
    if not config.last_run_at:
        return timezone.now()
    return config.last_run_at + timedelta(seconds=max(1, config.interval_seconds))


def cron_next_discord_run_at(config):
    if not config.last_discord_run_at:
        return timezone.now()
    return config.last_discord_run_at + timedelta(seconds=max(1, config.discord_notify_interval_seconds))


@staff_member_required
def admin_cron_page(request):
    User = get_user_model()
    all_configs = WaterSimulationCron.objects.all().order_by("id")
    
    config_id = request.GET.get("id")
    is_new = request.GET.get("new") == "1" or config_id == "new"
    
    if is_new:
        config = WaterSimulationCron(name="New simulation")
    elif config_id:
        config = get_object_or_404(WaterSimulationCron, pk=config_id)
    else:
        config = all_configs.first()
        if not config:
            config = WaterSimulationCron.objects.create(name="Water simulation")
            all_configs = WaterSimulationCron.objects.all().order_by("id")
            
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete":
            target_id = request.POST.get("config_id")
            target_config = get_object_or_404(WaterSimulationCron, pk=target_id)
            target_config.delete()
            messages.success(request, f"Simulation config '{target_config.name}' deleted.")
            return redirect("/adminx/cron/")
            
        config.name = (request.POST.get("name") or "").strip() or config.name
        config.is_enabled = request.POST.get("is_enabled") == "on"
        
        target_user_id = request.POST.get("target_user") or None
        config.target_user = User.objects.filter(pk=target_user_id).first() if target_user_id else None
        
        try:
            config.interval_seconds = max(1, int(request.POST.get("interval_seconds") or 500))
        except ValueError:
            config.interval_seconds = 500
        try:
            config.anomaly_rate = max(0.0, min(1.0, float(request.POST.get("anomaly_rate") or 0.2)))
        except ValueError:
            config.anomaly_rate = 0.2
        try:
            config.anomaly_duration_rounds = max(1, int(request.POST.get("anomaly_duration_rounds") or 3))
        except ValueError:
            config.anomaly_duration_rounds = 3
            
        anomaly_mode = request.POST.get("anomaly_mode")
        valid_modes = {choice[0] for choice in WaterSimulationCron.ANOMALY_MODE_CHOICES}
        if anomaly_mode in valid_modes:
            config.anomaly_mode = anomaly_mode
            
        config.discord_webhook_url = (request.POST.get("discord_webhook_url") or "").strip()
        config.discord_is_enabled = request.POST.get("discord_is_enabled") == "on"
        try:
            config.discord_notify_interval_seconds = max(10, int(request.POST.get("discord_notify_interval_seconds") or 300))
        except ValueError:
            config.discord_notify_interval_seconds = 300
        try:
            config.discord_suppression_interval_seconds = max(0, int(request.POST.get("discord_suppression_interval_seconds") or 3600))
        except ValueError:
            config.discord_suppression_interval_seconds = 3600

        config.asr_url = (request.POST.get("asr_url") or "").strip()
        config.asr_backup_url = (request.POST.get("asr_backup_url") or "").strip()

        config.save()


        
        pond_ids = request.POST.getlist("ponds")
        config.ponds.set(Pond.objects.filter(pk__in=pond_ids))
        
        messages.success(request, f"Simulation settings saved for '{config.name}'.")
        return redirect(f"/adminx/cron/?id={config.pk}")
        
    selected_pond_ids = set(config.ponds.values_list("pk", flat=True))
    next_run_at = cron_next_run_at(config)
    next_run_epoch_ms = int(next_run_at.timestamp() * 1000)
    next_discord_run_at = cron_next_discord_run_at(config)
    next_discord_run_epoch_ms = int(next_discord_run_at.timestamp() * 1000)
    server_time_epoch_ms = int(timezone.now().timestamp() * 1000)
    
    return render(request, "water/admin_cron.html", {
        "config": config,
        "is_new": is_new,
        "all_configs": all_configs,
        "users": User.objects.filter(is_active=True).order_by("email", "username"),
        "ponds": Pond.objects.all().prefetch_related("owners").order_by("name"),
        "selected_pond_ids": selected_pond_ids,
        "next_run_at": next_run_at,
        "next_run_epoch_ms": next_run_epoch_ms,
        "next_discord_run_at": next_discord_run_at,
        "next_discord_run_epoch_ms": next_discord_run_epoch_ms,
        "server_time_epoch_ms": server_time_epoch_ms,
    })


@staff_member_required
@require_POST
def admin_cron_run(request):
    config_id = request.POST.get("config_id")
    if config_id:
        config = get_object_or_404(WaterSimulationCron, pk=config_id)
    else:
        config = simulation_cron_config()
        
    force = request.POST.get("force") == "1"
    force_anomaly = request.POST.get("force_anomaly") == "1"
    force_discord = request.POST.get("force_discord") == "1"
    tick_sim = request.POST.get("tick_sim") == "1"
    tick_discord = request.POST.get("tick_discord") == "1"
    
    # 1. Handle Discord alert check
    if force_discord or tick_discord:
        if tick_discord:
            if not config.discord_is_enabled:
                return JsonResponse({
                    "status": "disabled",
                    "message": "Discord cron is disabled.",
                    "next_discord_run_epoch_ms": int(cron_next_discord_run_at(config).timestamp() * 1000),
                    "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
                })
            now = timezone.now()
            next_discord_run = cron_next_discord_run_at(config)
            if now < next_discord_run:
                return JsonResponse({
                    "status": "waiting",
                    "message": "Not due yet.",
                    "next_discord_run_epoch_ms": int(next_discord_run.timestamp() * 1000),
                    "server_time_epoch_ms": int(now.timestamp() * 1000),
                })

        try:
            from scratch.discord_notify import check_and_trigger_discord_alerts
            alert_result = check_and_trigger_discord_alerts(config, force=True)
            config.refresh_from_db()
            aerator_summary = alert_result.get("aerator_summary") or evaluate_aerator_operations(resolve_cron_ponds(config)).summary
            msg = (
                f"傳送狀態: {alert_result.get('sent_status')}。"
                f"新警報: {alert_result.get('triggered_count')} 筆，恢復: {alert_result.get('resolved_count')} 筆。"
                f"{aerator_summary}"
            )
            config.discord_last_result = msg
            config.save(update_fields=["discord_last_result"])
        except Exception:
            import logging
            logging.getLogger("water.views").exception("Discord notification run failed")
            msg = "Discord 警報通知執行失敗。"
            config.discord_last_result = msg
            config.save(update_fields=["discord_last_result"])

        return JsonResponse({
            "status": "success",
            "message": config.discord_last_result,
            "last_discord_run_at": timezone.localtime(config.last_discord_run_at).strftime("%Y-%m-%d %H:%M:%S") if config.last_discord_run_at else "尚未判讀",
            "next_discord_run_epoch_ms": int(cron_next_discord_run_at(config).timestamp() * 1000),
            "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
        })

    # 2. Handle simulation data generation
    if tick_sim:
        if not config.is_enabled:
            return JsonResponse({
                "status": "disabled",
                "message": "Simulation cron is disabled.",
                "next_run_epoch_ms": int(cron_next_run_at(config).timestamp() * 1000),
                "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
            })
        now = timezone.now()
        next_run_at = cron_next_run_at(config)
        if now < next_run_at:
            return JsonResponse({
                "status": "waiting",
                "message": "Not due yet.",
                "next_run_epoch_ms": int(next_run_at.timestamp() * 1000),
                "server_time_epoch_ms": int(now.timestamp() * 1000),
            })

    if force or force_anomaly or tick_sim:
        try:
            result = run_simulation_round(config.pk, force=True, force_anomaly=force_anomaly)
        except OperationalError as exc:
            if "database is locked" in str(exc).lower():
                msg = "SQLite 資料庫正在被其他請求寫入，這次 cron 已略過；稍後會自動重試。"
                try:
                    config.last_result = msg
                    config.save(update_fields=["last_result"])
                except OperationalError:
                    pass
                return JsonResponse({
                    "status": "locked",
                    "message": msg,
                    "next_run_epoch_ms": int((timezone.now() + timedelta(seconds=10)).timestamp() * 1000),
                    "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
                }, status=423)
            raise
        config.refresh_from_db()
        next_run_at = cron_next_run_at(config)
        aerator_snapshot = evaluate_aerator_operations(resolve_cron_ponds(config))
        
        if result.anomaly_label == "already_run":
            return JsonResponse({
                "status": "waiting",
                "message": "Already run by another request.",
                "next_run_epoch_ms": int(next_run_at.timestamp() * 1000),
                "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
            })

        if aerator_snapshot.total:
            config.last_result = f"{config.last_result} | {aerator_snapshot.summary}"
            config.save(update_fields=["last_result"])
            
        return JsonResponse({
            "status": "success",
            "message": config.last_result,
            "created_count": result.created_count,
            "pond_count": result.pond_count,
            "sensor_count": result.sensor_count,
            "anomaly": result.anomaly_label,
            "last_run_at": timezone.localtime(config.last_run_at).strftime("%Y-%m-%d %H:%M:%S") if config.last_run_at else "",
            "next_run_epoch_ms": int(next_run_at.timestamp() * 1000),
            "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
        })

    # 3. Fallback
    next_run_at = cron_next_run_at(config)
    return JsonResponse({
        "status": "waiting",
        "message": "No action specified.",
        "next_run_epoch_ms": int(next_run_at.timestamp() * 1000),
        "server_time_epoch_ms": int(timezone.now().timestamp() * 1000),
    })




def parse_float(value):
    value = (value or "").strip()
    if value == "":
        return None
    return float(value)


def parse_position(value, fallback):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(0, min(100, parsed))


def threshold_map_for(user, pond, sensor=None):
    threshold_map = default_thresholds()
    if not pond:
        return threshold_map

    target_user = get_pond_owner_for_thresholds(pond) or user
    if not getattr(target_user, "is_authenticated", False):
        return threshold_map

    if sensor is not None:
        qs = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=sensor)
    else:
        qs = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor__isnull=True)

    for threshold in qs:
        threshold_map[threshold.metric] = {
            "min": threshold.min_value,
            "max": threshold.max_value,
        }
    return threshold_map


def save_thresholds(request, pond):
    if not can_manage_pond(request.user, pond):
        messages.error(request, "你沒有權限修改此池區的警戒值。")
        return {"status": "error", "message": "你沒有權限修改此池區的警戒值。"}

    sensor_id = request.POST.get("sensor_id") or "default"
    sensor = None
    if sensor_id != "default":
        sensor = PondSensor.objects.filter(pk=sensor_id, pond=pond).first()

    # Determine target user for storing threshold
    target_user = get_pond_owner_for_thresholds(pond) or request.user

    has_error = False

    for metric in METRIC_DEFINITIONS:
        key = metric["key"]
        try:
            min_value = parse_float(request.POST.get(f"{key}_min"))
            max_value = parse_float(request.POST.get(f"{key}_max"))
        except ValueError:
            messages.error(request, f"{metric['label']} 的閾值請輸入數字。")
            has_error = True
            continue

        if min_value is not None and max_value is not None and min_value > max_value:
            messages.error(request, f"{metric['label']} 的下限不能大於上限。")
            has_error = True
            continue

        if min_value is None and max_value is None:
            # If both are empty, delete the threshold override to revert to default
            WaterThreshold.objects.filter(
                user=target_user,
                pond=pond,
                sensor=sensor,
                metric=key,
            ).delete()
        else:
            WaterThreshold.objects.update_or_create(
                user=target_user,
                pond=pond,
                sensor=sensor,
                metric=key,
                defaults={"min_value": min_value, "max_value": max_value},
            )

    if has_error:
        return {"status": "error", "message": "警戒值格式有誤，請檢查輸入。"}

    messages.success(request, "水質警戒值已更新。")


def add_sensor(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的感測器配置。"}

    name = (request.POST.get("sensor_name") or "").strip()
    sensor_type = request.POST.get("sensor_type") or "multi"

    if not name:
        return {"status": "error", "message": "請輸入感測器名稱。"}

    valid_types = {choice[0] for choice in PondSensor.SENSOR_TYPE_CHOICES}
    if sensor_type not in valid_types:
        sensor_type = "multi"

    sensor = PondSensor.objects.create(
        pond=pond,
        name=name,
        sensor_type=sensor_type,
        x_position=parse_position(request.POST.get("x_position"), 50),
        y_position=parse_position(request.POST.get("y_position"), 50),
    )
    return {"status": "success", "message": "感測器已加入池區地圖。", "sensor": sensor}


def update_sensor(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的感測器配置。"}

    sensor = PondSensor.objects.filter(pk=request.POST.get("sensor_id"), pond=pond).first()
    if not sensor:
        return {"status": "error", "message": "找不到指定的感測器。"}

    name = (request.POST.get("sensor_name") or "").strip()
    sensor.name = name or sensor.name
    sensor.sensor_type = request.POST.get("sensor_type") or sensor.sensor_type
    sensor.x_position = parse_position(request.POST.get("x_position"), sensor.x_position)
    sensor.y_position = parse_position(request.POST.get("y_position"), sensor.y_position)
    
    is_active_val = request.POST.get("is_active")
    if is_active_val is not None:
        sensor.is_active = is_active_val in ("on", "true", "1")
        
    sensor.save()
    return {"status": "success", "message": "感測器位置與設定已更新。", "sensor": sensor}


def delete_sensor(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的感測器配置。"}

    sensor = PondSensor.objects.filter(pk=request.POST.get("sensor_id"), pond=pond).first()
    if not sensor:
        return {"status": "error", "message": "找不到指定的感測器。"}

    sensor_id = sensor.pk
    sensor_name = sensor.name
    sensor.delete()
    return {"status": "success", "message": f"感測器 {sensor_name} 已刪除。", "sensor_id": sensor_id}


def regenerate_token(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的感測器配置。"}

    sensor = PondSensor.objects.filter(pk=request.POST.get("sensor_id"), pond=pond).first()
    if not sensor:
        return {"status": "error", "message": "找不到指定的感測器。"}

    import uuid
    sensor.secret_token = uuid.uuid4().hex
    sensor.save()
    return {"status": "success", "message": f"感測器 {sensor.name} 的上傳金鑰已更新。", "sensor": sensor}


@csrf_exempt
def voice_transcribe(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "error": "Only POST method is allowed."}, status=405)
    
    audio_file = request.FILES.get("audio")
    if not audio_file:
        return JsonResponse({"status": "error", "error": "未提供音訊檔案。"}, status=400)
    
    audio_data = audio_file.read()
    
    cron_config = WaterSimulationCron.objects.first()
    urls = []
    if cron_config:
        if cron_config.asr_url:
            urls.append(cron_config.asr_url)
        if cron_config.asr_backup_url:
            urls.append(cron_config.asr_backup_url)
            
    if not urls:
        urls.append("http://127.0.0.1:8002/transcribe")
        
    last_error = "無可用或配置的語音辨識服務。"
    
    import requests
    for base_url in urls:
        base_url = base_url.strip()
        if not base_url:
            continue
            
        endpoint = base_url
        if ".modal.run" in endpoint:
            # Modal web endpoints are served at the root, do not append /transcribe
            pass
        elif not endpoint.endswith("/transcribe"):
            if endpoint.endswith("/"):
                endpoint += "transcribe"
            else:
                endpoint += "/transcribe"
                
        try:
            res = requests.post(
                endpoint,
                data=audio_data,
                headers={"Content-Type": audio_file.content_type or "audio/webm"},
                timeout=60
            )
            if res.status_code == 200:
                return JsonResponse(res.json())
            else:
                last_error = f"ASR 服務回應錯誤碼: {res.status_code}"
        except Exception as e:
            last_error = f"連線 ASR 服務失敗: {str(e)}"
            
    return JsonResponse({"status": "error", "error": last_error}, status=503)


def add_aerator(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的水車配置。"}

    name = (request.POST.get("aerator_name") or "").strip()
    if not name:
        return {"status": "error", "message": "請輸入水車名稱。"}

    aerator = PondAerator.objects.create(
        pond=pond,
        name=name,
        x_position=parse_position(request.POST.get("x_position"), 50),
        y_position=parse_position(request.POST.get("y_position"), 50),
    )
    return {"status": "success", "message": "水車已加入池區地圖。", "aerator": aerator}


def update_aerator(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的水車配置。"}

    aerator = PondAerator.objects.filter(pk=request.POST.get("aerator_id"), pond=pond).first()
    if not aerator:
        return {"status": "error", "message": "找不到指定的水車。"}

    name = (request.POST.get("aerator_name") or "").strip()
    aerator.name = name or aerator.name
    aerator.x_position = parse_position(request.POST.get("x_position"), aerator.x_position)
    aerator.y_position = parse_position(request.POST.get("y_position"), aerator.y_position)
    
    is_active_val = request.POST.get("is_active")
    if is_active_val is not None:
        aerator.is_active = is_active_val in ("on", "true", "1")
        if not aerator.is_active:
            aerator.last_is_operating = False
            aerator.last_evaluation_reason = "水車已停用。"

    rules_json = request.POST.get("rules")
    if rules_json is not None:
        try:
            rules = json.loads(rules_json)
            aerator.rules = rules
        except json.JSONDecodeError:
            pass

    aerator.save()
    return {"status": "success", "message": "水車設定與規則已更新。", "aerator": aerator}


def delete_aerator(request, pond):
    if not can_manage_pond(request.user, pond):
        return {"status": "error", "message": "你尚未被授權編輯此池區的水車配置。"}

    aerator = PondAerator.objects.filter(pk=request.POST.get("aerator_id"), pond=pond).first()
    if not aerator:
        return {"status": "error", "message": "找不到指定的水車。"}

    aerator_id = aerator.pk
    aerator_name = aerator.name
    aerator.delete()
    return {"status": "success", "message": f"水車 {aerator_name} 已刪除。", "aerator_id": aerator_id}


def pond_list(request):
    """顯示所有池區的網格視圖（主儀表板）"""
    ponds = visible_ponds_for(request.user).prefetch_related("sensors", "owners", "aerators")
    
    pond_cards = []
    alert_count = 0
    latest_time = None

    for pond in ponds:
        threshold_map = threshold_map_for(request.user, pond)
        latest = pond.readings.first()
        status = reading_status(latest, threshold_map)

        if status["tone"] == "warning":
            alert_count += 1
        if latest and (latest_time is None or latest.measured_at > latest_time):
            latest_time = latest.measured_at

        sensor_list = []
        for sensor in pond.sensors.all():
            sensor_latest = sensor.readings.first() or latest
            sensor_list.append({
                "sensor": sensor,
                "reading": sensor_latest,
                "status": reading_status(sensor_latest, threshold_map),
                "metric_status": check_metrics_status(sensor_latest, threshold_map) if sensor_latest else {},
            })

        aerator_list = []
        for aerator in pond.aerators.all():
            aerator_list.append({
                "aerator": aerator,
                "is_operating": aerator.is_operating(),
            })

        pond_cards.append({
            "pond": pond,
            "reading": latest,
            "status": status,
            "can_manage": can_manage_pond(request.user, pond),
            "can_delete": can_delete_pond(request.user, pond),
            "sensor_cards": sensor_list,
            "aerator_cards": aerator_list,
        })

    context = {
        "pond_cards": pond_cards,
        "pond_count": len(pond_cards),
        "alert_count": alert_count,
        "latest_time": latest_time,
    }
    return render(request, "water/pond_list.html", context)


def pond_detail(request, pond_id):
    """顯示單個池區的詳細配置（感測器分布、水質數據）"""
    pond = get_object_or_404(Pond, pk=pond_id)
    
    # 檢查用戶是否可以查看此池區
    if pond not in visible_ponds_for(request.user):
        messages.error(request, "你沒有權限查看此池區。")
        return redirect("water:pond_list")

    # Determine target user for thresholds
    target_user = get_pond_owner_for_thresholds(pond) or request.user

    latest = pond.readings.first()

    # Handle AJAX GET request for telemetry auto-refresh
    is_ajax_get = request.method == "GET" and (
        request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("ajax") == "true"
    )
    if is_ajax_get:
        sensor_list = []
        for sensor in pond.sensors.all():
            sensor_latest = sensor.readings.first() or latest
            has_custom = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=sensor).exists()
            sensor_thresholds = threshold_map_for(target_user, pond, sensor=sensor if has_custom else None)
            s_status = reading_status(sensor_latest, sensor_thresholds)
            
            sensor_list.append({
                "sensor_id": sensor.pk,
                "tone": s_status["tone"],
                "label": s_status["label"],
                "message": s_status.get("message", ""),
                "metric_status": check_metrics_status(sensor_latest, sensor_thresholds) if sensor_latest else {},
                "reading": {
                    "temperature": float(sensor_latest.temperature) if sensor_latest and sensor_latest.temperature is not None else None,
                    "ph": float(sensor_latest.ph) if sensor_latest and sensor_latest.ph is not None else None,
                    "dissolved_oxygen": float(sensor_latest.dissolved_oxygen) if sensor_latest and sensor_latest.dissolved_oxygen is not None else None,
                    "ammonia_nitrogen": float(sensor_latest.ammonia_nitrogen) if sensor_latest and sensor_latest.ammonia_nitrogen is not None else None,
                    "nitrite": float(sensor_latest.nitrite) if sensor_latest and sensor_latest.nitrite is not None else None,
                } if sensor_latest else None
            })

        aerator_list = []
        for aerator in pond.aerators.all():
            aerator_list.append({
                "aerator_id": aerator.pk,
                "is_active": aerator.is_active,
                "is_operating": aerator.is_operating(),
            })

        return JsonResponse({
            "status": "success",
            "latest_measured_at": timezone.localtime(latest.measured_at).strftime("%Y/%m/%d %H:%M") if latest else "",
            "sensor_cards": sensor_list,
            "aerator_cards": aerator_list,
        })

    if request.method == "POST":
        action = request.POST.get("action")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or request.POST.get("ajax") == "true"

        result = None
        if action == "save_thresholds":
            result = save_thresholds(request, pond)
        elif action == "add_sensor":
            result = add_sensor(request, pond)
        elif action == "update_sensor":
            result = update_sensor(request, pond)
        elif action == "delete_sensor":
            result = delete_sensor(request, pond)
        elif action == "regenerate_token":
            result = regenerate_token(request, pond)
        elif action == "add_aerator":
            result = add_aerator(request, pond)
        elif action == "update_aerator":
            result = update_aerator(request, pond)
        elif action == "delete_aerator":
            result = delete_aerator(request, pond)

        if is_ajax:
            if action == "update_gates":
                if not can_manage_pond(request.user, pond):
                    return JsonResponse({"status": "error", "message": "無編輯此池區配置的權限。"}, status=403)
                inlet_x = parse_position(request.POST.get("inlet_x"), pond.inlet_x)
                inlet_y = parse_position(request.POST.get("inlet_y"), pond.inlet_y)
                outlet_x = parse_position(request.POST.get("outlet_x"), pond.outlet_x)
                outlet_y = parse_position(request.POST.get("outlet_y"), pond.outlet_y)
                pond.inlet_x = inlet_x
                pond.inlet_y = inlet_y
                pond.outlet_x = outlet_x
                pond.outlet_y = outlet_y
                pond.save()
                return JsonResponse({"status": "success", "message": "進排水口位置已更新。"})

            elif action == "delete_custom_thresholds":
                if not can_manage_pond(request.user, pond):
                    return JsonResponse({"status": "error", "message": "無編輯此池區配置的權限。"}, status=403)
                sensor_id = request.POST.get("sensor_id")
                if sensor_id:
                    WaterThreshold.objects.filter(user=target_user, pond=pond, sensor_id=sensor_id).delete()
                    return JsonResponse({"status": "success", "message": "已還原該感測器的警戒值為池區預設。"})
                return JsonResponse({"status": "error", "message": "未指定感測器。"}, status=400)

            if result:
                if result["status"] == "success":
                    sensor_data = {}
                    if "sensor" in result:
                        s = result["sensor"]
                        sensor_latest = s.readings.first() or latest
                        
                        # Find if sensor has custom thresholds
                        has_custom = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=s).exists()
                        sensor_thresholds = threshold_map_for(target_user, pond, sensor=s if has_custom else None)
                        s_status = reading_status(sensor_latest, sensor_thresholds)
                        
                        sensor_data = {
                            "id": s.pk,
                            "name": s.name,
                            "sensor_type": s.sensor_type,
                            "sensor_type_display": s.get_sensor_type_display(),
                            "x_position": s.x_position,
                            "y_position": s.y_position,
                            "is_active": s.is_active,
                            "secret_token": s.secret_token,
                            "status": s_status,
                            "has_custom_threshold": has_custom,
                            "reading": {
                                "temperature": float(sensor_latest.temperature) if sensor_latest and sensor_latest.temperature is not None else None,
                                "ph": float(sensor_latest.ph) if sensor_latest and sensor_latest.ph is not None else None,
                                "dissolved_oxygen": float(sensor_latest.dissolved_oxygen) if sensor_latest and sensor_latest.dissolved_oxygen is not None else None,
                                "ammonia_nitrogen": float(sensor_latest.ammonia_nitrogen) if sensor_latest and sensor_latest.ammonia_nitrogen is not None else None,
                                "nitrite": float(sensor_latest.nitrite) if sensor_latest and sensor_latest.nitrite is not None else None,
                            } if sensor_latest else None
                        }

                    aerator_data = {}
                    if "aerator" in result:
                        ae = result["aerator"]
                        aerator_data = {
                            "id": ae.pk,
                            "name": ae.name,
                            "x_position": ae.x_position,
                            "y_position": ae.y_position,
                            "is_active": ae.is_active,
                            "rules": ae.rules,
                            "enriched_rules": ae.get_enriched_rules(),
                            "is_operating": ae.is_operating(),
                        }

                    return JsonResponse({
                        "status": "success",
                        "message": result["message"],
                        "sensor": sensor_data,
                        "sensor_id": result.get("sensor_id"),
                        "aerator": aerator_data,
                        "aerator_id": result.get("aerator_id")
                    })
                else:
                    return JsonResponse({"status": "error", "message": result["message"]}, status=400)
            
            if action == "save_thresholds":
                return JsonResponse({"status": "success", "message": "水質警戒值已更新。"})
            return JsonResponse({"status": "error", "message": "未知的操作。"}, status=400)

        # Non-AJAX fallback (original behavior)
        if result:
            if result["status"] == "success":
                messages.success(request, result["message"])
            else:
                messages.error(request, result["message"])
        return redirect("water:pond_detail", pond_id=pond.pk)

    # GET 請求：加載池塘詳情
    pond_defaults = threshold_map_for(target_user, pond, sensor=None)
    status = reading_status(latest, pond_defaults)
    latest_stability = calculate_stability(latest, pond_defaults, pond.stability_w_do, pond.stability_w_ph, pond.stability_w_temp)

    metrics = []
    for index, metric in enumerate(METRIC_DEFINITIONS, start=1):
        value = getattr(latest, metric["key"], None) if latest else None
        limits = pond_defaults.get(metric["key"], {})
        metrics.append({
            **metric,
            "index": index,
            "value": value,
            "min": limits.get("min"),
            "max": limits.get("max"),
        })

    sensor_cards = []
    for sensor in pond.sensors.all():
        sensor_latest = sensor.readings.first() or latest
        has_custom = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=sensor).exists()
        sensor_thresholds = threshold_map_for(target_user, pond, sensor=sensor if has_custom else None)
        
        sensor_cards.append({
            "sensor": sensor,
            "reading": sensor_latest,
            "status": reading_status(sensor_latest, sensor_thresholds),
            "metric_status": check_metrics_status(sensor_latest, sensor_thresholds) if sensor_latest else {},
            "has_custom_threshold": has_custom,
        })

    # 為模板準備 pond-level default threshold 列表
    threshold_items = []
    for metric in METRIC_DEFINITIONS:
        limits = pond_defaults.get(metric["key"], {})
        threshold_items.append({
            "key": metric["key"],
            "label": metric["label"],
            "unit": metric["unit"],
            "min": limits.get("min"),
            "max": limits.get("max"),
        })

    # 產生 thresholds_json 傳遞給前端，便於在對象切換時直接無刷新填充
    base_defaults = {}
    for metric in METRIC_DEFINITIONS:
        base_defaults[metric["key"]] = {
            "min": metric["default_min"],
            "max": metric["default_max"]
        }
        
    thresholds_json = {
        "default": {
            "name": "池區預設警戒值",
            "is_custom": False,
            "values": pond_defaults
        }
    }
    
    for card in sensor_cards:
        s = card["sensor"]
        s_vals = {k: v.copy() for k, v in pond_defaults.items()}
        
        if card["has_custom_threshold"]:
            custom_qs = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=s)
            for threshold in custom_qs:
                s_vals[threshold.metric] = {
                    "min": threshold.min_value,
                    "max": threshold.max_value
                }
        thresholds_json[str(s.pk)] = {
            "name": s.name,
            "is_custom": card["has_custom_threshold"],
            "values": s_vals
        }
        
    thresholds_json_str = json.dumps(thresholds_json)

    # 獲取水車列表及運作狀態
    aerator_cards = []
    for aerator in pond.aerators.all():
        aerator_cards.append({
            "aerator": aerator,
            "is_operating": aerator.is_operating(),
        })

    context = {
        "pond": pond,
        "latest": latest,
        "status": status,
        "metrics": metrics,
        "sensor_cards": sensor_cards,
        "aerator_cards": aerator_cards,
        "thresholds": pond_defaults,
        "stability_score": latest_stability,
        "threshold_items": threshold_items,
        "thresholds_json_str": thresholds_json_str,
        "metric_definitions": METRIC_DEFINITIONS,
        "sensor_type_choices": PondSensor.SENSOR_TYPE_CHOICES,
        "can_manage": can_manage_pond(request.user, pond),
        "can_delete": can_delete_pond(request.user, pond),
        "now": timezone.now(),
    }
    return render(request, "water/pond_detail.html", context)


@login_required(login_url="login_portal")
def dashboard(request):
    """保留以兼容舊URL - 重定向到新的pond_list"""
    return redirect("water:pond_list")



@login_required(login_url="login_portal")
def add_pond(request):
    """新增魚池"""
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        species = (request.POST.get("species") or "").strip()
        description = (request.POST.get("description") or "").strip()
        map_note = (request.POST.get("map_note") or "").strip()

        # 驗證必填字段
        if not name:
            messages.error(request, "請輸入魚池名稱。")
            return redirect("water:add_pond")

        # 檢查名稱是否已存在
        if Pond.objects.filter(name=name).exists():
            messages.error(request, f"名稱 '{name}' 已存在，請使用其他名稱。")
            return redirect("water:add_pond")

        if not species:
            species = "文蛤"

        # 建立新魚池
        pond = Pond.objects.create(
            name=name,
            species=species,
            description=description,
            map_note=map_note,
            creator=request.user,
            map_image=request.FILES.get("map_image"),
        )

        # 添加當前使用者為擁有者
        pond.owners.add(request.user)

        messages.success(request, f"魚池 '{name}' 已建立，你已成為該池區的管理者。")
        return redirect("water:pond_detail", pond_id=pond.pk)

    # GET 請求：顯示新增表單
    return render(request, "water/add_pond.html")


@login_required(login_url="login_portal")
def manage_pond(request, pond_id):
    """管理魚池（編輯池區資訊）"""
    pond = get_object_or_404(Pond, pk=pond_id)

    # 權限檢查
    if not can_manage_pond(request.user, pond):
        messages.error(request, "你沒有權限編輯此池區。")
        return redirect("water:pond_list")

    if request.method == "POST":
        pond.name = (request.POST.get("name") or "").strip() or pond.name
        pond.species = (request.POST.get("species") or "").strip() or pond.species
        pond.description = (request.POST.get("description") or "").strip()
        pond.map_note = (request.POST.get("map_note") or "").strip()
        if can_delete_pond(request.user, pond):
            pond.discord_webhook_url = (request.POST.get("discord_webhook_url") or "").strip()

        # 處理地圖圖片上傳與刪除
        if request.POST.get("clear_map_image") == "1":
            if pond.map_image:
                pond.map_image.delete(save=False)
            pond.map_image = None
        else:
            map_image = request.FILES.get("map_image")
            if map_image:
                if pond.map_image:
                    pond.map_image.delete(save=False)
                pond.map_image = map_image


        # 驗證名稱唯一性（排除自己）
        if Pond.objects.filter(name=pond.name).exclude(pk=pond.pk).exists():
            messages.error(request, f"名稱 '{pond.name}' 已被其他池區使用。")
            return redirect("water:manage_pond", pond_id=pond.pk)

        # 穩定度公式權重設定
        try:
            pond.stability_w_do = int(request.POST.get("stability_w_do") or 40)
            pond.stability_w_ph = int(request.POST.get("stability_w_ph") or 30)
            pond.stability_w_temp = int(request.POST.get("stability_w_temp") or 30)
        except ValueError:
            pass

        pond.save()
        messages.success(request, f"池區 '{pond.name}' 已更新。")
        return redirect("water:pond_detail", pond_id=pond.pk)

    is_owner = can_delete_pond(request.user, pond)
    context = {
        "pond": pond,
        "is_owner": is_owner,
        "owners": pond.owners.all(),
        "viewers": pond.viewers.all(),
    }
    return render(request, "water/manage_pond.html", context)


@login_required(login_url="login_portal")
def delete_pond(request, pond_id):
    """刪除魚池"""
    pond = get_object_or_404(Pond, pk=pond_id)

    # 權限檢查 - 只有管理者和創立者可以刪除
    if not can_delete_pond(request.user, pond):
        messages.error(request, "你沒有權限刪除此池區。")
        return redirect("water:pond_list")

    if request.method == "POST":
        pond_name = pond.name
        pond.delete()
        messages.success(request, f"池區 '{pond_name}' 已刪除。")
        return redirect("water:pond_list")

    # GET 請求：顯示刪除確認頁面
    context = {
        "pond": pond,
        "sensor_count": pond.sensors.count(),
    }
    return render(request, "water/pond_delete_confirm.html", context)


def pond_history_api(request, pond_id):
    """取得特定池區的歷史水質數據 (JSON 格式)"""
    pond = get_object_or_404(Pond, pk=pond_id)
    if pond not in visible_ponds_for(request.user):
        return JsonResponse({"status": "error", "message": "無權限查看此池區。"}, status=403)

    # Determine target user for thresholds
    target_user = get_pond_owner_for_thresholds(pond) or request.user

    sensor_id = request.GET.get("sensor_id", "all")
    time_range = request.GET.get("time_range", "7d")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if time_range == "custom" and start_date_str and end_date_str:
        from django.utils.dateparse import parse_date
        parsed_start = parse_date(start_date_str)
        parsed_end = parse_date(end_date_str)
        if parsed_start and parsed_end:
            start_dt = timezone.make_aware(timezone.datetime.combine(parsed_start, timezone.datetime.min.time()))
            end_dt = timezone.make_aware(timezone.datetime.combine(parsed_end, timezone.datetime.max.time()))
            readings = SensorReading.objects.filter(pond=pond, measured_at__range=(start_dt, end_dt))
        else:
            readings = SensorReading.objects.filter(pond=pond)
    else:
        now = timezone.now()
        if time_range == "1h":
            start_date = now - timedelta(hours=1)
        elif time_range == "3h":
            start_date = now - timedelta(hours=3)
        elif time_range == "24h":
            start_date = now - timedelta(days=1)
        elif time_range == "30d":
            start_date = now - timedelta(days=30)
        else:  # 7d
            start_date = now - timedelta(days=7)
        readings = SensorReading.objects.filter(pond=pond, measured_at__gte=start_date)

    if sensor_id != "all":
        if str(sensor_id).startswith("aerator_"):
            aerator_id = str(sensor_id).split("_")[1]
            try:
                aerator = pond.aerators.get(pk=aerator_id)
            except Exception:
                return JsonResponse({"status": "error", "message": "找不到指定的水車。"}, status=400)

            log_qs = PondAeratorStateLog.objects.filter(pond=pond, aerator=aerator)
            if time_range == "custom" and start_date_str and end_date_str:
                from django.utils.dateparse import parse_date
                parsed_start = parse_date(start_date_str)
                parsed_end = parse_date(end_date_str)
                if parsed_start and parsed_end:
                    start_dt = timezone.make_aware(timezone.datetime.combine(parsed_start, timezone.datetime.min.time()))
                    end_dt = timezone.make_aware(timezone.datetime.combine(parsed_end, timezone.datetime.max.time()))
                    log_qs = log_qs.filter(recorded_at__range=(start_dt, end_dt))
            else:
                now = timezone.now()
                if time_range == "1h":
                    start_date = now - timedelta(hours=1)
                elif time_range == "3h":
                    start_date = now - timedelta(hours=3)
                elif time_range == "24h":
                    start_date = now - timedelta(days=1)
                elif time_range == "30d":
                    start_date = now - timedelta(days=30)
                else:
                    start_date = now - timedelta(days=7)
                log_qs = log_qs.filter(recorded_at__gte=start_date)

            if log_qs.exists():
                data = [
                    {
                        "measured_at": timezone.localtime(log.recorded_at).strftime("%Y-%m-%d %H:%M:%S"),
                        "sensor_name": aerator.name,
                        "aerator_state": 1 if log.is_operating else 0,
                        "temperature": None,
                        "ph": None,
                        "dissolved_oxygen": None,
                        "ammonia_nitrogen": None,
                        "nitrite": None,
                        "salinity": None,
                        "stability_index": None,
                    }
                    for log in log_qs.order_by("-recorded_at")
                ]
                return JsonResponse({"status": "success", "data": data})
            
            reading_qs = readings.select_related("sensor").order_by("measured_at")
            latest_values = {}
            data = []
            for r in reading_qs:
                if r.sensor_id:
                    latest_values[r.sensor_id] = {
                        "temperature": r.temperature,
                        "ph": r.ph,
                        "dissolved_oxygen": r.dissolved_oxygen,
                        "ammonia_nitrogen": r.ammonia_nitrogen,
                        "nitrite": r.nitrite,
                        "salinity": r.salinity,
                    }
                
                is_operating = True
                if not aerator.is_active:
                    is_operating = False
                elif aerator.rules:
                    for rule in aerator.rules:
                        s_id = rule.get("sensor_id")
                        metric = rule.get("metric")
                        op = rule.get("operator")
                        try:
                            t_val = float(rule.get("value", 0))
                        except (ValueError, TypeError):
                            continue
                        
                        sensor_vals = latest_values.get(s_id)
                        if not sensor_vals:
                            is_operating = False
                            break
                        
                        curr_val = sensor_vals.get(metric)
                        if curr_val is None:
                            is_operating = False
                            break
                            
                        try:
                            curr_val = float(curr_val)
                        except (ValueError, TypeError):
                            is_operating = False
                            break
                            
                        if op == "lt" and not (curr_val < t_val):
                            is_operating = False
                            break
                        elif op == "le" and not (curr_val <= t_val):
                            is_operating = False
                            break
                        elif op == "gt" and not (curr_val > t_val):
                            is_operating = False
                            break
                        elif op == "ge" and not (curr_val >= t_val):
                            is_operating = False
                            break
                        elif op == "eq" and not (curr_val == t_val):
                            is_operating = False
                            break
                        elif op not in ("lt", "le", "gt", "ge", "eq"):
                            is_operating = False
                            break
                
                data.append({
                    "measured_at": timezone.localtime(r.measured_at).strftime("%Y-%m-%d %H:%M:%S"),
                    "sensor_name": aerator.name,
                    "aerator_state": 1 if is_operating else 0,
                    "temperature": None,
                    "ph": None,
                    "dissolved_oxygen": None,
                    "ammonia_nitrogen": None,
                    "nitrite": None,
                    "salinity": None,
                    "stability_index": None,
                })
            
            data.reverse()
            return JsonResponse({"status": "success", "data": data})
        else:
            readings = readings.filter(sensor_id=sensor_id)

    readings = readings.select_related("sensor").order_by("-measured_at")
    pond_defaults = threshold_map_for(target_user, pond, sensor=None)

    data = []
    for r in readings:
        sensor_thresholds = pond_defaults
        if r.sensor:
            has_custom = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=r.sensor).exists()
            sensor_thresholds = threshold_map_for(target_user, pond, sensor=r.sensor if has_custom else None)
        stability = calculate_stability(r, sensor_thresholds, pond.stability_w_do, pond.stability_w_ph, pond.stability_w_temp)

        data.append({
            "measured_at": timezone.localtime(r.measured_at).strftime("%Y-%m-%d %H:%M:%S"),
            "sensor_name": r.sensor.name if r.sensor else "未分類感測器",
            "temperature": r.temperature,
            "ph": r.ph,
            "dissolved_oxygen": r.dissolved_oxygen,
            "ammonia_nitrogen": r.ammonia_nitrogen,
            "nitrite": r.nitrite,
            "salinity": r.salinity,
            "stability_index": stability,
        })

    return JsonResponse({"status": "success", "data": data})


@login_required(login_url="login_portal")
def export_pond_csv(request, pond_id):
    """匯出池區歷史水質資料為相容 Excel 的 CSV (UTF-8 BOM)"""
    pond = get_object_or_404(Pond, pk=pond_id)
    if pond not in visible_ponds_for(request.user):
        return HttpResponse("無權限查看此池區。", status=403)

    # Determine target user for thresholds
    target_user = get_pond_owner_for_thresholds(pond) or request.user

    sensor_id = request.GET.get("sensor_id", "all")
    time_range = request.GET.get("time_range", "7d")
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if time_range == "custom" and start_date_str and end_date_str:
        from django.utils.dateparse import parse_date
        parsed_start = parse_date(start_date_str)
        parsed_end = parse_date(end_date_str)
        if parsed_start and parsed_end:
            start_dt = timezone.make_aware(timezone.datetime.combine(parsed_start, timezone.datetime.min.time()))
            end_dt = timezone.make_aware(timezone.datetime.combine(parsed_end, timezone.datetime.max.time()))
            readings = SensorReading.objects.filter(pond=pond, measured_at__range=(start_dt, end_dt))
        else:
            readings = SensorReading.objects.filter(pond=pond)
    else:
        now = timezone.now()
        if time_range == "1h":
            start_date = now - timedelta(hours=1)
        elif time_range == "3h":
            start_date = now - timedelta(hours=3)
        elif time_range == "24h":
            start_date = now - timedelta(days=1)
        elif time_range == "30d":
            start_date = now - timedelta(days=30)
        else:  # 7d
            start_date = now - timedelta(days=7)
        readings = SensorReading.objects.filter(pond=pond, measured_at__gte=start_date)

    if sensor_id != "all":
        readings = readings.filter(sensor_id=sensor_id)

    readings = readings.select_related("sensor").order_by("-measured_at")
    pond_defaults = threshold_map_for(target_user, pond, sensor=None)

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="pond_{pond.pk}_history.csv"'

    response.write(b'\xef\xbb\xbf')

    writer = csv.writer(response)
    writer.writerow(["檢測時間", "感測器名稱", "水溫 (°C)", "pH 值", "溶氧量 (mg/L)", "氨氮 (mg/L)", "亞硝酸鹽 (mg/L)", "鹽度 (ppt)", "穩定度 (%)"])
    for r in readings:
        sensor_thresholds = pond_defaults
        if r.sensor:
            has_custom = WaterThreshold.objects.filter(user=target_user, pond=pond, sensor=r.sensor).exists()
            sensor_thresholds = threshold_map_for(target_user, pond, sensor=r.sensor if has_custom else None)
        stability = calculate_stability(r, sensor_thresholds, pond.stability_w_do, pond.stability_w_ph, pond.stability_w_temp)
        writer.writerow([
            timezone.localtime(r.measured_at).strftime("%Y-%m-%d %H:%M:%S"),
            r.sensor.name if r.sensor else "未分類感測器",
            r.temperature,
            r.ph,
            r.dissolved_oxygen,
            r.ammonia_nitrogen if r.ammonia_nitrogen is not None else "",
            r.nitrite if r.nitrite is not None else "",
            r.salinity if r.salinity is not None else "",
            stability if stability is not None else "",
        ])

    return response


@login_required(login_url="login_portal")
def generate_mock_readings(request, pond_id):
    """為池區產生最近 24 小時的隨機水質讀值以供測試"""
    pond = get_object_or_404(Pond, pk=pond_id)
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({"status": "error", "message": "無操作權限，僅系統管理員可以產生測試數據。"}, status=403)

    sensors = pond.sensors.filter(is_active=True)
    if not sensors.exists():
        return JsonResponse({"status": "error", "message": "此池區尚無啟用的感測器，請先在地圖上新增。"}, status=400)

    rng = random.Random()
    now = timezone.now()
    created_count = 0

    # 產生 6 個時間點的測試資料 (每 4 小時一筆)
    for i in range(6):
        measured_at = now - timedelta(hours=i * 4 + rng.uniform(0, 2))
        for sensor in sensors:
            SensorReading.objects.create(
                pond=pond,
                sensor=sensor,
                measured_at=measured_at,
                temperature=round(rng.uniform(21.0, 29.5), 1),
                ph=round(rng.uniform(7.5, 8.5), 2),
                dissolved_oxygen=round(rng.uniform(4.0, 7.8), 1),
                ammonia_nitrogen=round(rng.uniform(0.01, 0.19), 3),
                nitrite=round(rng.uniform(0.01, 0.14), 3),
                salinity=round(rng.uniform(20.0, 32.0), 1),
            )
            created_count += 1

    return JsonResponse({
        "status": "success",
        "message": f"成功為 {sensors.count()} 個感測器產生了 {created_count} 筆測試讀值。"
    })


@csrf_exempt
def upload_sensor_reading(request):
    """硬體感測器上傳水質讀值的 REST API Endpoint (免 CSRF)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "僅接受 POST 請求。"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "JSON 格式錯誤。"}, status=400)

    secret_token = body.get("secret_token")
    if not secret_token:
        return JsonResponse({"status": "error", "message": "缺少 secret_token 安全金鑰。"}, status=400)

    sensor = PondSensor.objects.filter(secret_token=secret_token).first()
    if not sensor:
        return JsonResponse({"status": "error", "message": "安全驗證失敗，無此感測器上傳金鑰。"}, status=403)

    if not sensor.is_active:
        return JsonResponse({"status": "error", "message": "該感測器已被停用，不接受讀值。"}, status=400)

    try:
        temperature = float(body.get("temperature"))
        ph = float(body.get("ph"))
        dissolved_oxygen = float(body.get("dissolved_oxygen"))

        ammonia_nitrogen = body.get("ammonia_nitrogen")
        if ammonia_nitrogen is not None:
            ammonia_nitrogen = float(ammonia_nitrogen)

        nitrite = body.get("nitrite")
        if nitrite is not None:
            nitrite = float(nitrite)

        salinity = body.get("salinity")
        if salinity is not None:
            salinity = float(salinity)

    except (ValueError, TypeError):
        return JsonResponse({"status": "error", "message": "temperature、ph 與 dissolved_oxygen 為必填且必須為數值。"}, status=400)

    reading = SensorReading.objects.create(
        pond=sensor.pond,
        sensor=sensor,
        measured_at=timezone.now(),
        temperature=temperature,
        ph=ph,
        dissolved_oxygen=dissolved_oxygen,
        ammonia_nitrogen=ammonia_nitrogen,
        nitrite=nitrite,
        salinity=salinity,
    )

    return JsonResponse({
        "status": "success",
        "message": "水質數據已成功記錄。",
        "reading_id": reading.pk
    })


@login_required(login_url="login_portal")
def share_pond(request, pond_id):
    """將魚池共享給其他使用者 (Gmail)"""
    pond = get_object_or_404(Pond, pk=pond_id)
    
    # 只有管理者/創立者才可以分享
    if not can_delete_pond(request.user, pond):
        messages.error(request, "你沒有權限管理此池區的共享設定。")
        return redirect("water:pond_detail", pond_id=pond.pk)
        
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        role = request.POST.get("role") or "viewer" # viewer or editor
        
        if not email:
            messages.error(request, "請輸入對方的 Email。")
            return redirect("water:manage_pond", pond_id=pond.pk)
            
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # 查找使用者：優先比對 email，其次比對 username
        target_user = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
        if not target_user:
            messages.error(request, f"找不到註冊為 '{email}' 的系統使用者。請確認對方已使用該 Google 帳號登入過本系統。")
            return redirect("water:manage_pond", pond_id=pond.pk)
            
        if role == "editor":
            # 加到 owners，並從 viewers 移除
            pond.owners.add(target_user)
            pond.viewers.remove(target_user)
            messages.success(request, f"已成功將 {target_user.email or target_user.username} 設為【編輯者】。")
        else: # viewer
            # 加到 viewers，並從 owners 移除
            pond.viewers.add(target_user)
            pond.owners.remove(target_user)
            messages.success(request, f"已成功將 {target_user.email or target_user.username} 設為【檢視者】。")
            
    return redirect("water:manage_pond", pond_id=pond.pk)


@login_required(login_url="login_portal")
def unshare_pond(request, pond_id):
    """移除與特定使用者的共享關係"""
    pond = get_object_or_404(Pond, pk=pond_id)
    
    # 只有管理者/創立者才可以移除共享
    if not can_delete_pond(request.user, pond):
        messages.error(request, "你沒有權限管理此池區的共享設定。")
        return redirect("water:pond_detail", pond_id=pond.pk)
        
    if request.method == "POST":
        target_user_id = request.POST.get("user_id")
        if not target_user_id:
            messages.error(request, "未指定要移除的使用者。")
            return redirect("water:manage_pond", pond_id=pond.pk)
            
        from django.contrib.auth import get_user_model
        User = get_user_model()
        target_user = get_object_or_404(User, pk=target_user_id)
        
        # 防呆：如果移除的是自己，且自己是唯一管理者，則不允許移除
        if target_user == request.user and pond.owners.count() <= 1:
            messages.error(request, "你是此池區唯一的管理者，無法移除自己。請先指定其他管理者。")
            return redirect("water:manage_pond", pond_id=pond.pk)
            
        # 從 owners 與 viewers 中同時移除
        pond.owners.remove(target_user)
        pond.viewers.remove(target_user)
        
        messages.success(request, f"已成功移除與 {target_user.email or target_user.username} 的共享。")
        
    return redirect("water:manage_pond", pond_id=pond.pk)


@ensure_csrf_cookie
def ar_feed(request):
    """
    AR 在地養殖餵食體驗頁面
    目前先使用模擬水質資料。
    之後可改成讀取你現有水質監測系統的最新資料。
    """
    import os
    from django.conf import settings

    static_dir = os.path.join(settings.BASE_DIR, "static", "water", "assets")
    glb_exists = {
        "milkfish": os.path.exists(os.path.join(static_dir, "milkfish.glb")),
        "shrimp": os.path.exists(os.path.join(static_dir, "shrimp.glb")),
        "clam": os.path.exists(os.path.join(static_dir, "clam.glb")),
        "crab": os.path.exists(os.path.join(static_dir, "crab.glb")),
        "fish": False,  # 先拿掉 fish.glb 模型，退回球體
    }

    initial_water = {
        "temperature": 27.2,
        "ph": 7.4,
        "oxygen": 6.5,
        "turbidity": 20,
        "source": "simulation",
        "updated_at": timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return render(request, "water/ar_feed.html", {
        "initial_water": initial_water,
        "glb_exists": glb_exists,
        "ar_player_name": user_display_name(request.user, fallback="匿名者"),
    })


@require_POST
def ar_feed_save_score(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    try:
        score = int(payload.get("score", 0))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "invalid_score"}, status=400)

    score = max(0, min(100, score))
    played_on = timezone.localdate()

    if request.user.is_authenticated:
        user = request.user
        player_key = f"user:{user.pk}"
        player_name = user_display_name(user, fallback="玩家")
    else:
        if not request.session.session_key:
            request.session.create()
        user = None
        player_key = f"session:{request.session.session_key}"
        player_name = str(payload.get("player_name") or "訪客")[:80]

    try:
        growth = float(payload.get("growth") or 0)
    except (TypeError, ValueError):
        growth = 0

    defaults = {
        "user": user,
        "player_name": player_name[:80],
        "score": score,
        "scene": str(payload.get("scene") or "clam_polyculture")[:40],
        "badge": str(payload.get("badge") or "")[:120],
        "result_text": str(payload.get("text") or ""),
        "growth": growth,
        "water": payload.get("water") if isinstance(payload.get("water"), dict) else {},
    }

    entry, created = ArFeedLeaderboardEntry.objects.get_or_create(
        played_on=played_on,
        player_key=player_key,
        defaults=defaults,
    )

    saved_best = created or score > entry.score
    should_update_name = entry.player_name != defaults["player_name"]
    if saved_best:
        for field, value in defaults.items():
            setattr(entry, field, value)
        entry.save()
    elif should_update_name:
        entry.player_name = defaults["player_name"]
        entry.user = user
        entry.save(update_fields=["player_name", "user", "updated_at"])

    return JsonResponse({
        "ok": True,
        "saved_best": saved_best,
        "score": entry.score,
        "played_on": played_on.isoformat(),
    })


@require_GET
def ar_feed_leaderboard(request):
    played_on = timezone.localdate()
    entries = list(
        ArFeedLeaderboardEntry.objects
        .filter(played_on=played_on)
        .order_by("-score", "updated_at")[:10]
    )

    data = [
        {
            "name": entry.player_name,
            "score": entry.score,
            "date": entry.played_on.isoformat(),
            "is_current_user": bool(request.user.is_authenticated and entry.user_id == request.user.id),
        }
        for entry in entries
    ]

    bot_entries = [
        {"name": "睏寶(bot)", "score": 75, "date": played_on.isoformat(), "is_current_user": False, "is_bot": True},
        {"name": "藍寶(bot)", "score": 65, "date": played_on.isoformat(), "is_current_user": False, "is_bot": True},
        {"name": "痞子妹(bot)", "score": 55, "date": played_on.isoformat(), "is_current_user": False, "is_bot": True},
        {"name": "囡囡(bot)", "score": 45, "date": played_on.isoformat(), "is_current_user": False, "is_bot": True},
    ]
    data = sorted(data + bot_entries, key=lambda item: item["score"], reverse=True)[:10]

    return JsonResponse({
        "ok": True,
        "date": played_on.isoformat(),
        "leaderboard": data,
    })


def latest_water_api(request):
    """
    簡易水質 API。
    目前回傳模擬值，方便前端測試。
    你之後可以把這裡改成讀資料庫最新監測資料。
    """
    data = {
        "temperature": round(random.uniform(26.5, 28.5), 1),
        "ph": round(random.uniform(7.1, 7.8), 1),
        "oxygen": round(random.uniform(5.8, 6.8), 1),
        "turbidity": random.randint(18, 28),
        "source": "simulation_api",
        "updated_at": timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return JsonResponse(data)


