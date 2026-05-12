from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from core.models import Activity, AiotProject, Notice, RelatedLink, UsrAchievement


def _trim(value: str | None, limit: int = 180) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit].rstrip()}..."


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
]


_TOOL_REGISTRY = {
    "list_upcoming_activities": list_upcoming_activities,
    "search_site_content": search_site_content,
    "get_latest_notices": get_latest_notices,
    "list_usr_highlights": list_usr_highlights,
}


def dispatch(name: str, arguments: dict) -> dict:
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return fn(**arguments)
    except TypeError as exc:
        return {"error": f"tool arguments error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"tool execution error: {type(exc).__name__}: {exc}"}
