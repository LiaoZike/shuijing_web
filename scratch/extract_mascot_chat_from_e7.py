import os
import shutil

search_dir = r"C:\Users\a0978\.gemini\antigravity\brain\e7ff2b3a-1e35-42df-967e-9864a38567eb"
target_file = "mascot_chat.js"

found = []
for root, dirs, files in os.walk(search_dir):
    if target_file in files:
        path = os.path.join(root, target_file)
        size = os.path.getsize(path)
        print(f"FOUND FILE: {path} | Size: {size} bytes")
        found.append((path, size))

if found:
    found.sort(key=lambda x: x[1], reverse=True)
    best_path = found[0][0]
    dest = r"d:\workspace\shuijing_web\static\js\core\mascot_chat.js"
    shutil.copy2(best_path, dest)
    print(f"SUCCESSFULLY RESTORED FILE ({found[0][1]} bytes) to {dest}!")
else:
    print("No mascot_chat.js found in e7ff folder.")
