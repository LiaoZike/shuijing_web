import json
import os

with open('scripts/merged_data_backup.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- ACTIVITY PK MAPPINGS ---")
for item in data['restored_activities']:
    print(f"ID:{item['pk']} | Title:{item['title'] if 'title' in item else item['fields']['title']}")

print("\n--- ACHIEVEMENT PK MAPPINGS ---")
for item in data['restored_achievements']:
    print(f"ID:{item['pk']} | Title:{item['title'] if 'title' in item else item['fields']['title']}")

print("\n--- MEDIA FILES SCAN ---")
for root, dirs, files in os.walk('media'):
    for file in files:
        if 'activity' in file or 'usrachievement' in file:
            print(f"File found: {os.path.join(root, file)}")
