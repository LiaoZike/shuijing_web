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

def update_notices_real():
    backup_file = os.path.join(project_path, 'scripts', 'merged_data_backup.json')
    if not os.path.exists(backup_file):
        print(f"Error: {backup_file} not found!")
        return

    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("--- Updating NOTICES to Real Data ---")
    
    # 1. Clear current notices
    print("Clearing current Notice table...")
    Notice.objects.all().delete()

    # 2. Extract New OSSR Data
    ossr = data.get('new_ossr_data', {}).get('notices', [])
    print(f"Adding {len(ossr)} real OSSR notices...")
    
    for item in ossr:
        if isinstance(item['publish_date'], str):
             item['publish_date'] = datetime.strptime(item['publish_date'], '%Y-%m-%d').date()
        Notice.objects.create(**item)

    print("--- Update Successful! ---")
    print(f"Total Notices now in DB: {Notice.objects.count()}")

if __name__ == "__main__":
    update_notices_real()
