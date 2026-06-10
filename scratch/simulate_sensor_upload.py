#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Periodically simulate water sensor readings and POST them to the upload API.

The default configuration groups sensors by pond. Sensors in the same pond
share one slowly drifting water state, so their values stay close unless an
anomaly is generated.

Examples:
    python scratch/simulate_sensor_upload.py
    python scratch/simulate_sensor_upload.py --interval 30 --limit 20
    python scratch/simulate_sensor_upload.py --anomaly 0.25
    python scratch/simulate_sensor_upload.py --pond pond2:token_a,token_b
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Iterable

import requests


# ========== Common settings ==========
# Most day-to-day tuning can be done here. Command-line args still override these.

DEFAULT_URL = "http://127.0.0.1:8000/water/api/upload/"
DEFAULT_INTERVAL_SECONDS = 300
DEFAULT_ANOMALY_RATE = 0.20
DEFAULT_ANOMALY_MODE = "mixed"  # mixed, pond, or sensor
DEFAULT_ANOMALY_DURATION_ROUNDS = 3
DEFAULT_LIMIT_ROUNDS = 0  # 0 means forever

DEFAULT_PONDS = {
    "pond1": [
        "6c61dd51d65e4870b6d4aecd632dda40",
        "991f2bcf95974f8e80741445d56ffe75",
    ],
}


# ========== Simulation behavior ==========

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


@dataclass
class PondState:
    name: str
    tokens: list[str]
    values: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.values:
            self.values = {
                key: random.uniform(low, high)
                for key, (low, high) in NORMAL_LIMITS.items()
            }

    def drift(self) -> None:
        for key, step in DRIFT.items():
            low, high = NORMAL_LIMITS[key]
            self.values[key] = clamp(self.values[key] + random.uniform(-step, step), low, high)


@dataclass
class ActiveAnomaly:
    pond_name: str
    scope: str
    anomaly_type: str
    remaining_rounds: int
    sensor_index: int | None = None

    @property
    def label(self) -> str:
        target = f"sensor{self.sensor_index + 1}" if self.sensor_index is not None else "pond"
        return f"{self.anomaly_type}:{target}:{self.remaining_rounds}r"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def jitter(values: dict[str, float]) -> dict[str, float]:
    return {
        key: values[key] + random.uniform(-SENSOR_NOISE[key], SENSOR_NOISE[key])
        for key in values
    }


def apply_anomaly(values: dict[str, float], anomaly_type: str) -> dict[str, float]:
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


def format_payload(token: str, reading: dict[str, float]) -> dict:
    return {
        "secret_token": token,
        "temperature": round(reading["temperature"], 1),
        "ph": round(reading["ph"], 2),
        "dissolved_oxygen": round(reading["dissolved_oxygen"], 1),
        "ammonia_nitrogen": round(reading["ammonia_nitrogen"], 3),
        "nitrite": round(reading["nitrite"], 3),
        "salinity": round(reading["salinity"], 1),
    }


def choose_anomaly_mode(configured_mode: str) -> str:
    if configured_mode == "mixed":
        return random.choice(["pond", "sensor"])
    return configured_mode


def build_round_payloads(
    pond: PondState,
    active_anomaly: ActiveAnomaly | None,
) -> Iterable[tuple[str, int, dict]]:
    pond.drift()

    for index, token in enumerate(pond.tokens, start=1):
        base = pond.values
        anomaly_label = "normal"
        if active_anomaly and active_anomaly.pond_name == pond.name:
            is_affected = active_anomaly.scope == "pond" or active_anomaly.sensor_index == index - 1
            if is_affected:
                base = apply_anomaly(base, active_anomaly.anomaly_type)
                anomaly_label = active_anomaly.label

        yield anomaly_label, index, format_payload(token, jitter(base))


def post_payload(url: str, pond_name: str, sensor_index: int, anomaly: str, payload: dict) -> None:
    response = requests.post(url, json=payload, timeout=8)
    prefix = f"[{pond_name} sensor{sensor_index}]"

    if response.ok:
        data = response.json()
        print(
            f"OK {prefix} reading_id={data.get('reading_id')} anomaly={anomaly} "
            f"temp={payload['temperature']} pH={payload['ph']} "
            f"DO={payload['dissolved_oxygen']} "
            f"NH3={payload['ammonia_nitrogen']} NO2={payload['nitrite']}"
        )
        return

    print(f"FAIL {prefix} status={response.status_code} body={response.text}")


def post_round_payloads(url: str, round_payloads: list[tuple[str, int, str, dict]]) -> None:
    if not round_payloads:
        return

    with ThreadPoolExecutor(max_workers=len(round_payloads)) as executor:
        futures = [
            executor.submit(post_payload, url, pond_name, sensor_index, anomaly, payload)
            for pond_name, sensor_index, anomaly, payload in round_payloads
        ]
        for future in as_completed(futures):
            future.result()


def parse_pond_spec(spec: str) -> tuple[str, list[str]]:
    if ":" not in spec:
        raise argparse.ArgumentTypeError("pond format must be name:token1,token2")

    name, token_text = spec.split(":", 1)
    tokens = [token.strip() for token in token_text.split(",") if token.strip()]
    if not name.strip() or not tokens:
        raise argparse.ArgumentTypeError("pond format must be name:token1,token2")

    return name.strip(), tokens


