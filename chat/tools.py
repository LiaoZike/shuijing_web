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


def _pond_sensor_summary(pond) -> list[dict]:
    sensors = []
    for sensor in pond.sensors.filter(is_active=True).order_by("name"):
        latest = sensor.readings.first()
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
        "sensors": _pond_sensor_summary(pond),
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


def get_pond_summary(days: int = 7, user=None) -> dict:
    from datetime import timedelta
    from django.db.models import Avg, Count, Max, Min
    from water.views import visible_ponds_for

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
            if (latest_do is not None and latest_do < 4) or (min_do is not None and min_do < 4):
                status = "low_oxygen"
            elif (
                (latest_do is not None and latest_do < 5)
                or (min_do is not None and min_do < 5)
                or avg_do < 5
            ):
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
                "sensors": _pond_sensor_summary(pond),
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
]


_TOOL_REGISTRY = {
    "list_upcoming_activities": list_upcoming_activities,
    "search_site_content": search_site_content,
    "get_latest_notices": get_latest_notices,
    "list_usr_highlights": list_usr_highlights,
    "get_latest_water_quality": get_latest_water_quality,
    "get_average_do": get_average_do,
    "get_aerator_status": get_aerator_status,
    "get_pond_summary": get_pond_summary,
}


def dispatch(name: str, arguments: dict, user=None) -> dict:
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        if name in ("get_latest_water_quality", "get_average_do", "get_aerator_status", "get_pond_summary"):
            return fn(**arguments, user=user)
        return fn(**arguments)
    except TypeError as exc:
        return {"error": f"tool arguments error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"tool execution error: {type(exc).__name__}: {exc}"}
