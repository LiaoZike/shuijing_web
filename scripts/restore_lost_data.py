import os
import django
from datetime import date
from django.utils import timezone

# Setup Django environment
import sys
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Activity, Notice, UsrAchievement

def restore_data():
    print("Restoring lost database records...")
    
    # 1. Restore Activities
    activities = [
        {
            "title": "水井風雲客棧 × OTTO 機器人",
            "title_2": "智慧學院系列工作坊",
            "tags": "智慧學院, USR, 機器人",
            "description": "帶領學員認識 OTTO 平衡機器人，透過 3D 列印與簡單程式設計，讓科技走入社區生活。",
            "date": date(2024, 4, 9),
            "time": "8:10 - 11:00",
            "location": "風雲客棧 二樓教室",
            "contact_name": "USR 團隊",
            "contact_phone": "05-6315000",
            "cover_image": "activities/activity_10_cover_image.jpg",
            "is_active": True,
            "is_featured": True
        },
        {
            "title": "MATRIX 機器人挑戰營—從零到戰鬥王",
            "title_2": "虎科 A0101 跨學科專案內容",
            "tags": "智慧學院&虎科AIA0201, 競賽, 科技",
            "description": "高階機器人組裝與競賽策略，針對具備基礎的學員提供進階挑戰。",
            "date": date(2024, 4, 7),
            "time": "8:10 - 11:00",
            "location": "風雲客棧 戶外廣場",
            "contact_name": "USR 辦公室",
            "contact_phone": "05-6315000",
            "cover_image": "activities/activity_11_cover_image.png",
            "is_active": True,
            "is_featured": True
        },
        {
            "title": "蒜皮永生花—不蒜花手作體驗",
            "title_2": "虎尾科技大學實踐成果展示",
            "tags": "虎尾科技大學, 永續工藝, 體驗",
            "description": "將原本廢棄的蒜皮轉化為永續工藝品，創造在地文創新價值。",
            "date": date(2024, 4, 19),
            "location": "水井村社區推廣中心",
            "contact_name": "USR 計畫主持人",
            "contact_phone": "05-6315000",
            "cover_image": "activities/activity_12_cover_image.jpg",
            "is_active": True,
            "is_featured": False
        },
        {
            "title": "玉米梗再生工藝—童玩編織",
            "title_2": "官邸兒童館合作課程",
            "tags": "官邸兒童館, 親子, 傳承",
            "description": "古法技藝傳承，利用農業廢棄物創作童玩指標。",
            "date": date(2024, 4, 4),
            "time": "09:00 - 12:00",
            "location": "官邸兒童館",
            "contact_name": "USR 辦公室",
            "contact_phone": "05-6315000",
            "cover_image": "activities/activity_13_cover_image.jpg",
            "is_active": True,
            "is_featured": False,
            "end_date": date(2024, 4, 4)
        }
    ]
    
    for act in activities:
        Activity.objects.get_or_create(title=act["title"], defaults=act)

    # 2. Restore Notices (1-6)
    notices = [
        {"title": "【活動】水井村週末導覽行程 (1)", "category": "event", "publish_date": date(2024, 4, 11), "content": "歡迎參加週末導覽。"},
        {"title": "【公告】社區發展協會會議記錄 (2)", "category": "event", "publish_date": date(2024, 4, 9), "content": "會議摘要紀錄。"},
        {"title": "【快訊】USR計畫校外參訪摘要 (3)", "category": "important", "publish_date": date(2024, 4, 9), "content": "參訪紀實。"},
        {"title": "【重要】網站系統維護通知 (4)", "category": "important", "publish_date": date(2024, 4, 8), "content": "維護公告。"},
        {"title": "【故事】水井三寶的神祕傳說 (5)", "category": "important", "publish_date": date(2024, 4, 7), "content": "在地故事集。"},
        {"title": "【花訊】姻緣花盛開期預測 (6)", "category": "general", "publish_date": date(2024, 4, 5), "content": "盛開預報。"},
    ]
    
    for n in notices:
        Notice.objects.get_or_create(title=n["title"], defaults={**n, "is_active": True})

    # 3. Restore USR Achievements
    achievements = [
        {"date": date(2024, 1, 15), "category": "社會實踐", "title": "「水井村智慧減碳節水三生一體社會實踐計畫」啟動", "description": "正式開啟跨領域合作。"},
        {"date": date(2024, 2, 1), "category": "AIoT 課程", "title": "AIoT 導入魚塭水質監測系統實地測試", "description": "提升養殖精準度。"},
        {"date": date(2024, 2, 20), "category": "服務學習", "title": "Matrix 機器人偏鄉小學工作坊", "description": "科技教育向下扎根。"}
    ]
    
    for ach in achievements:
        UsrAchievement.objects.get_or_create(title=ach["title"], defaults={**ach, "is_active": True})

    print("Restoration completed successfully!")

if __name__ == "__main__":
    restore_data()
