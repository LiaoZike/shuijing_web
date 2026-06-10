import random
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import Pond, PondSensor, SensorReading, WaterSimulationCron


NORMAL_LIMITS = {
    "temperature": (26.5, 29.5),
    "ph": (7.65, 8.25),
    "dissolved_oxygen": (5.7, 7.1),
    "ammonia_nitrogen": (0.02, 0.12),
    "nitrite": (0.02, 0.10),
    "salinity": (13.0, 15.5),
}

DRIFT = {
    "temperature": 0.08,
    "ph": 0.015,
    "dissolved_oxygen": 0.08,
    "ammonia_nitrogen": 0.003,
    "nitrite": 0.003,
    "salinity": 0.03,
}

SENSOR_NOISE = {
    "temperature": 0.15,
    "ph": 0.03,
    "dissolved_oxygen": 0.12,
    "ammonia_nitrogen": 0.005,
    "nitrite": 0.005,
    "salinity": 0.08,
}

ANOMALY_TYPES = ["low_do", "high_ph", "high_temp", "high_chem"]


@dataclass
class SimulationResult:
    created_count: int
    pond_count: int
    sensor_count: int
    anomaly_label: str


def clamp(value, low, high):
    return max(low, min(high, value))


def jitter(values):
    return {
        key: values[key] + random.uniform(-SENSOR_NOISE[key], SENSOR_NOISE[key])
        for key in values
    }


def reading_to_values(reading):
    if not reading:
        return {
            key: random.uniform(low, high)
            for key, (low, high) in NORMAL_LIMITS.items()
        }

    values = {
        "temperature": reading.temperature,
        "ph": reading.ph,
        "dissolved_oxygen": reading.dissolved_oxygen,
        "ammonia_nitrogen": reading.ammonia_nitrogen,
        "nitrite": reading.nitrite,
        "salinity": reading.salinity,
    }
    for key, (low, high) in NORMAL_LIMITS.items():
        if values[key] is None:
            values[key] = random.uniform(low, high)
    return values


def pond_base_values(pond):
    latest = SensorReading.objects.filter(pond=pond).order_by("-measured_at").first()
    values = reading_to_values(latest)
    for key, step in DRIFT.items():
        low, high = NORMAL_LIMITS[key]
        values[key] = clamp(values[key] + random.uniform(-step, step), low, high)
    return values


def apply_anomaly(values, anomaly_type):
    reading = dict(values)
    if anomaly_type == "low_do":
        reading["dissolved_oxygen"] = random.uniform(2.7, 4.0)
    elif anomaly_type == "high_ph":
        reading["ph"] = random.uniform(8.75, 9.25)
    elif anomaly_type == "high_temp":
        reading["temperature"] = random.uniform(31.0, 34.0)
        reading["dissolved_oxygen"] = random.uniform(4.3, 5.3)
    elif anomaly_type == "high_chem":
        reading["ammonia_nitrogen"] = random.uniform(0.24, 0.42)
        reading["nitrite"] = random.uniform(0.20, 0.34)
    return reading


def choose_anomaly_mode(configured_mode):
    if configured_mode == "mixed":
        return random.choice(["pond", "sensor"])
    return configured_mode


def start_anomaly_if_needed(config, ponds):
    if config.active_anomaly_remaining_rounds > 0 and config.active_anomaly_pond_id:
        return
    if not ponds or random.random() >= max(0.0, min(1.0, config.anomaly_rate)):
        clear_anomaly(config)
        return

    pond = random.choice(list(ponds))
    scope = choose_anomaly_mode(config.anomaly_mode)
    sensor_count = pond.sensors.filter(is_active=True).count()
    sensor_index = random.randrange(sensor_count) if scope == "sensor" and sensor_count else None

    config.active_anomaly_pond = pond
    config.active_anomaly_scope = scope
    config.active_anomaly_type = random.choice(ANOMALY_TYPES)
    config.active_anomaly_remaining_rounds = max(1, config.anomaly_duration_rounds)
    config.active_anomaly_sensor_index = sensor_index


def clear_anomaly(config):
    config.active_anomaly_pond = None
    config.active_anomaly_scope = ""
    config.active_anomaly_type = ""
    config.active_anomaly_remaining_rounds = 0
    config.active_anomaly_sensor_index = None


