from django.db import migrations


def add_default_sensors(apps, schema_editor):
    Pond = apps.get_model("water", "Pond")
    PondSensor = apps.get_model("water", "PondSensor")

    for pond in Pond.objects.all():
        if PondSensor.objects.filter(pond=pond).exists():
            continue

        PondSensor.objects.create(
            pond=pond,
            name="入口感測器",
            sensor_type="multi",
            x_position=24,
            y_position=34,
        )
        PondSensor.objects.create(
            pond=pond,
            name="中央感測器",
            sensor_type="multi",
            x_position=58,
            y_position=56,
        )


def remove_default_sensors(apps, schema_editor):
    PondSensor = apps.get_model("water", "PondSensor")
    PondSensor.objects.filter(name__in=["入口感測器", "中央感測器"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("water", "0002_pond_map_note_pond_owners_and_more"),
    ]

    operations = [
        migrations.RunPython(add_default_sensors, remove_default_sensors),
    ]
