"""
IM Bridge 视图
提供两个接口:
1. POST /im/register - 前端获取 accid + token
2. POST /im/callback - 云信消息回调
"""
import os
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .nim_api import create_user, refresh_token, send_text_message, send_custom_message

# 复用现有的生成逻辑
from advisor.views import generate_stream_response

logger = logging.getLogger(__name__)

# 机器人账号ID（从环境变量读取）
BOT_ACCID = os.getenv("NIM_BOT_ACCID", "advisor_bot")


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """
    前端调用此接口获取 accid + token
    
    请求:
        POST /im/register
        {"user_id": "你的站内用户ID", "name": "昵称(可选)"}
    
    响应:
        {"accid": "xxx", "token": "xxx", "bot_accid": "advisor_bot"}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    user_id = str(body.get("user_id", "")).strip()
    name = body.get("name") or user_id
    
    if not user_id:
        return JsonResponse({"error": "user_id is required"}, status=400)
    
    # 用你的站内用户ID作为云信accid（加前缀避免冲突）
    accid = f"user_{user_id}"
    
    try:
        # 尝试创建用户（如果已存在会返回错误码414）
        result = create_user(accid=accid, name=name)
        if result.get("code") == 200:
            token = result["info"]["token"]
            logger.info(f"[IM] 创建新用户: {accid}")
        elif result.get("code") == 414:
            # 用户已存在，刷新token
            result = refresh_token(accid=accid)
            token = result["info"]["token"]
            logger.info(f"[IM] 刷新用户token: {accid}")
        else:
            logger.error(f"[IM] 创建用户失败: {result}")
            return JsonResponse({"error": f"NIM API error: {result}"}, status=500)
    except Exception as e:
        logger.error(f"[IM] 注册异常: {e}")
        return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({
        "accid": accid,
        "token": token,
        "bot_accid": BOT_ACCID
    })


@csrf_exempt
@require_http_methods(["POST"])
def callback(request):
    """
    云信消息抄送回调
    在云信控制台配置: https://你的域名/im/callback
    
    当用户发消息给机器人时，云信会POST到这个接口
    """
    try:
        event = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)
    
    logger.info(f"[IM Callback] 收到事件: {event}")
    
    # 解析消息字段（云信回调格式）
    from_accid = event.get("fromAccid") or event.get("from")
    to_accid = event.get("to")
    msg_type = event.get("type")  # 0=文本
    body = event.get("body", {})
    
    # 如果body是字符串，尝试解析
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except:
            body = {"msg": body}
    
    text = body.get("msg", "")
    
    # 只处理发给机器人的文本消息
    if to_accid != BOT_ACCID:
        logger.debug(f"[IM Callback] 消息目标不是机器人，跳过")
        return JsonResponse({"ok": True})
    
    if msg_type not in (0, "0", None):
        logger.debug(f"[IM Callback] 非文本消息，跳过")
        return JsonResponse({"ok": True})
    
    if not text:
        logger.debug(f"[IM Callback] 空消息，跳过")
        return JsonResponse({"ok": True})
    
    logger.info(f"[IM Callback] 处理用户消息: {from_accid} -> {text[:50]}...")
    
    # 调用现有的生成逻辑，把SSE流转成多条IM消息
    try:
        process_user_message(from_accid, text)
    except Exception as e:
        logger.error(f"[IM Callback] 处理消息失败: {e}")
        # 发送错误提示给用户
        send_text_message(BOT_ACCID, from_accid, "Sorry, something went wrong. Please try again.")
    
    return JsonResponse({"ok": True})


def process_user_message(user_accid, text):
    """
    处理用户消息，调用现有生成逻辑，把结果发回给用户
    """
    # 用用户accid作为session_id
    session_id = f"im_{user_accid}"
    
    # 累积完整回复
    full_response = ""
    
    # 调用现有的流式生成器
    for chunk in generate_stream_response(text, session_id):
        if not isinstance(chunk, str) or not chunk.startswith("data: "):
            continue
        
        payload = chunk[6:].strip()
        
        if payload == "[DONE]":
            break
        
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        
        # 处理内容消息
        if "content" in data:
            full_response += data["content"]
    
    # 发送最终完整回复
    if full_response:
        send_text_message(BOT_ACCID, user_accid, full_response)
        logger.info(f"[IM] 回复完成: {user_accid}, 长度: {len(full_response)}")
