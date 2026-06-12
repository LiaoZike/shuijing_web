from django.contrib import admin

from .models import Pond, PondSensor, PondAerator, PondAeratorStateLog, SensorReading, WaterSimulationCron, WaterThreshold, WaterSensorAlert


@admin.register(Pond)
class PondAdmin(admin.ModelAdmin):
    list_display = ("name", "species", "display_owners", "description")
    filter_horizontal = ("owners",)

    def display_owners(self, obj):
        return ", ".join([user.email or user.username for user in obj.owners.all()])
    display_owners.short_description = "擁有者 (User)"


@admin.register(PondSensor)
class PondSensorAdmin(admin.ModelAdmin):
    list_display = ("name", "pond", "display_owners", "sensor_type", "x_position", "y_position", "is_active")
    list_filter = ("pond", "sensor_type", "is_active")

    def display_owners(self, obj):
        return ", ".join([user.email or user.username for user in obj.pond.owners.all()])
    display_owners.short_description = "所屬池區擁有者 (User)"


@admin.register(PondAerator)
class PondAeratorAdmin(admin.ModelAdmin):
    list_display = ("name", "pond", "x_position", "y_position", "is_active", "last_is_operating", "last_evaluated_at", "rules")
    list_filter = ("pond", "is_active", "last_is_operating")


@admin.register(PondAeratorStateLog)
class PondAeratorStateLogAdmin(admin.ModelAdmin):
    list_display = ("aerator", "pond", "recorded_at", "is_operating")
    list_filter = ("pond", "aerator", "is_operating")
    date_hierarchy = "recorded_at"


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = (
        "pond",
        "display_owners",
        "sensor",
        "measured_at",
        "temperature",
        "ph",
        "dissolved_oxygen",
        "ammonia_nitrogen",
        "nitrite",
        "salinity",
    )
    list_filter = ("pond", "sensor")
    date_hierarchy = "measured_at"

    def display_owners(self, obj):
        return ", ".join([user.email or user.username for user in obj.pond.owners.all()])
    display_owners.short_description = "所屬池區擁有者 (User)"


@admin.register(WaterThreshold)
class WaterThresholdAdmin(admin.ModelAdmin):
    list_display = ("user", "pond", "metric", "min_value", "max_value")
    list_filter = ("pond", "metric")


@admin.register(WaterSimulationCron)
class WaterSimulationCronAdmin(admin.ModelAdmin):
    list_display = ("name", "is_enabled", "target_user", "interval_seconds", "anomaly_rate", "anomaly_mode", "last_run_at", "discord_suppression_interval_seconds")
    filter_horizontal = ("ponds",)



@admin.register(WaterSensorAlert)
class WaterSensorAlertAdmin(admin.ModelAdmin):
    list_display = ("sensor", "metric", "is_active", "first_triggered_at", "last_triggered_at", "last_notified_at", "resolved_at")
    list_filter = ("is_active", "metric", "sensor__pond")

