import os
from PIL import Image

def make_mascot_transparent():
    """
    將烏龜精靈圖的白色背景轉為透明
    """
    sprite_path = os.path.join('static', 'image', 'mascot', 'sprite.png')
    if not os.path.exists(sprite_path):
        print(f"找不到烏龜圖片: {sprite_path}")
        return

    print(f"正在處理烏龜去背: {sprite_path}")
    img = Image.open(sprite_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # 判斷是否為接近白色的像素 (R, G, B > 240)
        if item[0] > 245 and item[1] > 245 and item[2] > 245:
            new_data.append((255, 255, 255, 0)) # 設為完全透明
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(sprite_path, "PNG")
    print("烏龜去背完成！")

def optimize_media():
    """
    遍歷 media 目錄並壓縮過大的圖片
    """
    media_root = 'media'
    if not os.path.exists(media_root):
        return

    print("\n--- 開始全站圖片瘦身 ---")
    
    optimized_count = 0
    total_saved = 0

    for root, dirs, files in os.walk(media_root):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(root, file)
                
                # 取得壓縮前大小
                old_size = os.path.getsize(filepath)
                
                try:
                    with Image.open(filepath) as img:
                        # 只有大檔案 (> 500KB) 或解析度過高 (> 1920px) 才有處理價值
                        if old_size > 500 * 1024 or img.width > 1920:
                            # 1. 調整解析度至最大 1920px 寬 (維持比例)
                            if img.width > 1920:
                                ratio = 1920 / float(img.width)
                                new_height = int(float(img.height) * float(ratio))
                                img = img.resize((1920, new_height), Image.Resampling.LANCZOS)
                            
                            # 2. 轉為 RGB 存 JPG 或是優化 PNG
                            if file.lower().endswith('.png'):
                                img.save(filepath, "PNG", optimize=True)
                            else:
                                img.save(filepath, "JPEG", quality=85, optimize=True)
                            
                            new_size = os.path.getsize(filepath)
                            saved = (old_size - new_size) / 1024
                            total_saved += saved
                            optimized_count += 1
                            print(f"  [瘦身] {file}: {old_size/1024:.1f}KB -> {new_size/1024:.1f}KB (節省 {saved:.1f}KB)")
                except Exception as e:
                    print(f"  [跳過] 無法處理 {file}: {e}")

    print(f"\n--- 瘦身結束 ---")
    print(f"成功優化: {optimized_count} 個檔案")
    print(f"總共節省空間: {total_saved/1024:.2f} MB")

if __name__ == "__main__":
    make_mascot_transparent()
    optimize_media()
