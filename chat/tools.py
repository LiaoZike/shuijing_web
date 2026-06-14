from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from core.models import Activity, AiotProject, Notice, RelatedLink, UsrAchievement
from water.models import Pond


def _trim(value: str | None, limit: int = 180) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


def _aerator_rule_summary(aerator) -> list[dict]:
    operator_labels = {
        "lt": "<",
        "le": "<=",
        "gt": ">",
        "ge": ">=",
        "eq": "=",
    }
    return [
        {
            "sensor_name": rule.get("sensor_name"),
            "metric": rule.get("metric"),
            "metric_label": rule.get("metric_label"),
            "operator": rule.get("operator"),
            "operator_label": operator_labels.get(rule.get("operator"), rule.get("operator")),
            "value": rule.get("value"),
        }
        for rule in aerator.get_enriched_rules()
    ]


def _pond_aerator_summary(pond) -> list[dict]:
    aerators = []
    for aerator in pond.aerators.all().order_by("name"):
        is_operating = aerator.is_operating()
        aerators.append(
            {
                "aerator_id": aerator.pk,
                "aerator_name": aerator.name,
                "is_enabled": aerator.is_active,
                "is_operating": is_operating,
                "status_label": "運作中" if is_operating else "已停止",
                "rule_mode": "all_rules_match" if aerator.rules else "always_on_when_enabled",
                "rules": _aerator_rule_summary(aerator),
            }
        )
    return aerators


def _pond_sensor_summary(pond, user=None) -> list[dict]:
    from water.views import threshold_map_for
    from water.utils import check_metrics_status
    sensors = []
    for sensor in pond.sensors.filter(is_active=True).order_by("name"):
        latest = sensor.readings.first()
        if latest:
            sensor_thresholds = threshold_map_for(user, pond, sensor=sensor)
            metric_status = check_metrics_status(latest, sensor_thresholds)
        else:
            metric_status = {}
            
        sensors.append(
            {
                "sensor_id": sensor.pk,
                "sensor_name": sensor.name,
                "sensor_type": sensor.get_sensor_type_display(),
                "measured_at": latest.measured_at.isoformat() if latest else "",
                "temperature_c": latest.temperature if latest else None,
                "ph": latest.ph if latest else None,
                "dissolved_oxygen_mg_l": latest.dissolved_oxygen if latest else None,
                "ammonia_nitrogen_mg_l": latest.ammonia_nitrogen if latest else None,
                "nitrite_mg_l": latest.nitrite if latest else None,
                "salinity_ppt": latest.salinity if latest else None,
                "metric_status": metric_status,
            }
        )
    return sensors


def list_upcoming_activities(limit: int = 5) -> dict:
    today = timezone.localdate()
    limit = max(1, min(int(limit or 5), 10))
    activities = (
        Activity.objects.filter(is_active=True)
        .filter(Q(end_date__gte=today) | Q(end_date__isnull=True, date__gte=today))
        .order_by("date")[:limit]
    )
    return {
        "today": today.isoformat(),
        "activities": [
            {
                "id": activity.id,
                "title": activity.title,
                "subtitle": activity.title_2,
                "date": activity.date.isoformat() if activity.date else "",
                "end_date": activity.end_date.isoformat() if activity.end_date else "",
                "time": activity.time,
                "location": activity.location,
                "tags": activity.tag_list(),
                "description": _trim(activity.description),
                "registration_open": activity.is_registration_open(),
                "remaining_spots": activity.remaining_spots(),
                "link": f"/events/{activity.id}/",
            }
            for activity in activities
        ],
    }


