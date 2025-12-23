"""
网易云信服务端API封装
官方文档: https://doc.yunxin.163.com/messaging/server-apis
"""
import os
import time
import hashlib
import json
import requests

# 从环境变量读取配置
APP_KEY = os.getenv("NIM_APP_KEY", "")
APP_SECRET = os.getenv("NIM_APP_SECRET", "")


def _headers():
    """生成云信API请求头（含签名）"""
    nonce = os.urandom(8).hex()
    cur_time = str(int(time.time()))
    # CheckSum = SHA1(AppSecret + Nonce + CurTime)
    checksum = hashlib.sha1((APP_SECRET + nonce + cur_time).encode()).hexdigest()
    return {
        "AppKey": APP_KEY,
        "Nonce": nonce,
        "CurTime": cur_time,
        "CheckSum": checksum,
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }


def create_user(accid, name=None, icon=None):
    """
    创建云信用户
    https://doc.yunxin.163.com/messaging/server-apis/TM0ODk0NjQ
    
    参数:
        accid: 用户账号ID（你的站内用户ID）
        name: 昵称（可选）
        icon: 头像URL（可选）
    返回:
        {"code": 200, "info": {"token": "xxx", "accid": "xxx", "name": "xxx"}}
    """
    data = {"accid": accid}
    if name:
        data["name"] = name
    if icon:
        data["icon"] = icon
    
    response = requests.post(
        "https://api-sg.yunxinapi.com/nimserver/user/create.action",
        headers=_headers(),
        data=data,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def refresh_token(accid):
    """
    刷新用户Token
    https://doc.yunxin.163.com/messaging/server-apis/jk4NDE0OTM
    
    参数:
        accid: 用户账号ID
    返回:
        {"code": 200, "info": {"token": "新token", "accid": "xxx"}}
    """
    response = requests.post(
        "https://api-sg.yunxinapi.com/nimserver/user/refreshToken.action",
        headers=_headers(),
        data={"accid": accid},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def send_text_message(from_accid, to_accid, text):
    """
    发送文本消息
    https://doc.yunxin.163.com/messaging/server-apis/TYzMDE4NzI
    
    参数:
        from_accid: 发送方（机器人accid）
        to_accid: 接收方（用户accid）
        text: 消息内容
    """
    data = {
        "from": from_accid,
        "ope": 0,  # 0=点对点
        "to": to_accid,
        "type": 0,  # 0=文本消息
        "body": json.dumps({"msg": text}, ensure_ascii=False),
    }
    response = requests.post(
        "https://api-sg.yunxinapi.com/nimserver/msg/sendMsg.action",
        headers=_headers(),
        data=data,
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def send_custom_message(from_accid, to_accid, payload, push_content=None):
    """
    发送自定义消息（用于流式分段输出）
    
    参数:
        from_accid: 发送方（机器人accid）
        to_accid: 接收方（用户accid）
        payload: 自定义JSON数据，如 {"type": "stream", "content": "..."}
        push_content: 推送文案（可选）
    """
    data = {
        "from": from_accid,
        "ope": 0,
        "to": to_accid,
        "type": 100,  # 100=自定义消息
        "body": json.dumps(payload, ensure_ascii=False),
    }
    if push_content:
        data["pushcontent"] = push_content
    
    response = requests.post(
        "https://api-sg.yunxinapi.com/nimserver/msg/sendMsg.action",
        headers=_headers(),
        data=data,
        timeout=10
    )
    response.raise_for_status()
    return response.json()
