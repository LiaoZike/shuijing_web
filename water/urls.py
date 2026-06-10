from django.urls import path

from . import views

app_name = "water"

urlpatterns = [
    # 主儀表板（池區列表）
    path("", views.pond_list, name="pond_list"),
    path("dashboard/", views.pond_list, name="dashboard"),  # 舊URL兼容
    
    # API上傳 (硬體專用)
    path("api/upload/", views.upload_sensor_reading, name="upload_sensor_reading"),
    
    # 池區管理與互動
    path("add/", views.add_pond, name="add_pond"),
    path("<int:pond_id>/", views.pond_detail, name="pond_detail"),
    path("<int:pond_id>/manage/", views.manage_pond, name="manage_pond"),
    path("<int:pond_id>/delete/", views.delete_pond, name="delete_pond"),
    path("<int:pond_id>/share/", views.share_pond, name="share_pond"),
    path("<int:pond_id>/unshare/", views.unshare_pond, name="unshare_pond"),
    
    # 數據查詢、測試與導出
    path("<int:pond_id>/history/", views.pond_history_api, name="pond_history_api"),
    path("<int:pond_id>/export-csv/", views.export_pond_csv, name="export_pond_csv"),
    path("<int:pond_id>/generate-mock-readings/", views.generate_mock_readings, name="generate_mock_readings"),
]