def search_site_content(keyword: str, limit: int = 5) -> dict:
    keyword = (keyword or "").strip()
    limit = max(1, min(int(limit or 5), 10))
    if not keyword:
        return {"error": "keyword is required"}

    activities = Activity.objects.filter(is_active=True).filter(
        Q(title__icontains=keyword)
        | Q(title_2__icontains=keyword)
        | Q(description__icontains=keyword)
        | Q(location__icontains=keyword)
        | Q(tags__icontains=keyword)
    )[:limit]
    notices = Notice.objects.filter(is_active=True).filter(
        Q(title__icontains=keyword) | Q(content__icontains=keyword)
    )[:limit]
    aiot_projects = AiotProject.objects.filter(is_active=True).filter(
        Q(title__icontains=keyword)
        | Q(description__icontains=keyword)
        | Q(tags__icontains=keyword)
    )[:limit]
    achievements = UsrAchievement.objects.filter(is_active=True).filter(
        Q(title__icontains=keyword)
        | Q(description__icontains=keyword)
        | Q(category__icontains=keyword)
    )[:limit]
    links = RelatedLink.objects.filter(is_active=True).filter(
        Q(title__icontains=keyword)
        | Q(description__icontains=keyword)
        | Q(category__icontains=keyword)
    )[:limit]

    return {
        "keyword": keyword,
        "activities": [
            {
                "title": item.title,
                "date": item.date.isoformat() if item.date else "",
                "location": item.location,
                "description": _trim(item.description),
                "link": f"/events/{item.id}/",
            }
            for item in activities
        ],
        "notices": [
            {
                "title": item.title,
                "publish_date": item.publish_date.isoformat() if item.publish_date else "",
                "content": _trim(item.content),
                "link": f"/notices/{item.id}/",
            }
            for item in notices
        ],
        "aiot_projects": [
            {
                "title": item.title,
                "tags": item.tag_list(),
                "description": _trim(item.description),
                "link": item.link_url or "/usr/#aiot-section",
            }
            for item in aiot_projects
        ],
        "achievements": [
            {
                "title": item.title,
                "date": item.date.isoformat() if item.date else "",
                "category": item.category,
                "description": _trim(item.description),
                "link": item.link_url or "/usr/#achievement-section",
            }
            for item in achievements
        ],
        "related_links": [
            {
                "title": item.title,
                "description": _trim(item.description),
                "link": item.link_url,
            }
            for item in links
        ],
    }


def get_latest_notices(limit: int = 5) -> dict:
    limit = max(1, min(int(limit or 5), 10))
    notices = Notice.objects.filter(is_active=True).order_by(
        "-is_priority", "-publish_date", "-created_at"
    )[:limit]
    return {
        "notices": [
            {
                "id": notice.id,
                "title": notice.title,
                "category": notice.category,
                "publish_date": notice.publish_date.isoformat()
                if notice.publish_date
                else "",
                "content": _trim(notice.content),
                "link": f"/notices/{notice.id}/",
            }
            for notice in notices
        ]
    }


def list_usr_highlights(limit: int = 5) -> dict:
    limit = max(1, min(int(limit or 5), 10))
    projects = AiotProject.objects.filter(is_active=True).order_by("order")[:limit]
    achievements = UsrAchievement.objects.filter(is_active=True).order_by("-date")[:limit]
    return {
        "aiot_projects": [
            {
                "title": project.title,
                "tags": project.tag_list(),
                "description": _trim(project.description),
                "link": project.link_url or "/usr/#aiot-section",
            }
            for project in projects
        ],
        "achievements": [
            {
                "title": achievement.title,
                "date": achievement.date.isoformat() if achievement.date else "",
                "category": achievement.category,
                "description": _trim(achievement.description),
                "link": achievement.link_url or "/usr/#achievement-section",
            }
            for achievement in achievements
        ],
    }


def get_latest_water_quality(pond_name: str, user=None) -> dict:
    from water.views import visible_ponds_for
    visible_ponds = visible_ponds_for(user)
    try:
        pond = visible_ponds.get(name=pond_name)
    except Pond.DoesNotExist:
        return {
            "error": f"unknown pond or permission denied: {pond_name}",
            "available_ponds": list(visible_ponds.values_list("name", flat=True)),
        }

    latest = pond.readings.first()
    if not latest:
        return {"error": f"no sensor readings for {pond_name}"}

    return {
        "pond": pond.name,
        "species": pond.species,
        "measured_at": latest.measured_at.isoformat(),
        "temperature_c": latest.temperature,
        "ph": latest.ph,
        "dissolved_oxygen_mg_l": latest.dissolved_oxygen,
        "salinity_ppt": latest.salinity,
        "sensors": _pond_sensor_summary(pond, user=user),
        "aerators": _pond_aerator_summary(pond),
    }


def get_aerator_status(pond_name: str | None = None, user=None) -> dict:
    from water.views import visible_ponds_for

    visible_ponds = visible_ponds_for(user).prefetch_related("aerators", "sensors")
    if pond_name:
        try:
            visible_ponds = visible_ponds.filter(name=pond_name)
            if not visible_ponds.exists():
                raise Pond.DoesNotExist
        except Pond.DoesNotExist:
            all_ponds = visible_ponds_for(user)
            return {
                "error": f"unknown pond or permission denied: {pond_name}",
                "available_ponds": list(all_ponds.values_list("name", flat=True)),
            }

    ponds = []
    for pond in visible_ponds.order_by("name"):
        aerators = _pond_aerator_summary(pond)
        ponds.append(
            {
                "pond": pond.name,
                "aerator_count": len(aerators),
                "operating_count": sum(1 for item in aerators if item["is_operating"]),
                "aerators": aerators,
            }
        )

    return {
        "pond_count": len(ponds),
        "ponds": ponds,
    }


