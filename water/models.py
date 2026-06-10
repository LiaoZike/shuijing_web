from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WaterMetric(models.TextChoices):
    DISSOLVED_OXYGEN = "dissolved_oxygen", "溶氧量"
    PH = "ph", "pH 值"
    AMMONIA_NITROGEN = "ammonia_nitrogen", "氨氮"
    NITRITE = "nitrite", "亞硝酸鹽"
    TEMPERATURE = "temperature", "溫度"


class Pond(models.Model):
    """養殖池基本資料。"""

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    species = models.CharField(max_length=50, default="文蛤")
    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="water_ponds",
        verbose_name="可查看帳號",
    )
    viewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="viewer_ponds",
        verbose_name="協作者 (唯讀)",
    )
    map_note = models.CharField("池區地圖備註", max_length=200, blank=True)

    # 穩定度公式權重設定
    stability_w_do = models.PositiveSmallIntegerField("穩定度-溶氧權重", default=40)
    stability_w_ph = models.PositiveSmallIntegerField("穩定度-pH權重", default=30)
    stability_w_temp = models.PositiveSmallIntegerField("穩定度-溫度權重", default=30)

    # 進排水口座標
    inlet_x = models.PositiveSmallIntegerField("進水口 X 座標", default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    inlet_y = models.PositiveSmallIntegerField("進水口 Y 座標", default=5, validators=[MinValueValidator(0), MaxValueValidator(100)])
    outlet_x = models.PositiveSmallIntegerField("排水口 X 座標", default=90, validators=[MinValueValidator(0), MaxValueValidator(100)])
    outlet_y = models.PositiveSmallIntegerField("排水口 Y 座標", default=95, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return self.name


class PondSensor(models.Model):
    """池區中的感測器與地圖位置。"""

    SENSOR_TYPE_CHOICES = [
        ("multi", "多合一感測器"),
        ("do", "溶氧感測器"),
        ("ph", "pH 感測器"),
        ("chem", "氨氮/亞硝酸鹽"),
        ("temp", "溫度感測器"),
    ]

    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="sensors")
    name = models.CharField(max_length=60)
    sensor_type = models.CharField(max_length=20, choices=SENSOR_TYPE_CHOICES, default="multi")
    x_position = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="地圖上的水平位置，0 到 100。",
    )
    y_position = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="地圖上的垂直位置，0 到 100。",
    )
    is_active = models.BooleanField(default=True)
    secret_token = models.CharField(
        "上傳金鑰 (Token)",
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        help_text="感測器上傳讀值時使用的唯一驗證金鑰。",
    )

    class Meta:
        ordering = ["pond", "name"]

    def save(self, *args, **kwargs):
        if not self.secret_token:
            import uuid
            self.secret_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pond.name} / {self.name}"


class SensorReading(models.Model):
    """感測器讀值 — 一次量到的水質快照。"""

    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="readings")
    sensor = models.ForeignKey(
        PondSensor,
        on_delete=models.SET_NULL,
        related_name="readings",
        null=True,
        blank=True,
    )
    measured_at = models.DateTimeField(db_index=True)

    temperature = models.FloatField(help_text="水溫 °C")
    ph = models.FloatField(help_text="pH 值")
    dissolved_oxygen = models.FloatField(help_text="溶氧 mg/L")
    ammonia_nitrogen = models.FloatField("氨氮 mg/L", null=True, blank=True)
    nitrite = models.FloatField("亞硝酸鹽 mg/L", null=True, blank=True)
    salinity = models.FloatField(help_text="鹽度 ppt", null=True, blank=True)

    class Meta:
        ordering = ["-measured_at"]
        indexes = [models.Index(fields=["pond", "-measured_at"])]

    def __str__(self):
        return f"{self.pond.name} @ {self.measured_at:%Y-%m-%d %H:%M}"


class WaterThreshold(models.Model):
    """使用者針對池區或個別感測器自訂的水質指標閾值。"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="water_thresholds")
    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="thresholds")
    sensor = models.ForeignKey(
        PondSensor,
        on_delete=models.CASCADE,
        related_name="thresholds",
        null=True,
        blank=True,
        verbose_name="專屬感測器"
    )
    metric = models.CharField(max_length=40, choices=WaterMetric.choices)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "pond", "sensor", "metric")
        ordering = ["pond", "sensor", "metric"]

    def __str__(self):
        sensor_part = f" / {self.sensor.name}" if self.sensor else " / 池區預設"
        return f"{self.user} / {self.pond.name}{sensor_part} / {self.get_metric_display()}"
