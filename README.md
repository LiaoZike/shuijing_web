# 水井村網站（Shuijing Web）

水井村網站是一個以 **Django** 開發的在地資訊與智慧養殖整合平台，結合村落資訊、活動報名、USR 成果展示、數位導覽、AI 導覽助手，以及魚池水質監控與感測器資料上傳功能。

本 README 同時作為專案介紹、基本安裝文件、水質 Dashboard 使用說明與感測器 API 文件。

---

## 目錄

- [主要功能](#主要功能)
- [專案結構](#專案結構)
- [安裝與執行](#安裝與執行)
- [第三方服務設定](#第三方服務設定)
- [水質監控系統](#水質監控系統)
- [水質 Dashboard](#水質-dashboard)
- [感測器資料上傳 API](#感測器資料上傳-api)
- [Python 上傳範例](#python-上傳範例)
- [ESP32 上傳範例](#esp32-上傳範例)
- [主要網址](#主要網址)
- [部署說明](#部署說明)

---

# 主要功能

## 村落資訊與內容管理

- 首頁輪播
- 最新公告
- 水井村介紹與在地故事
- 在地商家與相關連結
- 聯絡表單
- 全站內容搜尋

## 活動與報名

- 活動列表與活動詳情
- 活動日期、地點、名額與報名期限管理
- 使用者活動報名
- 候補機制
- 個人報名紀錄
- 後台報名資料管理

## USR 與成果展示

- AIoT 專案展示
- 師生實踐成果
- 成果圖片與影音
- YouTube / iframe 影音嵌入

## 使用者登入

網站透過 `django-allauth` 整合 Google OAuth，可使用 Google 帳號登入網站。

## 數位導覽與 AR

- 導覽景點與分類
- 景點知識內容
- AR 素材管理
- AR 導覽頁面
- 在地養殖 AR 體驗
- AR 體驗排行榜

## AI 導覽助手

網站整合 OpenAI API，可依網站資料協助查詢：

- 活動與公告
- USR / AIoT 成果
- 相關連結
- 使用者可查看的魚池
- 最新與歷史水質
- 感測器狀態
- 水車狀態
- 水質警報與穩定度

AI 回覆亦可搭配前端 Dashboard / Chart 呈現資料。

## 水質監控

水質模組提供：

- 魚池建立與管理
- 魚池平面配置
- 多感測器管理與位置配置
- 每顆感測器專屬上傳 Token
- 水溫、pH、溶氧、氨氮、亞硝酸鹽與鹽度紀錄
- 自訂水質警戒值
- 水質歷史紀錄與 CSV 匯出
- 水質穩定度計算
- 感測器異常警報
- Discord 警報通知
- 魚池權限分享
- 水車設備與自動運作規則
- 模擬感測資料

---

# 專案結構

```text
shuijing_web/
├── accounts/       # 登入、Google OAuth、使用者頁面
├── chat/           # AI 導覽助手
├── core/           # 首頁、活動、公告、USR、聯絡等功能
├── guide/          # 數位導覽與 AR
├── water/          # 魚池、水質、感測器、API、水車
├── shuijing/       # Django 專案設定
├── templates/      # HTML Templates
├── static/         # CSS / JavaScript / 圖片
├── media/          # 上傳媒體檔案
├── manage.py
└── requirements.txt
```

---

# 安裝與執行

以下流程為目前專案的基本開發環境安裝方式。

## 1. Python 環境

目前專案使用 Django 6，建議使用：

```text
Python 3.12+
```

## 2. Clone Repository

```bash
git clone https://github.com/LiaoZike/shuijing_web.git
cd shuijing_web
```

## 3. 建立 Virtual Environment

### Windows PowerShell

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

若系統只有一個 Python 版本，也可以：

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. 安裝 Python 套件

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. 建立環境設定檔

專案提供：

```text
.env_example
```

複製為 `.env`。

### Windows PowerShell

```powershell
Copy-Item .env_example .env
```

### Linux / macOS

```bash
cp .env_example .env
```

可依實際使用功能設定：

```env
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CONTACT_EMAIL=

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

NGROK_TOKEN=

WEATHER_LOCATION_NAME=
WEATHER_LATITUDE=
WEATHER_LONGITUDE=
```

未使用的第三方服務欄位可保持空白。

## 6. 初始化資料庫

專案預設使用 SQLite。

執行：

```bash
python manage.py migrate
```

若專案目錄已包含既有的 `db.sqlite3`，此指令會將資料庫 Schema 更新至目前 Migration 狀態。

若要建立全新的資料庫，可使用新的 SQLite Database 後重新執行：

```bash
python manage.py migrate
```

## 7. 建立管理員帳號（選用）

```bash
python manage.py createsuperuser
```

管理後台：

```text
http://127.0.0.1:8000/adminx/
```

## 8. 啟動網站

```bash
python manage.py runserver
```

預設網址：

```text
http://127.0.0.1:8000/
```

若需要讓同一區域網路中的裝置連線：

```bash
python manage.py runserver 0.0.0.0:8000
```

再使用 Server 所在電腦的區網 IP，例如：

```text
http://192.168.1.100:8000/
```

---

# 第三方服務設定

以下服務依使用需求設定，不影響 Django 基本網站啟動。

## Google OAuth

Google 登入需要建立 Google OAuth 應用，並設定：

- Google OAuth Client ID
- Google OAuth Client Secret
- Authorized Redirect URI
- `django-allauth` Social Application

主要 Callback Path：

```text
/accounts/google/login/callback/
```

## OpenAI

AI 導覽助手使用：

```env
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
OPENAI_MODEL=gpt-4o-mini
```

## Gmail SMTP

聯絡表單寄信功能可設定：

```env
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=YOUR_APP_PASSWORD
CONTACT_EMAIL=receiver@example.com
```

若使用 Gmail，建議使用 Google App Password。

## Discord

水質系統可使用 Discord Webhook 發送水質異常通知，Webhook 可依魚池設定配置。

## 語音辨識

水質系統可連接外部 ASR 服務，供語音相關功能使用。實際服務網址可依部署環境設定。

---

# 水質監控系統

水質系統的主要資料關係可簡化為：

```text
使用者
  │
  ├── 管理 / 查看
  ▼
魚池 Pond
  │
  ├── 感測器 PondSensor
  │      │
  │      └── 水質讀值 SensorReading
  │
  ├── 水質警戒值 WaterThreshold
  │
  └── 水車 PondAerator
```

每顆感測器可保存：

- 感測器名稱
- 感測器類型
- X / Y 地圖位置
- 啟用狀態
- 專屬 `secret_token`

目前感測器類型包含：

```text
multi   多合一感測器
do      溶氧感測器
ph      pH 感測器
chem    氨氮 / 亞硝酸鹽感測器
temp    溫度感測器
```

---

# 水質 Dashboard

水質首頁：

```text
/water/
```

魚池詳細頁：

```text
/water/<pond_id>/
```

魚池管理頁：

```text
/water/<pond_id>/manage/
```

## 建立魚池

魚池可設定：

- 名稱
- 養殖物種
- 說明
- 地圖圖片
- 進水口位置
- 排水口位置
- 水質穩定度權重
- Discord Webhook
- 分享權限

## 感測器配置

管理者可在魚池中新增感測器並設定名稱、類型、位置與啟用狀態。

感測器位置採用 `0 ~ 100` 的百分比座標。例如：

```text
X = 25
Y = 70
```

代表感測器位於池區地圖寬度約 25%、高度約 70% 的位置。

Dashboard 管理功能包含：

- 新增感測器
- 調整感測器位置
- 修改名稱與類型
- 啟用 / 停用感測器
- 刪除感測器
- 更新感測器 Token

## 感測器 Token

每顆感測器建立後會擁有專屬：

```text
secret_token
```

硬體上傳水質資料時，使用該 Token 對應至正確的感測器與魚池。

## 水質指標

| 欄位 | 說明 | 單位 |
| --- | --- | --- |
| `temperature` | 水溫 | °C |
| `ph` | pH | - |
| `dissolved_oxygen` | 溶氧量 | mg/L |
| `ammonia_nitrogen` | 氨氮 | mg/L |
| `nitrite` | 亞硝酸鹽 | mg/L |
| `salinity` | 鹽度 | ppt |

## 水質警戒值

系統可設定以下水質指標的上下限：

- 溶氧
- pH
- 氨氮
- 亞硝酸鹽
- 溫度

警戒值可用於 Dashboard 狀態、水質異常判斷、水質穩定度與 Discord 警報。

實際警戒範圍應依養殖物種與場域需求設定。

## 水質歷史紀錄

Dashboard 可查詢不同時間範圍的歷史資料，並依感測器篩選，例如：

```text
最近 1 小時
最近 3 小時
最近 24 小時
最近 7 天
最近 30 天
自訂日期範圍
```

## CSV 匯出

魚池歷史資料可由：

```text
/water/<pond_id>/export-csv/
```

匯出 CSV，內容包含檢測時間、感測器名稱與各項水質數值。

## 魚池分享權限

魚池支援管理與唯讀權限，可依使用情境分享魚池資料。

管理者可修改魚池、感測器、警戒值與設備設定；Viewer 主要提供資料查看功能。

## 水車自動規則

魚池可設定水車設備，並依感測器數值判斷是否需要運作。

例如：

```text
dissolved_oxygen < 4.5
```

可作為水車啟動條件。

支援的比較條件：

```text
<
<=
>
>=
==
```

## 模擬資料

管理功能可產生測試水質資料，供 Dashboard、圖表、異常流程、AI 導覽與水車規則測試使用。

---

# 感測器資料上傳 API

系統提供 HTTP JSON API，讓 ESP32、ESP8266、Raspberry Pi、PLC Gateway 或其他設備上傳水質資料。

```text
POST /water/api/upload/
```

本機範例：

```text
http://127.0.0.1:8000/water/api/upload/
```

區網設備則使用 Django Server 所在電腦的 IP，例如：

```text
http://192.168.1.100:8000/water/api/upload/
```

## 認證方式

每顆 `PondSensor` 使用自己的：

```text
secret_token
```

Token 直接放在 JSON Body 中。

```json
{
  "secret_token": "YOUR_SENSOR_TOKEN",
  "temperature": 27.2,
  "ph": 8.12,
  "dissolved_oxygen": 6.4,
  "ammonia_nitrogen": 0.05,
  "nitrite": 0.02,
  "salinity": 24.5
}
```

後端會透過 `secret_token` 找到對應的感測器與魚池，因此不需要額外提供 `sensor_id`。

## Request

### Method

```text
POST
```

### Content-Type

```text
application/json
```

### JSON 欄位

| 欄位 | 類型 | 必填 | 說明 |
| --- | --- | --- | --- |
| `secret_token` | String | 是 | 感測器專屬 Token |
| `temperature` | Float | 是 | 水溫 °C |
| `ph` | Float | 是 | pH |
| `dissolved_oxygen` | Float | 是 | 溶氧 mg/L |
| `ammonia_nitrogen` | Float | 否 | 氨氮 mg/L |
| `nitrite` | Float | 否 | 亞硝酸鹽 mg/L |
| `salinity` | Float | 否 | 鹽度 ppt |

## 成功回應

HTTP `200`

```json
{
  "status": "success",
  "message": "水質數據已成功記錄。",
  "reading_id": 482
}
```

## 常見回應狀態

| HTTP Status | 說明 |
| --- | --- |
| `200` | 資料成功寫入 |
| `400` | JSON、必要欄位或數值格式錯誤，或感測器未啟用 |
| `403` | `secret_token` 無效 |
| `405` | Request Method 不是 POST |

---

# Python 上傳範例

安裝 Requests：

```bash
pip install requests
```

範例：

```python
import requests

url = "http://127.0.0.1:8000/water/api/upload/"

payload = {
    "secret_token": "YOUR_SENSOR_TOKEN",
    "temperature": 26.8,
    "ph": 8.05,
    "dissolved_oxygen": 5.9,
    "ammonia_nitrogen": 0.08,
    "nitrite": 0.015,
    "salinity": 25.0,
}

response = requests.post(
    url,
    json=payload,
    timeout=10,
)

print("HTTP Status:", response.status_code)
print("Response:", response.json())
```

---

# ESP32 上傳範例

以下為基本 API 串接範例，可依實際感測器與網路環境修改。

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

const char* serverUrl =
  "http://192.168.1.100:8000/water/api/upload/";

const char* sensorToken =
  "YOUR_SENSOR_TOKEN";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    float temperature = 26.5;
    float ph = 8.1;
    float dissolvedOxygen = 6.2;
    float ammoniaNitrogen = 0.04;
    float nitrite = 0.01;
    float salinity = 24.5;

    String payload = "{";
    payload += "\"secret_token\":\"" + String(sensorToken) + "\",";
    payload += "\"temperature\":" + String(temperature, 2) + ",";
    payload += "\"ph\":" + String(ph, 2) + ",";
    payload += "\"dissolved_oxygen\":" + String(dissolvedOxygen, 2) + ",";
    payload += "\"ammonia_nitrogen\":" + String(ammoniaNitrogen, 3) + ",";
    payload += "\"nitrite\":" + String(nitrite, 3) + ",";
    payload += "\"salinity\":" + String(salinity, 2);
    payload += "}";

    int statusCode = http.POST(payload);

    Serial.print("HTTP Status: ");
    Serial.println(statusCode);

    if (statusCode > 0) {
      Serial.println(http.getString());
    }

    http.end();
  }

  // 範例：每 15 分鐘上傳一次
  delay(900000);
}
```

基本流程：

```text
讀取感測器
    ↓
建立 JSON
    ↓
加入 secret_token
    ↓
POST /water/api/upload/
    ↓
檢查 HTTP Status
    ↓
等待下一次採樣
```

---

# 主要網址

| Path | 功能 |
| --- | --- |
| `/` | 首頁 |
| `/events/` | 活動 |
| `/notices/` | 公告 |
| `/usr/` | USR 成果 |
| `/guide/` | 數位導覽 |
| `/water/` | 水質監控 |
| `/chat/` | AI 導覽助手 |
| `/accounts/profile/` | 個人頁面 |
| `/adminx/` | 管理後台 |
| `/water/api/upload/` | 感測器資料上傳 API |
| `/water/api/latest/` | 最新水質 API |
| `/water/api/voice/` | 語音辨識 API |
| `/water/ar-feed/` | AR 養殖體驗 |

---

# 部署說明

目前專案預設使用 SQLite，適合開發、展示與小型部署。

若部署環境具有大量感測器、高頻資料寫入或多人同時操作需求，可依實際環境改用 PostgreSQL 或 MySQL 等資料庫。

Google OAuth、OpenAI、Email、Discord Webhook 與外部 ASR 等功能，需要在部署環境中提供對應的服務設定與憑證。

---

## 專案定位

本專案主要用於水井村在地網站、USR 成果展示、數位導覽，以及智慧養殖 / AIoT 水質監控相關功能的開發與整合。
