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

from core.models import Activity, UsrAchievement

def restore_to_new_db():
    backup_file = os.path.join(project_path, 'scripts', 'merged_data_backup.json')
    if not os.path.exists(backup_file):
        print(f"Error: Backup file {backup_file} not found!")
        return

    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("--- Restoring to NEW DB ---")
    
    # 1. Clear current tables
    print("Clearing Activity and UsrAchievement tables...")
    Activity.objects.all().delete()
    UsrAchievement.objects.all().delete()

    # 2. Restore Restored Activities (from Old Git DB)
    print(f"Restoring {len(data['restored_activities'])} activities from backup...")
    for item in data['restored_activities']:
        fields = item['fields']
        # Convert date strings to date objects if necessary
        Activity.objects.create(**fields)

    # 3. Restore Restored Achievements (from Old Git DB)
    print(f"Restoring {len(data['restored_achievements'])} achievements from backup...")
    for item in data['restored_achievements']:
        fields = item['fields']
        UsrAchievement.objects.create(**fields)

    # 4. Insert New OSSR Data (Real News)
    print("Adding New OSSR Real Data...")
    ossr = data['new_ossr_data']
    
    for act in ossr['activities']:
        # Ensure date is date object
        if isinstance(act['date'], str):
            act['date'] = datetime.strptime(act['date'], '%Y-%m-%d').date()
        Activity.objects.get_or_create(title=act['title'], defaults=act)

    for ach in ossr['achievements']:
        if isinstance(ach['date'], str):
            ach['date'] = datetime.strptime(ach['date'], '%Y-%m-%d').date()
        UsrAchievement.objects.get_or_create(title=ach['title'], defaults=ach)

    print("--- Restoration Successful! ---")
    print(f"Total Activities: {Activity.objects.count()}")
    print(f"Total Achievements: {UsrAchievement.objects.count()}")

if __name__ == "__main__":
    restore_to_new_db()