def anomaly_label(config):
    if not config.active_anomaly_pond_id or config.active_anomaly_remaining_rounds <= 0:
        return "normal"
    if config.active_anomaly_scope == "sensor" and config.active_anomaly_sensor_index is not None:
        target = f"sensor{config.active_anomaly_sensor_index + 1}"
    else:
        target = "pond"
    return (
        f"{config.active_anomaly_pond.name}:"
        f"{config.active_anomaly_type}:{target}:"
        f"{config.active_anomaly_remaining_rounds}r"
    )


def make_reading(pond, sensor, values, measured_at):
    payload = jitter(values)
    return SensorReading(
        pond=pond,
        sensor=sensor,
        measured_at=measured_at,
        temperature=round(payload["temperature"], 1),
        ph=round(payload["ph"], 2),
        dissolved_oxygen=round(payload["dissolved_oxygen"], 1),
        ammonia_nitrogen=round(payload["ammonia_nitrogen"], 3),
        nitrite=round(payload["nitrite"], 3),
        salinity=round(payload["salinity"], 1),
    )


@transaction.atomic
def run_simulation_round(config_id, force=False, force_anomaly=False):
    config = WaterSimulationCron.objects.select_for_update().get(pk=config_id)
    
    # Final concurrency guard under row lock
    now = timezone.now()
    if config.last_run_at:
        from datetime import timedelta
        next_run_at = config.last_run_at + timedelta(seconds=max(1, config.interval_seconds))
        if not force and now < next_run_at:
            return SimulationResult(
                created_count=0,
                pond_count=0,
                sensor_count=0,
                anomaly_label="already_run",
            )

    ponds = list(config.ponds.all().order_by("name"))
    if not ponds and config.target_user_id:
        ponds = list(Pond.objects.filter(owners=config.target_user).order_by("name"))

    in_memory_anomaly = None
    if force_anomaly and ponds:
        # Pick a random pond and sensor to have anomaly for this round only
        import random
        # Filter ponds that have active sensors
        ponds_with_sensors = [p for p in ponds if p.sensors.filter(is_active=True).exists()]
        if ponds_with_sensors:
            target_pond = random.choice(ponds_with_sensors)
            sensors = list(target_pond.sensors.filter(is_active=True).order_by("name"))
            sensor_index = random.randrange(len(sensors))
            anomaly_type = random.choice(ANOMALY_TYPES)
            in_memory_anomaly = {
                "pond_id": target_pond.pk,
                "sensor_index": sensor_index,
                "type": anomaly_type
            }
            label = f"{target_pond.name}:{anomaly_type}:sensor{sensor_index + 1}:1r (forced)"
        else:
            label = "normal"
    else:
        start_anomaly_if_needed(config, ponds)
        label = anomaly_label(config)

    measured_at = timezone.now()
    readings = []
    sensor_total = 0

    for pond in ponds:
        sensors = list(pond.sensors.filter(is_active=True).order_by("name"))
        sensor_total += len(sensors)
        base_values = pond_base_values(pond)
        for index, sensor in enumerate(sensors):
            values = base_values
            
            # Check if this sensor is selected for one-off forced anomaly in memory
            if in_memory_anomaly and in_memory_anomaly["pond_id"] == pond.pk and in_memory_anomaly["sensor_index"] == index:
                values = apply_anomaly(base_values, in_memory_anomaly["type"])
            # Otherwise check if there is an active persistent anomaly from database
            elif (
                not in_memory_anomaly
                and config.active_anomaly_pond_id == pond.pk
                and config.active_anomaly_remaining_rounds > 0
                and (
                    config.active_anomaly_scope == "pond"
                    or config.active_anomaly_sensor_index == index
                )
            ):
                values = apply_anomaly(base_values, config.active_anomaly_type)
                
            readings.append(make_reading(pond, sensor, values, measured_at))

    if readings:
        SensorReading.objects.bulk_create(readings)

    # Only decrement persistent anomalies from db if we didn't run a forced one-off anomaly
    if not force_anomaly and config.active_anomaly_remaining_rounds > 0:
        config.active_anomaly_remaining_rounds -= 1
        if config.active_anomaly_remaining_rounds <= 0:
            clear_anomaly(config)

    config.last_run_at = measured_at
    config.last_result = (
        f"{measured_at:%Y-%m-%d %H:%M:%S} created={len(readings)} "
        f"ponds={len(ponds)} sensors={sensor_total} anomaly={label}"
    )
    config.save()

    return SimulationResult(
        created_count=len(readings),
        pond_count=len(ponds),
        sensor_count=sensor_total,
        anomaly_label=label,
    )

