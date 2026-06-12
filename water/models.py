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
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_ponds",
        verbose_name="建立者",
    )
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
    is_public_viewer = models.BooleanField(
        "開放所有人唯讀查看",
        default=False,
        help_text="啟用後，所有已登入使用者都能查看此池區與歷史數據，但不能編輯設定。",
    )
    map_note = models.CharField("池區地圖備註", max_length=200, blank=True)
    map_image = models.ImageField("感測器分佈地圖圖片", upload_to="pond_maps/", blank=True, null=True)
    discord_webhook_url = models.CharField("Discord Webhook URL", max_length=500, blank=True, default="")


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
        ("multi", "📟 多合一感測器"),
        ("do", "💨 溶氧感測器"),
        ("ph", "💧 pH 感測器"),
        ("chem", "# 氨氮/亞硝酸鹽"),
        ("temp", "🌡️ 溫度感測器"),
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


class PondAerator(models.Model):
    """池區中的水車與運作規則。"""
    pond = models.ForeignKey(Pond, on_delete=models.CASCADE, related_name="aerators")
    name = models.CharField("水車名稱", max_length=50)
    x_position = models.PositiveSmallIntegerField(
        "X 座標",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="地圖上的水平位置，0 到 100。",
    )
    y_position = models.PositiveSmallIntegerField(
        "Y 座標",
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="地圖上的垂直位置，0 到 100。",
    )
    is_active = models.BooleanField("是否啟用", default=True)
    # rules: [{"sensor_id": 1, "metric": "dissolved_oxygen", "operator": "lt", "value": 4.5}]
    rules = models.JSONField("運作規則", default=list, blank=True)

    def is_operating(self):
        """判斷水車是否正在運作"""
        if not self.is_active:
            return False
        if not self.rules:
            # 如果沒有設定任何規則，預設運作（或手動開啟為 True）
            return True
            
        for rule in self.rules:
            sensor_id = rule.get("sensor_id")
            metric = rule.get("metric")
            operator = rule.get("operator")
            try:
                target_value = float(rule.get("value", 0))
            except (ValueError, TypeError):
                continue
                
            try:
                sensor = self.pond.sensors.get(pk=sensor_id)
            except (PondSensor.DoesNotExist, ValueError, TypeError):
                return False
                
            latest_reading = sensor.readings.first()
            if not latest_reading:
                return False
                
            current_value = getattr(latest_reading, metric, None)
            if current_value is None:
                return False
                
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                return False
                
            if operator == "lt":
                if not (current_value < target_value):
                    return False
            elif operator == "le":
                if not (current_value <= target_value):
                    return False
            elif operator == "gt":
                if not (current_value > target_value):
                    return False
            elif operator == "ge":
                if not (current_value >= target_value):
                    return False
            elif operator == "eq":
                if not (current_value == target_value):
                    return False
            else:
                return False
                
        return True

    def get_enriched_rules(self):
        """傳回包含感測器名稱與指標中文名稱的規則清單"""
        enriched = []
        metric_labels = {
            "temperature": "水溫",
            "ph": "pH 值",
            "dissolved_oxygen": "溶氧量",
            "ammonia_nitrogen": "氨氮",
            "nitrite": "亞硝酸鹽",
            "salinity": "鹽度",
        }
        for rule in self.rules:
            sensor_id = rule.get("sensor_id")
            metric = rule.get("metric")
            operator = rule.get("operator")
            value = rule.get("value")
            
            sensor_name = "未知感測器"
            try:
                sensor = self.pond.sensors.get(pk=sensor_id)
                sensor_name = sensor.name
            except Exception:
                pass
                
            enriched.append({
                "sensor_id": sensor_id,
                "sensor_name": sensor_name,
                "metric": metric,
                "metric_label": metric_labels.get(metric, metric),
                "operator": operator,
                "value": value,
            })
        return enriched

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


class WaterSimulationCron(models.Model):
    """Admin-controlled browser cron settings for simulated sensor uploads."""

    ANOMALY_MODE_CHOICES = [
        ("mixed", "Mixed"),
        ("pond", "Whole pond"),
        ("sensor", "Single sensor"),
    ]

    ANOMALY_SCOPE_CHOICES = [
        ("", "None"),
        ("pond", "Whole pond"),
        ("sensor", "Single sensor"),
    ]

    name = models.CharField(max_length=80, default="Water simulation")
    is_enabled = models.BooleanField(default=False)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="water_simulation_crons",
    )
    ponds = models.ManyToManyField(Pond, blank=True, related_name="simulation_crons")
    interval_seconds = models.PositiveIntegerField(default=500)
    anomaly_rate = models.FloatField(default=0.2)
    anomaly_mode = models.CharField(max_length=20, choices=ANOMALY_MODE_CHOICES, default="mixed")
    anomaly_duration_rounds = models.PositiveIntegerField(default=3)

    active_anomaly_pond = models.ForeignKey(
        Pond,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    active_anomaly_scope = models.CharField(max_length=20, choices=ANOMALY_SCOPE_CHOICES, blank=True, default="")
    active_anomaly_type = models.CharField(max_length=30, blank=True, default="")
    active_anomaly_remaining_rounds = models.PositiveIntegerField(default=0)
    active_anomaly_sensor_index = models.PositiveIntegerField(null=True, blank=True)

    last_run_at = models.DateTimeField(null=True, blank=True)
    last_result = models.TextField(blank=True, default="")
    discord_webhook_url = models.CharField(
        "Discord Webhook URL",
        max_length=500,
        blank=True,
        default="",
    )
    discord_notify_interval_seconds = models.PositiveIntegerField(
        "Discord 判讀間隔 (秒)",
        default=300,
    )
    discord_suppression_interval_seconds = models.PositiveIntegerField(
        "相同項目避免重複通知間隔 (秒)",
        default=3600,
    )
    last_discord_run_at = models.DateTimeField(
        "Discord 上次執行時間",
        null=True,
        blank=True,
    )
    discord_is_enabled = models.BooleanField(
        "啟用 Discord 警報通知",
        default=False,
    )
    discord_last_result = models.TextField(
        "Discord 上次執行結果",
        blank=True,
        default="",
    )

    asr_url = models.CharField(
        "語音辨識 API URL（主要）",
        max_length=500,
        blank=True,
        default="",
        help_text="Colab/ngrok 等語音辨識服務的主要 URL，例如 https://xxxx.ngrok-free.app",
    )
    asr_backup_url = models.CharField(
        "語音辨識 API URL（備用）",
        max_length=500,
        blank=True,
        default="",
        help_text="主要 URL 無法連線時的備用 URL",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WaterSensorAlert(models.Model):
    """感測器指標異常警報紀錄，用於避免重複發送 Discord 通知"""

    sensor = models.ForeignKey(
        PondSensor,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name="感測器",
    )
    metric = models.CharField("指標", max_length=40, choices=WaterMetric.choices)
    is_active = models.BooleanField("是否啟動中", default=True, db_index=True)
    first_triggered_at = models.DateTimeField("首次觸發時間", auto_now_add=True)
    last_triggered_at = models.DateTimeField("最近觸發時間", auto_now=True)
    last_notified_at = models.DateTimeField("上次通知時間", null=True, blank=True)
    resolved_at = models.DateTimeField("恢復正常時間", null=True, blank=True)


    class Meta:
        verbose_name = "感測器警報"
        verbose_name_plural = "感測器警報列表"
        ordering = ["-first_triggered_at"]

    def __str__(self):
        status = "未解決" if self.is_active else "已恢復"
        return f"{self.sensor} / {self.get_metric_display()} ({status})"
