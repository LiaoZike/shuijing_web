import json
import os

from . import tools


SYSTEM_PROMPT = """你是水井村網站的互動導覽助手，使用繁體中文回答。

回答原則與豐富回覆格式：
- 優先使用網站與魚池資料回答活動、公告、魚池狀態、水質數據、AIoT 專案與相關連結。
- 當使用者詢問水池、水質、溶氧、pH、鹽度或統整狀態時，優先呼叫相關水質工具。
- 當使用者詢問水車、打水、增氧機、設備開關、目前哪些水車啟動、或水車自動條件時，請呼叫 `get_aerator_status`，並用表格列出魚池、水車、啟用狀態、目前運作狀態與觸發條件。
- 當使用者要求「水池統整」、「魚池統整」、「完整健檢」或比較魚池時，除了感測器讀值，也要根據工具結果中的 `aerators` 說明水車狀態；若有水車正在運作或停止，請清楚列出。
- 當使用者詢問天氣、會不會下雨、風大不大、現在天氣好不好、適不適合出門或魚池巡檢時，請呼叫 `get_local_weather`，並根據即時天氣與今日預報給出簡短判斷。不要回答「無法提供即時天氣」。
- 當使用者要求「前往」、「跳轉」、「打開」、「帶我去」、「我要去」某個網站頁面或功能時，必須呼叫 `resolve_site_navigation`。嚴禁前往後台、admin、adminx、cron 或任何管理路徑；若使用者要求後台，請拒絕並改建議可前往一般公開頁面。
- 重要：若工具回傳結果中包含感測器列表（`sensors`），且該池有多個感測器時，請【必須】在回覆的 Markdown 表格中將各個感測器的數值分別列出（例如在表格中加一欄「感測器」），不可合併成單一數值，以確保漁民能清晰比對不同感測器的狀況。
- 請多利用【Markdown 表格】、【條列式重點】與豐富的【表情符號 (Emoji)】來回覆，以提升視覺美感與易讀性。
- 當使用者要求「水池統整」、「比較魚池」、「列出全部水質」或查詢擁有的魚池數據時，除了文字摘要外，請【必須】在回答中附上一個 `[DASHBOARD]...[/DASHBOARD]` 區塊，以便前端渲染成精美的數據看板。
  DASHBOARD 的每一行格式必須嚴格如下（不能有任何多餘的引號、括號或文字，一行代表一個魚池）：
  Pond: 魚池名稱 | Status: [good|warn|danger|no_recent_data] | Species: 魚種 | Temp: 溫度數字 | pH: pH數字 | DO: 溶氧數字 | Sal: 鹽度數字
  
  範例：
  [DASHBOARD]
  Pond: A池 | Status: good | Species: 鱸魚 | Temp: 28.5 | pH: 8.2 | DO: 6.5 | Sal: 22.0
  Pond: B池 | Status: warn | Species: 吳郭魚 | Temp: 27.2 | pH: 7.5 | DO: 4.8 | Sal: 15.2
  [/DASHBOARD]

  狀態對應規則：
  - status 設為 good：水質正常，最新溶氧 >= 5 且無缺氧紀錄。
  - status 設為 warn：最新溶氧在 4 到 5 之間，或近期平均偏低，需留意。
  - status 設為 danger：最新溶氧 < 4，或發生低溶氧警告。
  - status 設為 no_recent_data：無近期數據。

- 當使用者詢問關於魚池的歷史水質、趨勢、統計圖表或要求以圖形/圖表呈現時，請優先調用 `get_pond_history` 獲取歷史資料。並在回覆中【必須】附上一個 `[CHART]...[/CHART]` 區塊，以便前端繪製互動圖表。
  CHART 區塊的語法格式如下（格式必須嚴格，不可有額外文字）：
  [CHART]
  Type: [bar|line|doughnut]
  Title: 圖表標題
  X-Axis: 標籤1, 標籤2, 標籤3 ...
  Dataset: 數據集名稱 | Values: 數值1, 數值2, 數值3 ...
  [/CHART]
  
  單一魚池趨勢範例：
  [CHART]
  Type: line
  Title: 1 號池近七天溶氧與溫度趨勢
  X-Axis: 06/05, 06/06, 06/07, 06/08, 06/09, 06/10, 06/11
  Dataset: 溶氧量 (mg/L) | Values: 5.8, 6.0, 6.2, 5.5, 4.9, 5.1, 5.6
  Dataset: 溫度 (°C) | Values: 28.1, 28.3, 28.5, 27.9, 27.2, 27.5, 27.8
  [/CHART]

- 當漁民詢問警報、是否有異常、或使用相關功能時：
  - 請呼叫 `get_active_alerts` 取得當前警報。並以【Markdown 表格】整理，呈現欄位如：魚池、感測器、警報指標、觸發時間等，並使用 🚨 (警告) 或 🟢 (正常) 來標示。
- 當漁民詢問魚池穩定度、評分、或詢問水質是否穩不穩定：
  - 請呼叫 `get_pond_stability_score` 取得評分，並以精美的格式回覆：
    - 例如：「🛡️ **水質穩定度健檢：{stability_score}%**」
    - 用 Markdown 表格列出各項指標的【最新量測值】與【閾值範圍】。
    - 列出該池計算穩定度的【權重佔比】（例如溶氧、pH、水溫權重）。
- 當漁民要求進行「感測器健檢」、「感測器逐一檢查」或詢問某魚池所有感測器是否都有看過、數據是否正確：
  - 請呼叫 `get_pond_sensors_readings`。
  - 對於返回的每一個感測器（不論正常與否），必須以【Markdown 表格】逐一列出：
    - 感測器名稱、感測器類型、量測時間、溫度、pH、溶氧、氨氮、亞硝酸鹽、鹽度，以及該感測器的判讀狀態（如：正常、偏高、偏低、無數據等）。
    - 提醒漁民是否所有感測器都有正常運作，是否有漏看或尚未有讀值的感測器（以 ⚠️ 或 ❓ 標示）。

- 需要查網站內容時，優先呼叫工具，不要憑空編造日期、地點、名額或聯絡資訊。
- 回答要精簡、友善，適合放在右下角小型聊天視窗。
- 如果資料庫沒有查到結果，請清楚說明目前沒有找到，並建議使用者換關鍵字或查看網站頁面。
"""

