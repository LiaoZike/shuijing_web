import os
import django
import json
import sys
from datetime import datetime

# Setup Django environment
project_path = os.getcwd()
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Notice

def update_extensive_notices():
    print("--- Extensive Notice Update ---")
    
    # 1. Clear current notices
    Notice.objects.all().delete()
    print("Cleared Notice table.")

    # 2. Hardcoded Extensive News Data from Research
    news_items = [
        {
            "title": "虎科大 × 雲林縣府攜手打造「永續行動大學」圓滿成功",
            "category": "general",
            "publish_date": "2025-12-24",
            "content": "虎科大與雲林縣政府合作，展示永續行動成果，圓滿達成合作目標，共同推動地方永續發展。"
        },
        {
            "title": "114年「永續行動大學 - 綠領人才 暨 ECOCO 系統啟動」聯合博覽會",
            "category": "event",
            "publish_date": "2025-12-17",
            "content": "本活動結合綠領人才培育與永續實踐，舉辦聯合博覽會並正式啟動 ECOCO 智慧循環經濟系統。"
        },
        {
            "title": "社會實踐課程辦理「肪片龜文化工坊」探尋在地民俗情懷",
            "category": "general",
            "publish_date": "2025-10-21",
            "content": "社會實踐課程帶領學生體驗在地傳統文化，透過揉製肪片龜，深入了解地方民俗與歷史情感。"
        },
        {
            "title": "虎尾科技大學與雲林縣政府攜手舉辦「雲林縣 SDGs 永續發展論壇」",
            "category": "important",
            "publish_date": "2025-09-15",
            "content": "藉由論壇交流，推動地方政府與大學在永續發展目標（SDGs）上的深度合作與實踐。"
        },
        {
            "title": "狂賀！！國立虎尾科技大學 榮獲 2026《遠見》USR 獎獎項肯定",
            "category": "important",
            "publish_date": "2026-04-10",
            "content": "虎科大在 2026 年《遠見雜誌》大學社會責任（USR）獎中榮獲肯定，展現長期深耕地方的卓越影響力。",
            "is_priority": True
        },
        {
            "title": "從零到戰鬥王：虎科大攜手鴻海基金會培育偏鄉科技種子",
            "category": "event",
            "publish_date": "2026-04-08",
            "content": "虎科大與鴻海基金會合作，深入偏鄉進行科技教育，培植在地青少年的數位技能與未來競爭力。"
        },
        {
            "title": "【天下雜誌 Podcast】虎尾溪畔的鋼鐵柔情——守護農業大縣未來",
            "category": "general",
            "publish_date": "2026-03-20",
            "content": "分享虎科大如何發揮工科專業優勢，積極守護雲林農業大縣並引領產業綠色轉型。"
        },
        {
            "title": "賀！國立虎尾科技大學榮獲 2025 台灣永續大學獎雙項肯定",
            "category": "important",
            "publish_date": "2025-11-26",
            "content": "虎科大榮獲「台灣永續績優大學獎」及「永續報告書獎銅級」，在永續治理與社會共融方面獲得高度評價。"
        }
    ]

    for item in news_items:
        if isinstance(item['publish_date'], str):
             item['publish_date'] = datetime.strptime(item['publish_date'], '%Y-%m-%d').date()
        Notice.objects.create(**item)

    print(f"Update Successful! Total Notices: {Notice.objects.count()}")

if __name__ == "__main__":
    update_extensive_notices()
