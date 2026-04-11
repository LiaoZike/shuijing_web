import os
import sys
import django
import random
from django.utils import timezone
from datetime import timedelta

# Set project root and add to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Notice

def create_notices():
    cats = ['important', 'general', 'event']
    titles = [
        '【活動】水井村週末導覽行程',
        '【公告】社區發展協會會議記錄',
        '【快訊】USR計畫校外參訪摘要',
        '【重要】網站系統維護通知',
        '【故事】水井三寶的神祕傳說',
        '【花訊】姻緣花盛開期預測',
        '【USR】青銀共學工作坊花絮',
        '【公告】垃圾清運時間調整',
        '【節慶】水井村年度祭典預告',
        '【招募】導覽志工招募中'
    ]
    content_sample = '這是模擬公告的詳細內容。水井村是一個充滿故事的地方，我們致力於保存地方文化並推動數位導覽服務。感謝大家的支持與參與！'
    
    for i in range(10):
        Notice.objects.create(
            title=f"{titles[i % len(titles)]} ({i+1})",
            content=content_sample,
            category=random.choice(cats),
            publish_date=timezone.now() - timedelta(days=i, hours=random.randint(1, 23)),
            is_priority=random.choice([True, False]),
            is_active=True
        )
    print('Successfully created 10 simulated notices.')

if __name__ == '__main__':
    create_notices()
