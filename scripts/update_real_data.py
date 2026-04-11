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

def update_data():
    print("Deleting/Deactivating old dummy data...")
    # Delete old dummy activities and notices
    Activity.objects.all().delete()
    Notice.objects.all().delete()
    UsrAchievement.objects.all().delete()
    
    print("Inserting real NFU USR data...")
    
    # 1. Activities
    Activity.objects.create(
        title="「籜」永續工藝 - 雲林水井村竹編文化體驗工作坊",
        title_2="在地長輩教導傳統技藝，連結青年學子與地方文化",
        tags="USR, 永續工藝, 在地文化",
        description="本活動透過水井村在地長輩的指導，帶領學生親手製作竹編工藝品，不僅傳承了瀕臨失傳的技藝，更促進了跨世代的對話與理解，實踐三生共好的計畫精神。",
        date=date(2024, 5, 15),
        location="雲林縣口湖鄉水井村社區活動中心",
        contact_name="USR 辦公室",
        contact_phone="05-6315000",
        is_active=True,
        is_featured=True
    )
    
    Activity.objects.create(
        title="智慧減碳節水：AIoT 智慧農業感測系統實作課程",
        title_2="學生實地安裝感測器，推動科技結合在地農業",
        tags="AIoT, 科技農業, USR",
        description="進入水井村農田，實地佈建土壤濕度感測器與自動化灌溉系統。透過即時數據分析，協助在地農民精準給水，減輕勞動負擔並達到節水減碳效益。",
        date=date(2024, 6, 20),
        location="水井村智慧農業示範場域",
        contact_name="王小明助理教授",
        contact_phone="05-6310000",
        is_active=True,
        is_featured=False
    )
    
    # 2. Notices
    Notice.objects.create(
        title="虎科大社會實踐卓越表現，榮獲 2024 USR 大學社會責任績優計畫獎",
        category="important",
        content="國立虎尾科技大學推動「水井村三生一體計畫」在全國大學社會責任評鑑中表現優異，榮獲年度績優計畫獎項，肯定師生深入地方、解決實務問題的努力。",
        publish_date=date(2024, 4, 10),
        is_active=True,
        is_priority=True
    )
    
    Notice.objects.create(
        title="【成果展訊】校園永續影響力成果展 - 走進水井村的日常",
        category="event",
        content="即將在校園內舉辦盛大的 USR 成果巡迴展，屆時將展示水井村計畫之 AIoT 技術應用、竹編工藝作品及在地漁產開發成果，歡迎全校師生共襄盛舉。",
        publish_date=date(2024, 5, 1),
        is_active=True
    )
    
    Notice.objects.create(
        title="113年度永續農業推廣座談：共創綠色轉型新契機",
        category="general",
        content="與在地社區共同舉辦的永續農業座談會圓滿成功，會中邀請專家分享綠色資材應用與減碳農業經驗，為水井村的轉型提供專業見解。",
        publish_date=date(2024, 3, 15),
        is_active=True
    )
    
    # 3. USR Achievements
    UsrAchievement.objects.create(
        date=date(2024, 3, 25),
        category="社會實踐",
        title="水井村在地對話 - 師生共創智慧農業新篇章",
        description="虎科大師生與水井村民共同研發適合沿海漁村的智慧節水方案，透過現場工作坊與農民直接溝通需求，大幅減少了農事運維成本。",
        is_active=True
    )
    
    UsrAchievement.objects.create(
        date=date(2024, 2, 10),
        category="AIoT 課程",
        title="數位導覽地圖上線：讓更多人看見水井村的美",
        description="USR 計畫團隊成功開發數位化導覽地圖，整合在地故事與 AR 技術，讓遊客透過手機就能深入了解水井村的起源與特色。",
        is_active=True
    )

    print("Data update completed successfully!")

if __name__ == "__main__":
    update_data()