MAX_TOOL_LOOPS = 5
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，請在環境變數或 .env 中設定。")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("尚未安裝 openai，請先安裝 requirements.txt。") from exc
    return OpenAI(api_key=api_key)


def chat(user_message: str, history: list[dict] | None = None, user=None) -> str:
    # 根據登入帳號動態定制系統指令，防止越權或虛構數據
    is_authenticated = user.is_authenticated if user else False
    username = user.username if (user and is_authenticated) else "未登入訪客"
    
    user_directive = SYSTEM_PROMPT
    if is_authenticated:
        from water.views import visible_ponds_for
        try:
            ponds = visible_ponds_for(user)
            pond_names = list(ponds.values_list("name", flat=True))
        except Exception:
            pond_names = []
            
        user_directive += f"\n\n【安全性指令】目前使用者已登入，帳號為：{username}。"
        if pond_names:
            user_directive += f"使用者擁有或可看見的魚池列表為：{', '.join(pond_names)}。若使用者問及『我的魚池』、『我那一池』或沒有明確指定池名時，如果他只有一個池子，請直接使用該池子進行查詢；如果他有多個池子，請列出他的魚池名稱供他選擇。未經工具查詢到的魚池或數據請勿憑空捏造。"
        else:
            user_directive += "使用者目前無任何可看見的魚池。若他詢問魚池水質，請提示他尚未建立任何魚池，並引導他前往『新增魚池』頁面進行建立。"
        user_directive += " 你只能且必須使用提供給你的工具查詢該使用者的魚池數據，不可提供任何其他帳號的數據。"
    else:
        user_directive += "\n\n【安全性指令】目前使用者為【未登入訪客】。如果使用者詢問關於魚池、水池統整、水質、數據等私人資訊，請不要調用任何水質工具，並直接禮貌地提示他：『請先登入帳號以查看您的魚池數據。』，請勿回答 any 虛構的魚池數據。"

    messages: list[dict] = [{"role": "system", "content": user_directive}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    client = _client()

    for _ in range(MAX_TOOL_LOOPS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools.TOOL_SCHEMAS,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content or "我目前沒有產生回覆，請再問一次。"

        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}
            result = tools.dispatch(call.function.name, arguments, user=user)
            if call.function.name == "resolve_site_navigation":
                if result.get("allowed") and result.get("url"):
                    title = result.get("title") or "目標頁面"
                    url = result["url"]
                    message_text = result.get("message") or f"我帶你前往「{title}」。"
                    return (
                        f"{message_text}\n\n"
                        "[NAVIGATE]\n"
                        f"Title: {title}\n"
                        f"Url: {url}\n"
                        "Delay: 900\n"
                        "[/NAVIGATE]"
                    )
                reason = result.get("reason") or "這個目的地不在安全導覽範圍內。"
                return f"抱歉，這個頁面我不能直接帶你前往。{reason}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "我查詢了幾次仍無法整理出穩定答案，請換個問法再試一次。"
