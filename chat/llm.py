import json
import os

from . import tools


SYSTEM_PROMPT = """你是水井村網站的互動導覽助手，使用繁體中文回答。

回答原則：
- 先用網站資料回答活動、公告、USR 成果、AIoT 專案、地方故事入口與相關連結。
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


def chat(user_message: str, history: list[dict] | None = None) -> str:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
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
            result = tools.dispatch(call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "我查詢了幾次仍無法整理出穩定答案，請換個問法再試一次。"
