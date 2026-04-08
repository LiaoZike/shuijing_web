import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuijing.settings') # Replace 'shuijing.settings' with actual
django.setup()

from core.models import AiotProject, UsrAchievement, UsrVideo, UsrTeamMember

def run():
    print("Clearing old data...")
    AiotProject.objects.all().delete()
    UsrAchievement.objects.all().delete()
    UsrVideo.objects.all().delete()
    UsrTeamMember.objects.all().delete()

    print("Adding AiotProjects...")
    aiot_data = [
        {
            "icon": "🐟",
            "title": "水產智慧監控系統",
            "tags": "智慧養殖,水質監測",
            "description": "水井村以養殖漁業為重，我們導入 AIoT 感測器即時監控魚塭水質，包含溫度、pH值、溶氧量等關鍵指標，讓漁民隨時掌握養殖狀況，提升魚貨存活率與品質，實現在地產業升級。",
            "link_url": "",
            "image": "usr/aiot_farming.png",
            "order": 1
        },
        {
            "icon": "💧",
            "title": "水井村水資源節水監控",
            "tags": "節水技術,循環利用",
            "description": "因應氣候變遷與地下水資源枯竭，建立水資源循環監控系統，透過智慧節水技術與生物淨水技術，減少水資源浪費，實現農業與養殖用水的永續循環再利用。",
            "link_url": "",
            "order": 2
        },
        {
            "icon": "🌾",
            "title": "農田環境智慧監測",
            "tags": "智慧農業,低碳生產",
            "description": "結合土壤溫濕度感測器與環境微氣候監測，提供農戶即時分析與精準的種植建議，減少農藥與肥料的過度使用，邁向低碳永續農業生產模式。",
            "link_url": "",
            "order": 3
        },
        {
            "icon": "🚀",
            "title": "在地農產品數位行銷",
            "tags": "智慧行銷,數位轉型",
            "description": "結合網路商城與社群媒體平台，協助水井村建立「尚虎雲」數位產銷品牌。不僅打破傳統中盤商的限制，也透過故事行銷讓更多人認識水井村的農漁產。",
            "link_url": "",
            "order": 4
        },
        {
            "icon": "🌸",
            "title": "水井三寶 AR 互動體驗",
            "tags": "樹藝AI,文化科技",
            "description": "以水井村專屬特產的「水井三寶」— 烏龜、白馬、姻緣花 為主題，結合生成式 AI 與 AR 技術。掃描實體圖卡即可看見在地傳說的動態演繹，將故事生動傳承。",
            "link_url": "/guide/",
            "order": 5
        },
        {
            "icon": "🤖",
            "title": "OTTO 與 Matrix 偏鄉機器人",
            "tags": "STEAM教育,創客",
            "description": "師生親自帶領水井村學童動手組裝 OTTO 機器人與操作 Matrix 系統。除了學習基本程式設計外，也點燃偏鄉孩子對科技的熱情，有效縮短城鄉數位落差。",
            "link_url": "",
            "image": "usr/aiot_robot.png",
            "order": 6
        }
    ]
    for d in aiot_data:
        AiotProject.objects.create(**d)

    print("Adding Achievements...")
    achi_data = [
        {
            "date": date(2025, 3, 10),
            "category": "社會實踐",
            "title": "三寶奇緣——水井村 × 他里霧文化尋訪",
            "description": "電機資訊學院於雲林縣斗南他里霧文化園區舉辦實體活動，水井村居民與師生親手製作「姻緣花」玉米籜工藝，結合 LED 燈光設計，融合傳統工藝與現代創意科技，完美詮釋跨世代合作的感動。"
        },
        {
            "date": date(2025, 5, 22),
            "category": "AIoT 課程",
            "title": "智慧科技滿載，AIoT 課程正式進駐水井村",
            "image": "usr/usr_course.png",
            "description": "學院教師與滿腔熱血的大學生，攜手將智慧養殖監控技術推廣至水井村漁塭，手把手指導當地漁民如何透過 App 讀取感測器數值，開啟漁業科技化的第一哩路。"
        },
        {
            "date": date(2025, 10, 15),
            "category": "樹藝 AI 展出",
            "title": "水井三寶 AI 藝術創作展",
            "description": "尚虎雲團隊以「水井三寶」為創作核心的 AI 藝術作品，於竹山鎮小鎮文創的協助下順利在台西客運站展出，為傳統故事披上科技的新衣，吸引大量旅客駐足欣賞。"
        },
        {
            "date": date(2026, 1, 8),
            "category": "STEAM 教育",
            "title": "偏鄉亮點：機器人工作坊熱烈展開",
            "image": "usr/aiot_robot.png",
            "description": "針對口湖鄉與水井村孩童所設計的 OTTO 與 Matrix 機器人寒假營隊。由虎科大學生擔任隊輔，孩子們從看見機器人動起來的驚呼中，看見了翻轉偏鄉科技教育的微光。"
        }
    ]
    for d in achi_data:
        UsrAchievement.objects.create(**d)


    print("Adding Videos...")
    video_data = [
        {
            "date": date(2026, 1, 15),
            "title": "114年深耕計畫目標二成果影片",
            "link_url": "https://ossr.nfu.edu.tw/zh_tw/practices/getVideoList"
        },
        {
            "date": date(2026, 2, 20),
            "title": "2026 樹藝森林精靈機器人工作坊",
            "link_url": "https://ossr.nfu.edu.tw/zh_tw/practices/getVideoList"
        },
        {
            "date": date(2025, 10, 10),
            "title": "第四屆亞太永續博覽會 USR EXPO",
            "link_url": "https://ossr.nfu.edu.tw/zh_tw/practices/getVideoList"
        },
        {
            "date": date(2025, 10, 5),
            "title": "尚虎雲在竹山小鎮社會實踐",
            "link_url": "https://ossr.nfu.edu.tw/zh_tw/practices/getVideoList"
        }
    ]
    for d in video_data:
        UsrVideo.objects.create(**d)

    print("Adding Team Members...")
    team_data = [
        {"name": "許永和 博士", "role": "計畫主持人", "department": "資訊工程系特聘教授\n電機資訊學院院長", "order": 1},
        {"name": "林正敏 教授", "role": "共同主持人", "department": "電機資訊學院教授\n永續發展暨社會責任處執行長", "order": 2},
        {"name": "張耀南 教授", "role": "共同主持人", "department": "生物科技系教授", "order": 3},
        {"name": "莊文河 副教授", "role": "協同主持人", "department": "資訊工程系", "order": 4},
        {"name": "郭永明 助理教授", "role": "協同主持人", "department": "電子工程系", "order": 5},
        {"name": "吳添全 助理教授", "role": "協同主持人", "department": "電子工程系", "order": 6},
        {"name": "陳鳳雀 助理教授", "role": "協同主持人", "department": "通識教育中心", "order": 7},
        {"name": "陳靜美", "role": "計畫聯絡人", "department": "電資學院 研究副管理師", "order": 8},
    ]
    for d in team_data:
        UsrTeamMember.objects.create(**d)
    
    print("Data Initialization Complete!")

if __name__ == '__main__':
    run()
