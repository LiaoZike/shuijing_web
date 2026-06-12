import os
import json
import shutil

history_path = r"C:\Users\a0978\AppData\Roaming\Code\User\History"
target_file_name = "mascot_chat.js"

found_entries = []

for root, dirs, files in os.walk(history_path):
    if "entries.json" in files:
        entries_file = os.path.join(root, "entries.json")
        try:
            with open(entries_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                resource = data.get("resource", "")
                if target_file_name in resource:
                    print(f"Found match in {root} for resource: {resource}")
                    entries = data.get("entries", [])
                    for entry in entries:
                        id_val = entry.get("id")
                        updated_at = entry.get("updatedAt")
                        # The actual file is named after the id in the same folder
                        history_file = os.path.join(root, id_val)
                        if os.path.exists(history_file):
                            size = os.path.getsize(history_file)
                            found_entries.append({
                                "file": history_file,
                                "updated_at": updated_at,
                                "size": size
                            })
        except Exception as e:
            pass

# Sort by updatedAt desc
found_entries.sort(key=lambda x: x["updated_at"], reverse=True)

for entry in found_entries:
    print(f"File: {entry['file']}, Updated: {entry['updated_at']}, Size: {entry['size']} bytes")
    # Read first line to see if it starts with (function ()
    try:
        with open(entry['file'], 'r', encoding='utf-8') as f:
            first_lines = [f.readline().strip() for _ in range(5)]
        print("  Preview:", first_lines)
    except Exception as e:
        print("  Error reading:", e)

if found_entries:
    # Copy the latest one with large size to a temp place
    latest_large = None
    for entry in found_entries:
        if entry["size"] > 20000: # The 1122 lines version is about 39184 bytes
            latest_large = entry
            break
    if latest_large:
        dest = r"d:\workspace\shuijing_web\static\js\core\mascot_chat.js"
        shutil.copy2(latest_large["file"], dest)
        print(f"\nSUCCESSFULLY RESTORED LATEST LARGE FILE ({latest_large['size']} bytes) to {dest}!")
    else:
        print("\nNo file found > 20000 bytes.")
else:
    print("\nNo entries found in VS Code history.")
