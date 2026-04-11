import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import UsrVideo

videos = [
    {
        "title": "深耕計畫目標二｜2026 兒童館無人機足球",
        "url": "https://www.youtube.com/watch?v=BNSiAJfvotk"
    },
    {
        "title": "深耕計畫目標二｜2026 \"不要科學怪人\"-樹藝森林精靈機器人工作坊",
        "url": "https://www.youtube.com/watch?v=n_6NbJkXCvc"
    },
    {
        "title": "深耕計畫目標二｜2026尚虎雲Q Robot AI 教學",
        "url": "https://www.youtube.com/watch?v=QnD0DEtjDlU"
    },
    {
        "title": "深耕計畫目標二｜2026 Q-ROBOT AI X白陽光祥童軍團",
        "url": "https://www.youtube.com/watch?v=gopi1_dntwo"
    },
    {
        "title": "深耕計畫目標二｜尚虎雲在竹山小鎮社會實踐",
        "url": "https://www.youtube.com/watch?v=nvyTHvSP9E4"
    },
    {
        "title": "114年 USR EXPO 水井村智慧減碳節水三生一體",
        "url": "https://www.youtube.com/watch?v=WktqrxogavQ"
    },
    {
        "title": "113高教深耕計畫目標二 樹藝AI林正敏和李永謨聯展",
        "url": "https://www.youtube.com/watch?v=Zz4IQo8R1wI"
    },
    {
        "title": "113年USR Hub：雲林沿海偏鄉的社區共好實踐計畫－以水井村三生共好為例",
        "url": "https://www.youtube.com/watch?v=86o-pZddrjM"
    },
    {
        "title": "113高教深耕計畫目標二 樹藝與micro：bit魔幻交織計畫-紀錄片",
        "url": "https://www.youtube.com/watch?v=tr7Rfgt6lpk"
    }
]

today = datetime.date.today()

count = 0
for v in videos:
    obj, created = UsrVideo.objects.get_or_create(
        link_url=v["url"],
        defaults={
            "title": v["title"],
            "date": today,
            "is_active": True
        }
    )
    if created:
        count += 1
        print(f"Created: {v['title']}")
    else:
        print(f"Already exists: {v['title']}")

print(f"Successfully imported {count} videos.")
