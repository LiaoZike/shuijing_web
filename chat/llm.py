import json
import os

from . import tools


SYSTEM_PROMPT = """你是水井村網站的互動導覽助手，使用繁體中文回答。

回答原則：
- 先用網站資料回答活動、公告、USR 成果、AIoT 專案、地方故事入口與相關連結。
- 使用者詢問水池、水質、溶氧、pH、鹽度或統整狀態時，優先呼叫水質工具，再整理成容易掃讀的重點。
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
        user_directive += f"\n\n【安全性指令】目前使用者已登入，帳號為：{username}。你只能且必須使用提供給你的工具查詢該使用者的魚池數據，不可提供任何其他帳號的數據。未經工具查詢到的魚池或數據請勿憑空捏造。"
    else:
        user_directive += "\n\n【安全性指令】目前使用者為【未登入訪客】。如果使用者詢問關於魚池、水池統整、水質、數據等私人資訊，請不要調用任何水質工具，並直接禮貌地提示他：『請先登入帳號以查看您的魚池數據。』，請勿回答任何虛構的魚池數據。"

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
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "我查詢了幾次仍無法整理出穩定答案，請換個問法再試一次。"
