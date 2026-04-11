import os
import django
import shutil
from django.conf import settings
from django.apps import apps
from django.core.files.storage import default_storage

# 初始化 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

# 定義要清理的模型、App 及其欄位
MODELS_TO_CLEAN = [
    ('core', 'HeroSlide', ['image']),
    ('core', 'Activity', ['cover_image']),
    ('core', 'AiotProject', ['image']),
    ('core', 'UsrAchievement', ['image']),
    ('core', 'UsrVideo', ['video_file']),
    ('core', 'UsrVideoImage', ['image']),
    ('core', 'UsrTeamMember', ['image']),
    ('core', 'NoticeImage', ['image']),
    ('guide', 'StorySpot', ['cover_image']),
    ('guide', 'ARAsset', ['marker_image', 'target_file', 'video_file', 'audio_file', 'image_file', 'model_file']),
]

def clean_filename(filename):
    """標準化副檔名"""
    name, ext = os.path.splitext(filename)
    return ext.lower()

def cleanup_media():
    print("--- 開始全站 Media 大掃除 ---")
    
    count = 0
    errors = 0

    for app_label, model_name, fields in MODELS_TO_CLEAN:
        try:
            Model = apps.get_model(app_label, model_name)
            instances = Model.objects.all()
            print(f"\n[檢查模型] {app_label}.{model_name} (共 {instances.count()} 筆)")
            
            for instance in instances:
                for field_name in fields:
                    field_file = getattr(instance, field_name)
                    
                    if not field_file or not field_file.name:
                        continue
                        
                    old_path = field_file.path
                    if not os.path.exists(old_path):
                        print(f"  [跳過] 檔案不存在: {field_file.name}")
                        continue

                    # 產生新檔名規範：[model]_[id]_[field].[ext]
                    ext = clean_filename(field_file.name)
                    new_filename = f"{model_name.lower()}_{instance.id}_{field_name}{ext}"
                    
                    # 取得原始目錄路徑
                    original_rel_dir = os.path.dirname(field_file.name)
                    new_rel_path = os.path.join(original_rel_dir, new_filename)
                    new_abs_path = os.path.join(settings.MEDIA_ROOT, new_rel_path)

                    # 如果檔名已經是標準格式，則跳過
                    if os.path.basename(old_path) == new_filename:
                        continue

                    try:
                        # 確保目標資料夾存在
                        os.makedirs(os.path.dirname(new_abs_path), exist_ok=True)
                        
                        # 物理更名
                        shutil.move(old_path, new_abs_path)
                        
                        # 資料庫更新路徑
                        field_file.name = new_rel_path.replace('\\', '/')
                        instance.save()
                        
                        print(f"  [成功] {os.path.basename(old_path)} -> {new_filename}")
                        count += 1
                    except Exception as e:
                        print(f"  [錯誤] 重命名失敗 {old_path}: {e}")
                        errors += 1
                        
        except Exception as e:
            print(f"[嚴重錯誤] 無法讀取模型 {app_label}.{model_name}: {e}")

    print(f"\n--- 大掃除結束 ---")
    print(f"成功處理: {count} 個檔案")
    print(f"失敗數量: {errors}")

if __name__ == "__main__":
    cleanup_media()
