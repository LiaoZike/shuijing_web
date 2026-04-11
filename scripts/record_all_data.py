import os
import django
import json
import sys
from datetime import date

# Setup Django environment
project_path = os.getcwd()
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Activity, Notice, UsrAchievement
from django.core import serializers

def record_data():
    print("Record Start: Capturing current state (Old Git DB)...")
    
    # Capture current data (the ones user wants to keep)
    activities_json = serializers.serialize('json', Activity.objects.all())
    notices_json = serializers.serialize('json', Notice.objects.all())
    achievements_json = serializers.serialize('json', UsrAchievement.objects.all())
    
    backup_data = {
        "restored_activities": json.loads(activities_json),
        "restored_notices": json.loads(notices_json),
        "restored_achievements": json.loads(achievements_json),
        "new_ossr_data": {
            "activities": [
                {
                    "title": "「籜」永續工藝 - 雲林水井村竹編文化體驗工作坊",
                    "title_2": "在地長輩教導傳統技藝，連結青年學子與地方文化",
                    "tags": "USR, 永續工藝, 在地文化",
                    "description": "本活動透過水井村在地長輩的指導，帶領學生親手製作竹編工藝品...",
                    "date": "2024-05-15",
                    "location": "雲林縣口湖鄉水井村社區活動中心",
                    "contact_name": "USR 辦公室",
                    "contact_phone": "05-6315000",
                    "is_active": True,
                    "is_featured": True
                },
                {
                    "title": "智慧減碳節水：AIoT 智慧農業感測系統實作課程",
                    "title_2": "學生實地安裝感測器，推動科技結合在地農業",
                    "tags": "AIoT, 科技農業, USR",
                    "description": "進入水井村農田，實地佈建土壤濕度感測器與自動化灌溉系統...",
                    "date": "2024-06-20",
                    "location": "水井村智慧農業示範場域",
                    "contact_name": "王小明助理教授",
                    "contact_phone": "05-6310000",
                    "is_active": True,
                    "is_featured": False
                }
            ],
            "notices": [
                {
                    "title": "虎科大社會實踐卓越表現，榮獲 2024 USR 大學社會責任績優計畫獎",
                    "category": "important",
                    "content": "國立虎尾科技大學推動「水井村三生一體計畫」成果斐然...",
                    "publish_date": "2024-04-10",
                    "is_active": True,
                    "is_priority": True
                },
                {
                    "title": "【成果展訊】校園永續影響力成果展 - 走進水井村的日常",
                    "category": "event",
                    "content": "即將在校園內舉辦盛大的 USR 成果巡迴展...",
                    "publish_date": "2024-05-01",
                    "is_active": True
                },
                {
                    "title": "113年度永續農業推廣座談：共創綠色轉型新契機",
                    "category": "general",
                    "content": "與在地社區共同舉辦的永續農業座談會圓滿成功...",
                    "publish_date": "2024-03-15",
                    "is_active": True
                }
            ],
            "achievements": [
                {
                    "date": "2024-03-25",
                    "category": "社會實踐",
                    "title": "水井村在地對話 - 師生共創智慧農業新篇章",
                    "description": "虎科大師生與水井村民共同研發...",
                    "is_active": True
                },
                {
                    "date": "2024-02-10",
                    "category": "AIoT 課程",
                    "title": "數位導覽地圖上線：讓更多人看見水井村的美",
                    "description": "USR 計畫團隊成功開發數位化導覽地圖...",
                    "is_active": True
                }
            ]
        }
    }
    
    backup_file = os.path.join(project_path, 'scripts', 'merged_data_backup.json')
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
    print(f"Success: Recorded {len(backup_data['restored_activities'])} activities, "
          f"{len(backup_data['restored_notices'])} notices, and "
          f"{len(backup_data['restored_achievements'])} achievements from DB.")
    print("Also included the 5 new OSSR items.")

if __name__ == "__main__":
    record_data()
