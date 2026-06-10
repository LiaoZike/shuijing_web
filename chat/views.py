import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import llm


def chat_page(request):
    return render(request, "chat/chat.html")


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "請送出正確的 JSON 格式。"}, status=400)

    message = (body.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "請先輸入想詢問的內容。"}, status=400)

    history = request.session.get("chat_history", [])

    try:
        reply = llm.chat(message, history=history, user=request.user)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"error": f"聊天服務暫時無法回應：{type(exc).__name__}: {exc}"},
            status=500,
        )

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    request.session["chat_history"] = history[-20:]

    return JsonResponse({"reply": reply})


@csrf_exempt
@require_POST
def clear_api(request):
    request.session.pop("chat_history", None)
    return JsonResponse({"message": "聊天紀錄已清除。"})
