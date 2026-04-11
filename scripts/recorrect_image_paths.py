import os
import django
import json
import sys

# Setup Django environment
project_path = os.getcwd()
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings')
django.setup()

from core.models import Activity, UsrAchievement

def recorrect_paths():
    backup_file = os.path.join(project_path, 'scripts', 'merged_data_backup.json')
    if not os.path.exists(backup_file):
        print(f"Error: {backup_file} not found!")
        return

    with open(backup_file, 'r', encoding='utf-8') as f:
        backup = json.load(f)

    # 1. Activities Mapping
    act_map = {} # Title -> Original ID
    for item in backup['restored_activities']:
        title = item['fields']['title'].strip()
        act_map[title] = item['pk']

    # 2. Achievements Mapping
    ach_map = {} # Title -> Original ID
    for item in backup['restored_achievements']:
        title = item['fields']['title'].strip()
        ach_map[title] = item['pk']

    print("--- Correcting Activity Paths ---")
    activities = Activity.objects.all()
    for act in activities:
        title = act.title.strip()
        if title in act_map:
            old_id = act_map[title]
            # Try to find the file with various extensions
            found = False
            for ext in ['.jpg', '.png', '.jpeg', '.webp']:
                rel_path = f"activities/activity_{old_id}_cover_image{ext}"
                full_path = os.path.join(project_path, 'media', rel_path)
                if os.path.exists(full_path):
                    act.cover_image = rel_path
                    act.save()
                    print(f"MATCH: {title} -> {rel_path}")
                    found = True
                    break
            if not found:
                print(f"MISSING FILE: No physical file found for {title} (ID:{old_id})")
        else:
            print(f"SKIP: No original mapping for {title} (Might be new OSSR item)")

    print("\n--- Correcting UsrAchievement Paths ---")
    achievements = UsrAchievement.objects.all()
    for ach in achievements:
         title = ach.title.strip()
         if title in ach_map:
             old_id = ach_map[title]
             found = False
             for ext in ['.jpg', '.png', '.jpeg', '.webp']:
                 rel_path = f"usr/achievements/usrachievement_{old_id}_image{ext}"
                 full_path = os.path.join(project_path, 'media', rel_path)
                 if os.path.exists(full_path):
                     ach.image = rel_path
                     ach.save()
                     print(f"MATCH: {title} -> {rel_path}")
                     found = True
                     break
             if not found:
                 print(f"MISSING FILE: No physical file found for {title} (ID:{old_id})")
         else:
             print(f"SKIP: No original mapping for {title}")

    print("\n--- Correction process finished! ---")

if __name__ == "__main__":
    recorrect_paths()
