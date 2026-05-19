from django.db import models


class Pond(models.Model):
    """養殖池基本資料。"""

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    species = models.CharField(max_length=50, default="文蛤")

    def __str__(self):
        return self.name


class SensorReading(models.Model):
    """感測器讀值 — 一次量到的水質快照。"""

    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="readings")
    measured_at = models.DateTimeField(db_index=True)

    temperature = models.FloatField(help_text="水溫 °C")
    ph = models.FloatField(help_text="pH 值")
    dissolved_oxygen = models.FloatField(help_text="溶氧 mg/L")
    salinity = models.FloatField(help_text="鹽度 ppt", null=True, blank=True)

    class Meta:
        ordering = ["-measured_at"]
        indexes = [models.Index(fields=["pond", "-measured_at"])]

    def __str__(self):
        return f"{self.pond.name} @ {self.measured_at:%Y-%m-%d %H:%M}"
