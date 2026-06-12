from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("water", "0015_pond_map_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="pond",
            name="is_public_viewer",
            field=models.BooleanField(
                default=False,
                help_text="啟用後，所有已登入使用者都能查看此池區與歷史數據，但不能編輯設定。",
                verbose_name="開放所有人唯讀查看",
            ),
        ),
    ]
