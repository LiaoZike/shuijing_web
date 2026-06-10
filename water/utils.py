METRIC_DEFINITIONS = [
    {
        "key": "dissolved_oxygen",
        "label": "溶氧量",
        "short": "DO",
        "unit": "mg/L",
        "default_min": 4.5,
        "default_max": 8.5,
    },
    {
        "key": "ph",
        "label": "pH 值",
        "short": "pH",
        "unit": "",
        "default_min": 7.5,
        "default_max": 8.5,
    },
    {
        "key": "ammonia_nitrogen",
        "label": "氨氮",
        "short": "NH3-N",
        "unit": "mg/L",
        "default_min": 0,
        "default_max": 0.2,
    },
    {
        "key": "nitrite",
        "label": "亞硝酸鹽",
        "short": "NO2",
        "unit": "mg/L",
        "default_min": 0,
        "default_max": 0.15,
    },
    {
        "key": "temperature",
        "label": "溫度",
        "short": "Temp",
        "unit": "°C",
        "default_min": 20,
        "default_max": 30,
    },
]


def default_thresholds():
    return {
        metric["key"]: {
            "min": metric["default_min"],
            "max": metric["default_max"],
        }
        for metric in METRIC_DEFINITIONS
    }


def check_metrics_status(reading, thresholds=None):
    if not reading:
        return {}

    active_thresholds = default_thresholds()
    if thresholds:
        for key, limits in thresholds.items():
            if key in active_thresholds:
                active_thresholds[key].update(limits)

    status = {}
    for metric in METRIC_DEFINITIONS:
        key = metric["key"]
        value = getattr(reading, key, None)
        if value is None:
            status[key] = "muted"
            continue

        limits = active_thresholds[key]
        min_value = limits.get("min")
        max_value = limits.get("max")

        if (min_value is not None and value < min_value) or (max_value is not None and value > max_value):
            status[key] = "warning"
        else:
            status[key] = "good"

    return status


def reading_status(reading, thresholds=None):
    if not reading:
        return {
            "label": "尚無資料",
            "tone": "muted",
            "message": "此池尚未收到感測資料。",
        }

    active_thresholds = default_thresholds()
    if thresholds:
        for key, limits in thresholds.items():
            if key in active_thresholds:
                active_thresholds[key].update(limits)

    warnings = []

    for metric in METRIC_DEFINITIONS:
        value = getattr(reading, metric["key"], None)
        if value is None:
            continue

        limits = active_thresholds[metric["key"]]
        min_value = limits.get("min")
        max_value = limits.get("max")

        if min_value is not None and value < min_value:
            warnings.append(f"{metric['label']}偏低")
        elif max_value is not None and value > max_value:
            warnings.append(f"{metric['label']}偏高")

    if warnings:
        return {
            "label": "需留意",
            "tone": "warning",
            "message": "、".join(warnings),
        }

    return {
        "label": "穩定",
        "tone": "good",
        "message": "主要水質指標落在可觀察範圍內。",
    }


def calculate_stability(reading, thresholds, w_do, w_ph, w_temp):
    if not reading:
        return None

    total_w = int(w_do or 0) + int(w_ph or 0) + int(w_temp or 0)
    if total_w == 0:
        return 100.0

    scores = {}
    metrics = {
        "dissolved_oxygen": int(w_do or 0),
        "ph": int(w_ph or 0),
        "temperature": int(w_temp or 0)
    }

    for key, weight in metrics.items():
        if weight == 0:
            scores[key] = 100.0
            continue

        value = getattr(reading, key, None)
        if value is None:
            scores[key] = 100.0
            continue

        limits = thresholds.get(key, {})
        t_min = limits.get("min")
        t_max = limits.get("max")

        if t_min is None or t_max is None or t_max <= t_min:
            scores[key] = 100.0
            continue

        if t_min <= value <= t_max:
            scores[key] = 100.0
        else:
            center = (t_max + t_min) / 2.0
            half_width = (t_max - t_min) / 2.0
            deviation = abs(value - center) - half_width
            ratio = deviation / half_width
            scores[key] = max(0.0, 100.0 - (ratio * 50.0))

    weighted_score = (
        scores["dissolved_oxygen"] * metrics["dissolved_oxygen"] +
        scores["ph"] * metrics["ph"] +
        scores["temperature"] * metrics["temperature"]
    ) / total_w
    return round(weighted_score, 1)
