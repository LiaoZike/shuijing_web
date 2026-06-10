#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Evaluate water sensor readings for anomalies and send alerts to Discord.
Can be executed as a standalone script or imported directly.

Usage:
    python scratch/discord_notify.py [--config-id 1] [--force]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import timedelta
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("discord_notify")


def setup_django() -> None:
    """Initialize Django environment for standalone script execution."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shuijing.settings")

    import django
    django.setup()


def check_and_trigger_discord_alerts(config, force: bool = False) -> dict:
    """
    Evaluate recent readings for anomalies and post to Discord webhook.
    Returns a status dict containing information on what was run and sent.
    """
    from django.utils import timezone
    from water.models import Pond, PondSensor, SensorReading, WaterThreshold, WaterSensorAlert
    from water.utils import METRIC_DEFINITIONS, check_metrics_status
    from water.views import get_pond_owner_for_thresholds, threshold_map_for

    now = timezone.now()
    if not force and config.last_discord_run_at:
        elapsed = now - config.last_discord_run_at
        if elapsed.total_seconds() < config.discord_notify_interval_seconds:
            logger.info(f"Skipping check: interval not elapsed yet ({elapsed.total_seconds():.1f}s / {config.discord_notify_interval_seconds}s)")
            return {"status": "waiting", "elapsed": elapsed.total_seconds()}

    # Resolve ponds to check
    ponds = list(config.ponds.all().order_by("name"))
    if not ponds and config.target_user_id:
        ponds = list(Pond.objects.filter(owners=config.target_user).order_by("name"))

    if not ponds:
        logger.warning("No ponds found for evaluation.")
        return {"status": "no_ponds"}

    # Find active sensors
    sensors = PondSensor.objects.filter(pond__in=ponds, is_active=True)
    if not sensors.exists():
        logger.info("No active sensors found in the target ponds.")
        return {"status": "no_sensors"}

    # We will group alert events by webhook URL
    # format: webhook_url -> {
    #     "triggered": {pond: {sensor: [(metric_key, val, limits)]}},
    #     "resolved_ponds": {pond: [resolved_alerts_list]}
    # }
    alerts_by_webhook = {}

    # Build metric lookup map
    metric_labels = {m["key"]: m for m in METRIC_DEFINITIONS}

    for pond in ponds:
        # Resolve webhook URL for this pond
        webhook_url = pond.discord_webhook_url or config.discord_webhook_url
        if not webhook_url or not webhook_url.startswith("http"):
            continue

        pond_sensors = sensors.filter(pond=pond)
        resolved_alerts_in_pond = []
        triggered_alerts_in_pond = {}  # sensor -> [(metric_key, val, limits)]

        for sensor in pond_sensors:
            # Fetch the absolute latest reading for this sensor
            reading = SensorReading.objects.filter(sensor=sensor).order_by("-measured_at").first()
            if not reading:
                continue

            owner = get_pond_owner_for_thresholds(sensor.pond) or config.target_user
            # Retrieve thresholds
            has_custom = WaterThreshold.objects.filter(user=owner, pond=sensor.pond, sensor=sensor).exists()
            thresholds = threshold_map_for(owner, sensor.pond, sensor=sensor if has_custom else None)

            status_map = check_metrics_status(reading, thresholds)

            for metric_key, status in status_map.items():
                if status == "muted":
                    continue

                val = getattr(reading, metric_key, None)
                limits = thresholds.get(metric_key, {})
                min_val = limits.get("min")
                max_val = limits.get("max")

                # Check if there is an active alert for this sensor and metric
                active_alert = WaterSensorAlert.objects.filter(
                    sensor=sensor,
                    metric=metric_key,
                    is_active=True
                ).first()

                if status == "warning":
                    # Anomaly detected
                    if not active_alert:
                        # Create a new active alert
                        alert = WaterSensorAlert.objects.create(
                            sensor=sensor,
                            metric=metric_key,
                            is_active=True,
                            last_notified_at=now
                        )
                        if sensor not in triggered_alerts_in_pond:
                            triggered_alerts_in_pond[sensor] = []
                        triggered_alerts_in_pond[sensor].append((metric_key, val, limits))
                    else:
                        # Anomaly persists, check duplicate suppression interval
                        should_notify = False
                        if active_alert.last_notified_at is None:
                            should_notify = True
                        else:
                            elapsed = now - active_alert.last_notified_at
                            if elapsed.total_seconds() >= config.discord_suppression_interval_seconds:
                                should_notify = True

                        if should_notify:
                            active_alert.last_notified_at = now
                            active_alert.save()
                            if sensor not in triggered_alerts_in_pond:
                                triggered_alerts_in_pond[sensor] = []
                            triggered_alerts_in_pond[sensor].append((metric_key, val, limits))
                        else:
                            active_alert.save()  # Just updates last_triggered_at
                elif status == "good":
                    # Normal state
                    if active_alert:
                        # Deactivate the existing alert
                        active_alert.is_active = False
                        active_alert.resolved_at = now
                        active_alert.save()
                        resolved_alerts_in_pond.append(active_alert)

        # Check if the pond is now completely normal (no active alerts left)
        # and we resolved at least one alert in this run
        active_alerts_left = WaterSensorAlert.objects.filter(sensor__pond=pond, is_active=True).exists()

        if webhook_url not in alerts_by_webhook:
            alerts_by_webhook[webhook_url] = {
                "triggered": {},
                "resolved_ponds": {}
            }

        if not active_alerts_left and resolved_alerts_in_pond:
            alerts_by_webhook[webhook_url]["resolved_ponds"][pond] = resolved_alerts_in_pond

        if triggered_alerts_in_pond:
            alerts_by_webhook[webhook_url]["triggered"][pond] = triggered_alerts_in_pond

    # Send webhooks grouped by URL
    sent_count = 0
    total_triggered = 0
    total_resolved = 0

    for webhook, data in alerts_by_webhook.items():
        triggered_ponds = data["triggered"]
        resolved_ponds = data["resolved_ponds"]
        
        if triggered_ponds or resolved_ponds:
            send_discord_webhook_v2(webhook, triggered_ponds, resolved_ponds, metric_labels)
            sent_count += 1
            
            # Count for status return
            for pond, sensors_dict in triggered_ponds.items():
                for sensor, metrics_list in sensors_dict.items():
                    total_triggered += len(metrics_list)
            for pond, resolved_list in resolved_ponds.items():
                total_resolved += len(resolved_list)

    sent_status = "sent" if sent_count > 0 else "no_updates"

    config.last_discord_run_at = now
    config.save(update_fields=["last_discord_run_at"])

    return {
        "status": "success",
        "sent_status": sent_status,
        "triggered_count": total_triggered,
        "resolved_count": total_resolved
    }


def send_discord_webhook_v2(
    webhook_url: str,
    triggered_ponds: dict,  # pond -> {sensor: [(metric_key, val, limits)]}
    resolved_ponds: dict,   # pond -> [resolved_alerts_list]
    metric_labels: dict
) -> None:
    """Send grouped warning and recovery embeds to Discord."""
    from django.utils import timezone
    embeds = []

    # 1. Process resolved ponds (green)
    for pond, resolved_list in resolved_ponds.items():
        recovered_lines = []
        for alert in resolved_list:
            metric_info = metric_labels.get(alert.metric, {"label": alert.metric})
            label = metric_info.get("label", alert.metric)
            short = metric_info.get("short", "")
            recovered_lines.append(f"• **{alert.sensor.name}**: {label} ({short}) 已恢復正常")

        embed = {
            "title": f"✅ 水質指標已恢復正常 - {pond.name}",
            "color": 1096065,  # Emerald green (#10b981)
            "description": "該池區的所有感測器水質指標已全部恢復正常範圍。\n\n" + "\n".join(recovered_lines),
            "timestamp": timezone.now().isoformat()
        }
        embeds.append(embed)

    # 2. Process triggered warnings (one embed per pond, red)
    for pond, sensors_dict in triggered_ponds.items():
        fields = []
        for sensor, metrics_list in sensors_dict.items():
            lines = []
            for metric_key, val, limits in metrics_list:
                metric_info = metric_labels.get(metric_key, {"label": metric_key, "unit": ""})
                unit = metric_info.get("unit", "")
                label = metric_info.get("label", metric_key)
                short = metric_info.get("short", "")
                min_val = limits.get("min")
                max_val = limits.get("max")

                status_text = "異常"
                if min_val is not None and val < min_val:
                    status_text = "偏低"
                elif max_val is not None and val > max_val:
                    status_text = "偏高"

                lines.append(
                    f"• **{label} ({short})**: `{val} {unit}`. "
                    f"(警戒: {min_val} ~ {max_val} {unit}, {status_text})"
                )
            
            fields.append({
                "name": f"感測器: {sensor.name}",
                "value": "\n".join(lines),
                "inline": False
            })

        embed = {
            "title": f"⚠️ 水質指標異常警告 - {pond.name}",
            "color": 14753096,  # Rose red (#e11d48)
            "fields": fields,
            "timestamp": timezone.now().isoformat()
        }
        embeds.append(embed)

    # Discord permits a maximum of 10 embeds per message. Send in chunks.
    chunk_size = 10
    for i in range(0, len(embeds), chunk_size):
        chunk = embeds[i:i+chunk_size]
        payload = {"embeds": chunk}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code not in (200, 204):
                logger.error(f"Discord webhook failed with status {resp.status_code}: {resp.text}")
            else:
                logger.info(f"Successfully sent {len(chunk)} grouped embeds to Discord.")
        except Exception as e:
            logger.exception("Failed to make POST request to Discord Webhook.")



def main() -> None:
    parser = argparse.ArgumentParser(description="Run sensor anomaly checking and Discord notifications.")
    parser.add_argument("--config-id", type=int, default=1, help="Simulation cron configuration ID.")
    parser.add_argument("--force", action="store_true", help="Force run notifications even if interval has not elapsed.")
    args = parser.parse_args()

    # Set up Django since we are executing in standalone mode
    setup_django()

    from water.models import WaterSimulationCron
    try:
        config = WaterSimulationCron.objects.get(pk=args.config_id)
    except WaterSimulationCron.DoesNotExist:
        logger.error(f"WaterSimulationCron configuration with ID {args.config_id} does not exist.")
        sys.exit(1)

    logger.info(f"Starting Discord alert evaluation for config #{config.pk} ({config.name})...")
    result = check_and_trigger_discord_alerts(config, force=args.force)
    logger.info(f"Done. Result: {result}")


if __name__ == "__main__":
    main()
