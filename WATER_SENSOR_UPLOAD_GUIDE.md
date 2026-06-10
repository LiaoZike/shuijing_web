# 水井村硬體感測器上傳水質數據說明書 (WATER_SENSOR_UPLOAD_GUIDE)

本文件供硬體端工程師（如使用 ESP8266、ESP32、樹莓派或工業 PLC 閘道器）對接水井村水質監控系統使用。

水井村系統提供安全、免 CSRF 的 **HTTP POST** API Endpoint，用於定期（例如每 10-30 分鐘）回傳現場水質讀值。

---

## 1. 介面接口說明 (API Specification)

- **接口網址 (URL Path)**: `/water/api/upload/` (例如本地開發環境為 `http://127.0.0.1:8000/water/api/upload/`)
- **請求方法 (HTTP Method)**: `POST`
- **數據類型 (Content-Type)**: `application/json`
- **安全認證 (Authorization)**:
  - 必須於 **HTTP Headers** 中帶入 `X-Api-Key`。
  - 或在 **JSON Payload** 的最外層帶入 `api_key` 欄位。
  - **預設 API 專用金鑰**: `shuijing_key_2026`

---

## 2. 請求主體 (JSON Request Body)

```json
{
  "api_key": "shuijing_key_2026",
  "sensor_id": 1,
  "temperature": 27.2,
  "ph": 8.12,
  "dissolved_oxygen": 6.4,
  "ammonia_nitrogen": 0.05,
  "nitrite": 0.02,
  "salinity": 24.5
}
```

### 欄位詳細定義：

| 欄位名稱 | 類型 | 必填 | 說明 |
| :--- | :--- | :--- | :--- |
| **api_key** | String | 否\* | API 認證金鑰。如果在 Header 中已包含 `X-Api-Key` 則可省略。 |
| **sensor_id** | Integer | 是 | 系統分配給感測器的唯一 ID。可在該感測器詳情頁面的管理面板中查得。 |
| **temperature**| Float | 是 | 水溫值，單位：`°C`。 |
| **ph** | Float | 是 | 酸鹼值 (pH)，範圍 `0.0` 到 `14.0`。 |
| **dissolved_oxygen**| Float| 是 | 溶氧量 (DO)，單位：`mg/L`。 |
| **ammonia_nitrogen**| Float| 否 | 氨氮量 (NH₃-N)，單位：`mg/L`。 |
| **nitrite** | Float | 否 | 亞硝酸鹽量 (NO₂)，單位：`mg/L`。 |
| **salinity** | Float | 否 | 鹽度值，單位：`ppt`。 |

---

## 3. 響應回傳 (API Response)

### 成功 (200 OK)
```json
{
  "status": "success",
  "message": "水質數據已成功記錄。",
  "reading_id": 482
}
```

### 失敗 (400 / 403 / 404 / 405)
```json
{
  "status": "error",
  "message": "無效的 API 專用金鑰。"
}
```
*常見錯誤原因包含金鑰無效、感測器 ID 不存在、感測器已在管理系統中被停用、或是格式並非合法 JSON。*

---

## 4. 對接程式碼範例 (Code Examples)

### 範例 A：Python 對接範例

```python
import json
import requests

url = "http://127.0.0.1:8000/water/api/upload/"
headers = {
    "Content-Type": "application/json",
    "X-Api-Key": "shuijing_key_2026"
}

payload = {
    "sensor_id": 1,
    "temperature": 26.8,
    "ph": 8.05,
    "dissolved_oxygen": 5.9,
    "ammonia_nitrogen": 0.08,
    "nitrite": 0.015,
    "salinity": 25.0
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("HTTP Status Code:", response.status_code)
    print("Response JSON:", response.json())
except Exception as e:
    print("連線發生異常:", e)
```

### 範例 B：Arduino C++ (適用於 ESP8266/ESP32 微處理器)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "Your_WiFi_SSID";
const char* password = "Your_WiFi_Password";
const char* serverUrl = "http://YOUR_SERVER_IP:8000/water/api/upload/";

void setup() {
  Serial.begin(115500);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi連線成功");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    
    // 設定 Header
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Api-Key", "shuijing_key_2026");
    
    // 構造 JSON 數據
    String jsonPayload = "{\"sensor_id\": 1, \"temperature\": 26.5, \"ph\": 8.1, \"dissolved_oxygen\": 6.2, \"ammonia_nitrogen\": 0.04, \"nitrite\": 0.01}";
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
    } else {
      Serial.print("POST傳送失敗，錯誤代碼: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  }
  // 每 15 分鐘上傳一次 (900000 毫秒)
  delay(900000);
}
```

---

## 5. 關於 MQTT 對接整合方式

若硬體環境因低功耗或網路限制只能透過 MQTT 協定傳輸：
1. 可在雲林在地端或雲端架設輕量級的 MQTT Broker（例如 **Mosquitto**）。
2. 感測器將 JSON 讀值 publish 到指定 topic（如 `shuijing/sensor_1/readings`）。
3. 撰寫一個極簡的 Node-RED 流程或 Python 訂閱腳本 (Subscriber)，在收到 MQTT 訊息時解析其 JSON 內容，並隨即轉發 HTTP POST 請求至本 API 接口，實現 MQTT 對接。
