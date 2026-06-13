from django.urls import path

from . import views

app_name = "water"

urlpatterns = [
    path("", views.pond_list, name="pond_list"),
    path("dashboard/", views.pond_list, name="dashboard"),

    path("api/upload/", views.upload_sensor_reading, name="upload_sensor_reading"),
    path("api/voice/", views.voice_transcribe, name="voice_transcribe"),
    path("api/latest/", views.latest_water_api, name="latest_water_api"),

    path("add/", views.add_pond, name="add_pond"),
    path("<int:pond_id>/", views.pond_detail, name="pond_detail"),
    path("<int:pond_id>/manage/", views.manage_pond, name="manage_pond"),
    path("<int:pond_id>/delete/", views.delete_pond, name="delete_pond"),
    path("<int:pond_id>/share/", views.share_pond, name="share_pond"),
    path("<int:pond_id>/unshare/", views.unshare_pond, name="unshare_pond"),
    path("<int:pond_id>/history/", views.pond_history_api, name="pond_history_api"),
    path("<int:pond_id>/export-csv/", views.export_pond_csv, name="export_pond_csv"),
    path("<int:pond_id>/generate-mock-readings/", views.generate_mock_readings, name="generate_mock_readings"),

    path("ar-feed/", views.ar_feed, name="ar_feed"),
    path("ar-feed/score/", views.ar_feed_save_score, name="ar_feed_save_score"),
    path("ar-feed/leaderboard/", views.ar_feed_leaderboard, name="ar_feed_leaderboard"),
]
