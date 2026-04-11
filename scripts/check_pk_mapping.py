import json
import os

def read_backup(filename, encoding='utf-16le'):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding=encoding) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

print("--- ACTIVITY MAPPINGS ---")
activities = read_backup('scripts/backup_activities.json')
for item in activities:
    print(f"OriginalPK: {item['pk']} | Title: {item['fields']['title']}")

print("\n--- ACHIEVEMENT MAPPINGS ---")
achievements = read_backup('scripts/backup_achievements.json')
for item in achievements:
    print(f"OriginalPK: {item['pk']} | Title: {item['fields']['title']}")