def get_average_do(pond_name: str, days: int = 7, user=None) -> dict:
    from datetime import timedelta
    from django.db.models import Avg
    from water.views import visible_ponds_for

    visible_ponds = visible_ponds_for(user)
    try:
        pond = visible_ponds.get(name=pond_name)
    except Pond.DoesNotExist:
        return {
            "error": f"unknown pond or permission denied: {pond_name}",
            "available_ponds": list(visible_ponds.values_list("name", flat=True)),
        }

    days = max(1, min(int(days or 7), 30))
    since = timezone.now() - timedelta(days=days)
    average = pond.readings.filter(measured_at__gte=since).aggregate(
        avg_do=Avg("dissolved_oxygen")
    )
    return {
        "pond": pond.name,
        "days": days,
        "average_dissolved_oxygen_mg_l": round(average["avg_do"] or 0, 2),
    }


def get_pond_history(pond_name: str, days: int = 7, user=None) -> dict:
    from datetime import timedelta
    from django.db.models.functions import TruncDate
    from django.db.models import Avg
    from water.views import visible_ponds_for

    visible_ponds = visible_ponds_for(user)
    try:
        pond = visible_ponds.get(name=pond_name)
    except Pond.DoesNotExist:
        return {
            "error": f"unknown pond or permission denied: {pond_name}",
            "available_ponds": list(visible_ponds.values_list("name", flat=True)),
        }

    days = max(1, min(int(days or 7), 30))
    since = timezone.now() - timedelta(days=days)

    readings = (
        pond.readings.filter(measured_at__gte=since)
        .annotate(date=TruncDate("measured_at"))
        .values("date")
        .annotate(
            avg_temp=Avg("temperature"),
            avg_ph=Avg("ph"),
            avg_do=Avg("dissolved_oxygen"),
            avg_sal=Avg("salinity"),
        )
        .order_by("date")
    )

    history_list = []
    for r in readings:
        d = r["date"]
        date_str = d.strftime("%m/%d") if d else ""
        history_list.append({
            "date": date_str,
            "avg_temperature_c": round(r["avg_temp"] or 0, 1),
            "avg_ph": round(r["avg_ph"] or 0, 2),
            "avg_dissolved_oxygen_mg_l": round(r["avg_do"] or 0, 1),
            "avg_salinity_ppt": round(r["avg_sal"] or 0, 1),
        })

    return {
        "pond": pond.name,
        "days": days,
        "history": history_list,
    }


