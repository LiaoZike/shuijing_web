import os

brain_dir = r"C:\Users\a0978\.gemini\antigravity\brain"
search_term = "initChart"

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if search_term in content:
                    print(f"FOUND: {file_path} (Size: {os.path.getsize(file_path)} bytes)")
                    # Print preview
                    print(content[:300])
                    print("-" * 50)
        except Exception as e:
            pass
print("Search complete.")
