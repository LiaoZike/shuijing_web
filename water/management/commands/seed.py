"""seed — 灌一批假水質資料進 DB，給課程示範用。

執行：
    python manage.py seed         # 灌假資料
    python manage.py seed --reset  # 先清空再灌
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from water.models import Pond, PondSensor, SensorReading

PONDS = [
    {"name": "1 號池", "species": "文蛤", "description": "靠近進水口的小池"},
    {"name": "2 號池", "species": "文蛤", "description": "中央大池"},
    {"name": "3 號池", "species": "白蝦", "description": "去年底新挖的池"},
]

# 一池產生最近 30 天的讀值，每天 4 筆（早/午/傍晚/夜）。
DAYS_BACK = 30
READINGS_PER_DAY = 4


class Command(BaseCommand):
    help = "Seed mock water quality data for the AI assistant demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Delete existing readings before seeding."
        )

    def handle(self, *args, **options):
        if options["reset"]:
            SensorReading.objects.all().delete()
            PondSensor.objects.all().delete()
            Pond.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing data."))

        ponds = []
        for spec in PONDS:
            pond, _ = Pond.objects.get_or_create(name=spec["name"], defaults=spec)
            PondSensor.objects.get_or_create(
                pond=pond,
                name="入口感測器",
                defaults={"sensor_type": "multi", "x_position": 22, "y_position": 34},
            )
            PondSensor.objects.get_or_create(
                pond=pond,
                name="中央感測器",
                defaults={"sensor_type": "multi", "x_position": 58, "y_position": 54},
            )
            PondSensor.objects.get_or_create(
                pond=pond,
                name="排水側感測器",
                defaults={"sensor_type": "chem", "x_position": 78, "y_position": 72},
            )
            ponds.append(pond)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        rng = random.Random(42)
        created = 0

        for pond in ponds:
            sensors = list(pond.sensors.filter(is_active=True))
            for day_offset in range(DAYS_BACK):
                day = now - timedelta(days=day_offset)
                for slot in range(READINGS_PER_DAY):
                    sensor = sensors[slot % len(sensors)] if sensors else None
                    measured_at = day.replace(hour=6 + slot * 5)
                    # 故意讓 1 號池在最近 2 天溶氧偏低，給 LLM 有題目可以講
                    low_do = pond.name == "1 號池" and day_offset < 2
                    SensorReading.objects.create(
                        pond=pond,
                        sensor=sensor,
                        measured_at=measured_at,
                        temperature=round(rng.uniform(26, 30), 1),
                        ph=round(rng.uniform(7.5, 8.6), 2),
                        dissolved_oxygen=round(
                            rng.uniform(2.5, 3.8) if low_do else rng.uniform(5.5, 7.5),
                            1,
                        ),
                        ammonia_nitrogen=round(rng.uniform(0.02, 0.18), 3),
                        nitrite=round(rng.uniform(0.01, 0.12), 3),
                        salinity=round(rng.uniform(20, 32), 1),
                    )
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(ponds)} ponds, {created} sensor readings "
                f"(over {DAYS_BACK} days, {READINGS_PER_DAY}/day)."
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                "提示：1 號池最近 2 天溶氧故意偏低（DO < 4），讓 LLM 有題目可以講。"
            )
        )