def build_ponds(args: argparse.Namespace) -> list[PondState]:
    pond_map = {name: list(tokens) for name, tokens in DEFAULT_PONDS.items()}

    for name, tokens in args.pond or []:
        pond_map[name] = tokens

    if args.tokens:
        pond_map = {"manual": args.tokens}

    return [PondState(name=name, tokens=tokens) for name, tokens in pond_map.items()]


def maybe_start_anomaly(
    ponds: list[PondState],
    anomaly_rate: float,
    anomaly_mode: str,
    anomaly_duration: int,
) -> ActiveAnomaly | None:
    if not ponds or random.random() >= anomaly_rate:
        return None

    pond = random.choice(ponds)
    scope = choose_anomaly_mode(anomaly_mode)
    sensor_index = random.randrange(len(pond.tokens)) if scope == "sensor" else None

    return ActiveAnomaly(
        pond_name=pond.name,
        scope=scope,
        anomaly_type=random.choice(["low_do", "high_ph", "high_temp", "high_chem"]),
        remaining_rounds=anomaly_duration,
        sensor_index=sensor_index,
    )


def run(
    url: str,
    ponds: list[PondState],
    interval: float,
    anomaly_rate: float,
    anomaly_mode: str,
    anomaly_duration: int,
    limit: int,
) -> None:
    count = 0
    active_anomaly: ActiveAnomaly | None = None
    print(f"POST URL: {url}")
    print(
        f"Interval: {interval}s, anomaly rate: {anomaly_rate * 100:.1f}%, "
        f"mode: {anomaly_mode}, duration: {anomaly_duration} rounds"
    )
    for pond in ponds:
        print(f"{pond.name}: {', '.join(token[:8] + '...' for token in pond.tokens)}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            round_started_at = time.monotonic()
            if active_anomaly is None:
                active_anomaly = maybe_start_anomaly(ponds, anomaly_rate, anomaly_mode, anomaly_duration)
                if active_anomaly:
                    print(f"ANOMALY START {active_anomaly.pond_name} {active_anomaly.label}")

            round_payloads = []
            for pond in ponds:
                for anomaly, sensor_index, payload in build_round_payloads(pond, active_anomaly):
                    round_payloads.append((pond.name, sensor_index, anomaly, payload))

            post_round_payloads(url, round_payloads)

            if active_anomaly:
                active_anomaly.remaining_rounds -= 1
                if active_anomaly.remaining_rounds <= 0:
                    print(f"ANOMALY END {active_anomaly.pond_name}")
                    active_anomaly = None

            count += 1
            if limit and count >= limit:
                break

            elapsed = time.monotonic() - round_started_at
            time.sleep(max(0.0, interval - elapsed))
    except KeyboardInterrupt:
        print("\nStopped.")


def setup_django() -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shuijing.settings")

    import django
    django.setup()


def run_from_django_config(config_id: int, limit: int) -> None:
    setup_django()

    from water.models import WaterSimulationCron
    from water.simulator import run_simulation_round

    count = 0
    print(f"Using WaterSimulationCron config #{config_id}")
    try:
        while True:
            round_started_at = time.monotonic()
            config = WaterSimulationCron.objects.get(pk=config_id)
            result = run_simulation_round(config.pk)
            config.refresh_from_db()
            print(
                f"OK created={result.created_count} ponds={result.pond_count} "
                f"sensors={result.sensor_count} anomaly={result.anomaly_label}"
            )

            count += 1
            if limit and count >= limit:
                break

            elapsed = time.monotonic() - round_started_at
            time.sleep(max(0.0, config.interval_seconds - elapsed))
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate periodic water sensor uploads.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Upload API URL.")
    parser.add_argument("--pond", action="append", type=parse_pond_spec, help="Pond sensors as name:token1,token2.")
    parser.add_argument("--tokens", nargs="+", help="Backward-compatible manual tokens. These become one pond.")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS, help="Seconds between upload rounds.")
    parser.add_argument("--anomaly", type=float, default=DEFAULT_ANOMALY_RATE, help="Anomaly rate from 0.0 to 1.0 per pond round.")
    parser.add_argument(
        "--anomaly-mode",
        choices=["mixed", "pond", "sensor"],
        default=DEFAULT_ANOMALY_MODE,
        help="Whether anomalies affect a whole pond, one sensor, or either.",
    )
    parser.add_argument(
        "--anomaly-duration",
        type=int,
        default=DEFAULT_ANOMALY_DURATION_ROUNDS,
        help="How many upload rounds an anomaly should continue once triggered.",
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT_ROUNDS, help="Number of upload rounds. 0 means forever.")
    parser.add_argument("--config-id", type=int, help="Run using a WaterSimulationCron database config.")
    args = parser.parse_args()

    if args.config_id:
        run_from_django_config(args.config_id, max(0, args.limit))
        return

    interval = max(1.0, args.interval)
    anomaly_rate = max(0.0, min(1.0, args.anomaly))
    anomaly_duration = max(1, args.anomaly_duration)
    ponds = build_ponds(args)

    run(args.url, ponds, interval, anomaly_rate, args.anomaly_mode, anomaly_duration, max(0, args.limit))


if __name__ == "__main__":
    main()
