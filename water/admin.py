from django.contrib import admin

from .models import Pond, PondSensor, SensorReading, WaterThreshold


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