def get_pond_summary(days: int = 7, user=None) -> dict:
    from datetime import timedelta
    from django.db.models import Avg, Count, Max, Min
    from water.views import visible_ponds_for, threshold_map_for
    from water.utils import reading_status

    days = max(1, min(int(days or 7), 30))
    since = timezone.now() - timedelta(days=days)
    ponds = visible_ponds_for(user).order_by("name")
    summaries = []

    for pond in ponds:
        latest = pond.readings.first()
        recent = pond.readings.filter(measured_at__gte=since)
        stats = recent.aggregate(
            reading_count=Count("id"),
            avg_temperature=Avg("temperature"),
            avg_ph=Avg("ph"),
            avg_do=Avg("dissolved_oxygen"),
            min_do=Min("dissolved_oxygen"),
            max_do=Max("dissolved_oxygen"),
            avg_salinity=Avg("salinity"),
        )
        avg_do = stats["avg_do"]
        latest_do = latest.dissolved_oxygen if latest else None
        min_do = stats["min_do"]
        status = "no_recent_data"
        if avg_do is not None:
            # 取得使用者自訂警戒值，預設為 5.0
            threshold_map = threshold_map_for(user, pond)
            do_limits = threshold_map.get("dissolved_oxygen", {})
            do_warn = do_limits.get("min")
            if do_warn is None:
                do_warn = 5.0
            do_danger = max(1.0, do_warn - 1.0)

            # 檢查池中所有啟用中感測器的最新測值，以決定最嚴重的狀態
            has_data = False
            worst_tone = "good"  # "good" < "warning" < "danger"
            
            for sensor in pond.sensors.filter(is_active=True):
                sensor_latest = sensor.readings.first()
                if not sensor_latest:
                    continue
                has_data = True
                sensor_thresholds = threshold_map_for(user, pond, sensor=sensor)
                res = reading_status(sensor_latest, sensor_thresholds)
                
                # Check for low oxygen danger
                if sensor_latest.dissolved_oxygen is not None and sensor_latest.dissolved_oxygen < do_danger:
                    worst_tone = "danger"
                elif res["tone"] == "warning" and worst_tone != "danger":
                    worst_tone = "warning"
            
            if has_data:
                if worst_tone == "danger":
                    status = "low_oxygen"
                elif worst_tone == "warning":
                    status = "watch"
                else:
                    status = "normal"

        summaries.append(
            {
                "pond": pond.name,
                "species": pond.species,
                "description": pond.description,
                "latest_measured_at": latest.measured_at.isoformat() if latest else "",
                "latest_temperature_c": latest.temperature if latest else None,
                "latest_ph": latest.ph if latest else None,
                "latest_dissolved_oxygen_mg_l": latest.dissolved_oxygen if latest else None,
                "latest_salinity_ppt": latest.salinity if latest else None,
                "sensors": _pond_sensor_summary(pond, user=user),
                "recent_days": days,
                "recent_reading_count": stats["reading_count"],
                "avg_temperature_c": round(stats["avg_temperature"], 2)
                if stats["avg_temperature"] is not None
                else None,
                "avg_ph": round(stats["avg_ph"], 2) if stats["avg_ph"] is not None else None,
                "avg_dissolved_oxygen_mg_l": round(avg_do, 2)
                if avg_do is not None
                else None,
                "min_dissolved_oxygen_mg_l": stats["min_do"],
                "max_dissolved_oxygen_mg_l": stats["max_do"],
                "avg_salinity_ppt": round(stats["avg_salinity"], 2)
                if stats["avg_salinity"] is not None
                else None,
                "status": status,
                "aerators": _pond_aerator_summary(pond),
            }
        )

    return {"days": days, "pond_count": len(summaries), "ponds": summaries}


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_upcoming_activities",
            "description": "查詢水井村網站目前即將到來的活動。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "最多回傳幾筆，預設 5，最多 10。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_site_content",
            "description": "用關鍵字搜尋活動、公告、AIoT 專案、USR 成果與相關連結。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜尋關鍵字。"},
                    "limit": {
                        "type": "integer",
                        "description": "每個分類最多回傳幾筆，預設 5，最多 10。",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_notices",
            "description": "查詢最新公告。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "最多回傳幾筆，預設 5，最多 10。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_usr_highlights",
            "description": "查詢 USR AIoT 專案與成果亮點。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "最多回傳幾筆，預設 5，最多 10。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_water_quality",
            "description": "Get the latest water quality reading for a pond, including temperature, pH, dissolved oxygen, and salinity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pond_name": {
                        "type": "string",
                        "description": "Pond name, for example: 1 號池, 2 號池, 3 號池.",
                    }
                },
                "required": ["pond_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_average_do",
            "description": "Calculate the average dissolved oxygen for a pond over the recent N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pond_name": {
                        "type": "string",
                        "description": "Pond name, for example: 1 號池.",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of recent days to average. Defaults to 7 and is capped at 30.",
                    },
                },
                "required": ["pond_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_aerator_status",
            "description": "查詢可見魚池內所有水車/增氧設備目前是運作中或已停止，並列出自動啟動條件與依據的感測器規則。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pond_name": {
                        "type": "string",
                        "description": "可選。指定魚池名稱；不填則查詢所有可見魚池。",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pond_summary",
            "description": "Summarize all ponds with latest readings and recent averages, including dissolved oxygen status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of recent days to summarize. Defaults to 7 and is capped at 30.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pond_history",
            "description": "獲取指定魚池近期的歷史水質資料趨勢（包含每日平均溫度、pH、溶氧、鹽度），供繪製歷史趨勢折線圖/圖表使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pond_name": {
                        "type": "string",
                        "description": "魚池名稱，例如：文蛤一號池, 2 號池.",
                    },
                    "days": {
                        "type": "integer",
                        "description": "查詢的天數，預設為 7，最多 30 天。",
                    },
                },
                "required": ["pond_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_site_navigation",
            "description": "根據使用者要求的目標頁面，解析為對應的網站網址路由。",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "使用者想前往的目的地描述（例如：水質監控、AR遊戲、公告、首頁、近期活動等）。",
                    }
                },
                "required": ["destination"],
            },
        },
    },
]


def resolve_site_navigation(destination: str) -> dict:
    dest = (destination or "").strip().lower()
    
    # 阻擋敏感或無權限後台路徑
    if any(k in dest for k in ["admin", "後台", "cron", "manage", "delete", "edit"]):
        return {
            "allowed": False,
            "reason": "安全性限制：無法導覽至系統管理或敏感操作頁面。"
        }
        
    if "監控" in dest or "監測" in dest or "儀表板" in dest or "dashboard" in dest:
        return {
            "allowed": True,
            "url": "/water/dashboard/",
            "title": "個人魚池監控",
            "message": "好的，水井龜這就帶您前往水質監控儀表板。"
        }
    elif "ar" in dest or "遊戲" in dest or "混養" in dest or "模擬" in dest:
        return {
            "allowed": True,
            "url": "/water/ar-feed/",
            "title": "AR 混養模擬遊戲",
            "message": "好的，正在為您載入 AR 混養模擬遊戲。"
        }
    elif "ai" in dest or "諮詢" in dest or "聊天" in dest or "問答" in dest or "導覽" in dest:
        return {
            "allowed": True,
            "url": "/chat/",
            "title": "AI 養殖諮詢",
            "message": "好的，正在為您切換至 AI 養殖諮詢主頁面。"
        }
    elif "公告" in dest or "最新公告" in dest or "notice" in dest:
        return {
            "allowed": True,
            "url": "/notices/",
            "title": "網站最新公告",
            "message": "好的，水井龜帶您去查看網站最新公告。"
        }
    elif "活動" in dest or "近期活動" in dest or "event" in dest:
        return {
            "allowed": True,
            "url": "/events/",
            "title": "近期活動列表",
            "message": "好的，正在為您打開近期活動列表。"
        }
    elif "故事" in dest or "地方故事" in dest or "story" in dest:
        return {
            "allowed": True,
            "url": "/story/",
            "title": "地方故事",
            "message": "好的，正在帶您前往探索地方故事頁面。"
        }
    elif "usr" in dest or "成果" in dest or "aiot" in dest or "專案" in dest:
        return {
            "allowed": True,
            "url": "/usr/",
            "title": "USR 實踐與成果",
            "message": "好的，正在帶您前往 USR 實踐與成果頁面。"
        }
    elif "連結" in dest or "相關連結" in dest or "link" in dest:
        return {
            "allowed": True,
            "url": "/links/",
            "title": "相關連結",
            "message": "好的，為您打開相關連結頁面。"
        }
    elif "關於" in dest or "about" in dest:
        return {
            "allowed": True,
            "url": "/about/",
            "title": "關於我們",
            "message": "好的，為您導向關於我們網頁。"
        }
    elif "聯絡" in dest or "contact" in dest:
        return {
            "allowed": True,
            "url": "/contact/",
            "title": "聯絡我們",
            "message": "好的，正在為您導向聯絡我們頁面。"
        }
    elif "首頁" in dest or "home" in dest or "主頁" in dest:
        return {
            "allowed": True,
            "url": "/",
            "title": "首頁",
            "message": "好的，正在為您回到水井村網站首頁。"
        }
        
    return {
        "allowed": False,
        "reason": "未找到符合的公開頁面路由描述。請試試『首頁』、『水質監控』、『AR遊戲』、『網站公告』、『近期活動』或『USR專案』。"
    }


_TOOL_REGISTRY = {
    "list_upcoming_activities": list_upcoming_activities,
    "search_site_content": search_site_content,
    "get_latest_notices": get_latest_notices,
    "list_usr_highlights": list_usr_highlights,
    "get_latest_water_quality": get_latest_water_quality,
    "get_average_do": get_average_do,
    "get_aerator_status": get_aerator_status,
    "get_pond_summary": get_pond_summary,
    "get_pond_history": get_pond_history,
    "resolve_site_navigation": resolve_site_navigation,
}


def dispatch(name: str, arguments: dict, user=None) -> dict:
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        if name in ("get_latest_water_quality", "get_average_do", "get_aerator_status", "get_pond_summary", "get_pond_history"):
            return fn(**arguments, user=user)
        return fn(**arguments)
    except TypeError as exc:
        return {"error": f"tool arguments error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"tool execution error: {type(exc).__name__}: {exc}"}
