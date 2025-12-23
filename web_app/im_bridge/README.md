# IM Bridge - 网易云信集成模块

## 一、模块概述

`im_bridge` 是一个 Django 应用，用于将现有的 Wu Xing Decision Advisor 后端与网易云信（Netease IM）即时通讯服务集成。

**核心目标**：让前端通过云信SDK实现聊天界面，后端只负责处理消息逻辑，不再需要维护前端页面。

---

## 二、文件说明

```
im_bridge/
├── __init__.py      # Python 包初始化
├── admin.py         # Django Admin 配置（暂未使用）
├── apps.py          # Django App 配置
├── models.py        # 数据模型（暂未使用）
├── tests.py         # 测试文件
├── nim_api.py       # ⭐ 云信服务端 API 封装
├── urls.py          # ⭐ 路由配置
└── views.py         # ⭐ 核心视图（两个接口）
```

### 核心文件详解

#### `nim_api.py` - 云信 API 封装

封装了网易云信服务端 API 的常用操作：

| 函数 | 功能 | 说明 |
|------|------|------|
| `create_user(accid, name)` | 创建云信用户 | 为站内用户在云信侧注册账号 |
| `refresh_token(accid)` | 刷新用户 Token | 获取新的登录凭证 |
| `send_text_message(from, to, text)` | 发送文本消息 | 机器人回复用户 |
| `send_custom_message(from, to, payload)` | 发送自定义消息 | 用于流式/结构化数据 |

#### `views.py` - 两个核心接口

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| `register` | POST | `/im/register` | 为用户创建云信账号，返回 accid + token |
| `callback` | POST | `/im/callback` | 接收云信消息回调，处理用户问题并回复 |

#### `urls.py` - 路由配置

```python
urlpatterns = [
    path("register", views.register),   # POST /im/register
    path("callback", views.callback),   # POST /im/callback
]
```

---

## 三、功能说明

### 1. 用户注册（获取凭证）

前端调用 `/im/register` 获取云信登录凭证。

**请求**：
```json
POST /im/register
Content-Type: application/json

{
    "user_id": "站内用户ID",
    "name": "用户昵称（可选）"
}
```

**响应**：
```json
{
    "accid": "user_站内用户ID",
    "token": "云信Token（用于SDK登录）",
    "bot_accid": "advisor_bot"
}
```

### 2. 消息回调（接收并处理用户消息）

当用户在IM中发送消息给机器人时，云信会将消息抄送到 `/im/callback`。

**云信回调请求**：
```json
POST /im/callback

{
    "fromAccid": "user_123",
    "to": "advisor_bot",
    "type": 0,
    "body": "{\"msg\": \"约会该穿什么颜色？\"}"
}
```

**后端处理流程**：
1. 解析用户消息
2. 调用现有的 `generate_stream_response()` 生成回复
3. 通过云信 API 将回复发送给用户

**响应**：
```json
{"ok": true}
```

---

## 四、流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户登录流程                                   │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────────┐         ┌──────────────┐
    │  前端APP  │ ──1──> │  后端 Django  │ ──2──> │  网易云信API  │
    │          │         │ /im/register │         │  创建用户     │
    └──────────┘         └──────────────┘         └──────────────┘
         │                      │                        │
         │                      │ <────────3──────────── │
         │                      │   返回 accid + token   │
         │ <────────4────────── │                        │
         │  返回 accid + token  │                        │
         │                      │                        │
         ▼                      │                        │
    ┌──────────┐                │                        │
    │ 用云信SDK │                │                        │
    │ 登录IM   │                │                        │
    └──────────┘                │                        │


┌─────────────────────────────────────────────────────────────────────────┐
│                           消息交互流程                                   │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐         ┌──────────────┐         ┌──────────────┐
    │   用户    │ ──1──> │  网易云信     │ ──2──> │  后端 Django  │
    │ 发送消息  │         │  消息通道     │         │ /im/callback │
    └──────────┘         └──────────────┘         └──────────────┘
                                                         │
                                                         │ 3. 解析消息
                                                         ▼
                                                  ┌──────────────┐
                                                  │ advisor/     │
                                                  │ views.py     │
                                                  │ 调用现有逻辑  │
                                                  └──────────────┘
                                                         │
                                                         │ 4. 生成回复
                                                         ▼
    ┌──────────┐         ┌──────────────┐         ┌──────────────┐
    │   用户    │ <──6── │  网易云信     │ <──5── │  后端 Django  │
    │ 收到回复  │         │  推送消息     │         │ 调用云信API  │
    └──────────┘         └──────────────┘         └──────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                           完整交互示例                                   │
└─────────────────────────────────────────────────────────────────────────┘

用户操作                    系统处理                      结果
───────                    ────────                      ────
1. 打开APP                  
   └─> 调用 /im/register    后端创建云信账号              返回 accid + token
                           
2. 用SDK登录云信            前端用 accid+token 登录       连接IM成功

3. 发送消息给 advisor_bot   
   └─> "约会穿什么颜色？"    云信转发到 /im/callback
                           后端解析 → 调用LLM → 生成回复
                           后端调用云信API发送回复        
                           
4. 收到机器人回复            云信推送消息到用户            显示回复内容
   └─> "建议选择暖色调..."
```

---

## 五、前后端配合指南

### 前端需要做的事

1. **调用注册接口获取凭证**
   ```javascript
   // 用户登录后，调用后端接口获取云信凭证
   const response = await fetch('/im/register', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
           user_id: '你的站内用户ID',
           name: '用户昵称'
       })
   });
   const { accid, token, bot_accid } = await response.json();
   ```

2. **使用云信SDK登录**
   ```javascript
   // 用返回的 accid + token 登录云信
   NIM.getInstance({
       appKey: '你的NIM_APP_KEY',
       account: accid,
       token: token,
       // ... 其他配置
   });
   ```

3. **发送消息给机器人**
   ```javascript
   // 给机器人发送文本消息
   nim.sendText({
       scene: 'p2p',
       to: bot_accid,  // 'advisor_bot'
       text: '约会该穿什么颜色？'
   });
   ```

4. **接收机器人回复**
   ```javascript
   // 监听消息
   nim.on('msg', function(msg) {
       console.log('收到消息:', msg.text);
       // 渲染到聊天界面
   });
   ```

### 后端需要做的事

1. **配置环境变量**（`.env`）
   ```env
   NIM_APP_KEY=你的AppKey
   NIM_APP_SECRET=你的AppSecret
   NIM_BOT_ACCID=advisor_bot
   ```

2. **在云信控制台配置回调URL**
   - 登录 https://app.yunxin.163.com/
   - 找到「消息抄送」配置
   - 设置回调地址：`https://你的域名/im/callback`

3. **创建机器人账号**
   ```python
   # 可以在 Django shell 中执行一次
   from im_bridge.nim_api import create_user
   create_user("advisor_bot", "五行顾问")
   ```

### 接口约定

| 项目 | 值 |
|------|------|
| 注册接口 | `POST /im/register` |
| 回调接口 | `POST /im/callback`（云信调用，前端不用管） |
| 机器人ID | `advisor_bot`（由 `NIM_BOT_ACCID` 配置） |
| 用户ID格式 | `user_{站内用户ID}` |

---

## 六、注意事项

1. **Token 有效期**
   - 云信 Token 有有效期，过期后前端需重新调用 `/im/register` 刷新

2. **回调安全**
   - 生产环境建议在云信控制台配置 IP 白名单
   - 可在 `callback` 视图中添加签名校验

3. **消息限流**
   - 云信有 API 调用频率限制，避免短时间内大量发送

4. **错误处理**
   - 如果消息处理失败，会向用户发送错误提示
   - 详细日志记录在 Django 日志中

---

## 七、测试方法

### 1. 测试注册接口

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/im/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"user_id": "test123", "name": "测试用户"}'
```

### 2. 模拟云信回调

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/im/callback" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"fromAccid": "user_test123", "to": "advisor_bot", "type": 0, "body": "{\"msg\": \"约会穿什么？\"}"}'
```

---

## 八、相关文档

- [网易云信官方文档](https://doc.yunxin.163.com/)
- [创建用户 API](https://doc.yunxin.163.com/messaging/server-apis/TM0ODk0NjQ)
- [发送消息 API](https://doc.yunxin.163.com/messaging/server-apis/TYzMDE4NzI)
- [消息抄送配置](https://doc.yunxin.163.com/messaging/server-apis/Dc0MjQ4NTM)

---

## 九、Django 架构说明

对于不熟悉 Django 的开发者，这一节说明 `web_app` 项目的整体架构。

### Django 的 Project 与 App 概念

```
web_app/                              # 这是一个 Django Project（项目）
├── manage.py                         # Django 命令行工具
├── wu_xing_advisor/                  # 项目配置文件夹（项目同名）
│   ├── settings.py                   # ⭐ 全局配置（数据库、Apps等）
│   ├── urls.py                       # ⭐ 总路由（URL分发器）
│   ├── wsgi.py                       # WSGI 服务器入口
│   └── asgi.py                       # ASGI 服务器入口
├── advisor/                          # ⭐ App #1 - 决策顾问（Web聊天）
│   ├── views.py                      # 视图函数（业务逻辑）
│   ├── urls.py                       # App路由
│   ├── models.py                     # 数据模型
│   └── templates/                    # HTML模板
│       └── advisor/index.html
└── im_bridge/                        # ⭐ App #2 - 云信集成（IM聊天）
    ├── views.py                      # 视图函数（注册、回调）
    ├── urls.py                       # App路由
    └── nim_api.py                    # 云信API封装
```

**核心概念**：
- **Project（wu_xing_advisor）**：整个网站项目，管理所有配置和App
- **App（advisor, im_bridge）**：功能模块，每个App专注一个业务领域

### URL 路由流程

从浏览器请求到视图函数的完整路径：

```
┌─────────────────────────────────────────────────────────────────┐
│                        URL 路由分发流程                          │
└─────────────────────────────────────────────────────────────────┘

用户请求                总路由                   APP路由                视图函数
─────────              ─────────                ────────              ────────

GET /                   
   └─> wu_xing_advisor/urls.py
          └─> path("", include("advisor.urls"))
                                └─> advisor/urls.py
                                       └─> path("", views.index)
                                                      └─> advisor/views.py::index()
                                                            返回 index.html

POST /generate-stream
   └─> wu_xing_advisor/urls.py
          └─> path("", include("advisor.urls"))
                                └─> advisor/urls.py
                                       └─> path("generate-stream", views.stream)
                                                      └─> advisor/views.py::stream()
                                                            调用 generate_stream_response()
                                                            返回 SSE 流

POST /im/register
   └─> wu_xing_advisor/urls.py
          └─> path("im/", include("im_bridge.urls"))
                                 └─> im_bridge/urls.py
                                        └─> path("register", views.register)
                                                       └─> im_bridge/views.py::register()
                                                             调用 create_user()
                                                             返回 accid + token

POST /im/callback
   └─> wu_xing_advisor/urls.py
          └─> path("im/", include("im_bridge.urls"))
                                 └─> im_bridge/urls.py
                                        └─> path("callback", views.callback)
                                                       └─> im_bridge/views.py::callback()
                                                             调用 process_user_message()
                                                             返回 {"ok": true}
```

### 两个数据流向

#### 流向 #1: Web 聊天（advisor App）

```
浏览器 → /generate-stream → advisor/views.py::stream()
                               ↓
                         generate_stream_response()
                               ↓
                         调用 LLM API
                               ↓
                         返回 SSE 流 → 浏览器实时显示
```

#### 流向 #2: IM 聊天（im_bridge App）

```
用户发送IM消息 → 网易云信 → /im/callback → im_bridge/views.py::callback()
                                              ↓
                                        process_user_message()
                                              ↓
                                        调用 advisor.views.generate_stream_response()
                                              ↓
                                        把 SSE 流聚合成完整文本
                                              ↓
                                        调用 send_text_message() → 网易云信 → 用户收到回复
```

### 关键配置文件的作用

#### `wu_xing_advisor/settings.py`
```python
INSTALLED_APPS = [
    # ...
    'advisor',       # 注册 advisor App
    'im_bridge',     # 注册 im_bridge App
]
```
- 注册所有 App，Django 才会识别它们
- 配置数据库、中间件、模板等

#### `wu_xing_advisor/urls.py`（总路由）
```python
urlpatterns = [
    path("", include("advisor.urls")),      # 所有 / 开头的请求分发给 advisor
    path("im/", include("im_bridge.urls")), # 所有 /im/ 开头的请求分发给 im_bridge
]
```
- 这是URL的"总调度室"
- 根据路径前缀分发到不同的 App

#### `advisor/urls.py`（App路由）
```python
urlpatterns = [
    path("", views.index),                    # GET /
    path("generate-stream", views.stream),    # POST /generate-stream
]
```

#### `im_bridge/urls.py`（App路由）
```python
urlpatterns = [
    path("register", views.register),   # POST /im/register
    path("callback", views.callback),   # POST /im/callback
]
```

### App 之间如何复用代码

在 `im_bridge/views.py` 中，直接导入 `advisor` 的函数：

```python
# im_bridge 复用 advisor 的生成逻辑
from advisor.views import generate_stream_response

def process_user_message(user_accid, text):
    # ...
    for chunk in generate_stream_response(text, session_id):
        # 处理流式响应
```

**好处**：
- 两个 App 共享同一套 LLM 生成逻辑
- advisor 提供 Web 界面 + SSE 流
- im_bridge 提供 IM 接口，把 SSE 流转成 IM 消息

### 完整请求生命周期示例

以用户发送 IM 消息为例：

```
1. 用户在手机 App 发送消息："约会穿什么？"
   ↓
2. 网易云信接收消息，POST 到 https://你的域名/im/callback
   ↓
3. Django 接收请求，根据 URL 查找路由：
   /im/callback → wu_xing_advisor/urls.py → im_bridge.urls → views.callback
   ↓
4. im_bridge/views.py::callback() 被执行：
   - 解析消息体，提取 fromAccid、text
   - 调用 process_user_message(user_accid, text)
   ↓
5. process_user_message() 调用 advisor.views.generate_stream_response()：
   - 查询知识库匹配 L4 条目
   - 调用 LLM API 生成回复
   - 返回 SSE 流（生成器）
   ↓
6. process_user_message() 累积完整回复：
   - 遍历 SSE 流的每个 chunk
   - 拼接成完整文本
   ↓
7. 调用 send_text_message(BOT_ACCID, user_accid, full_response)：
   - 通过网易云信 API 发送消息
   ↓
8. 网易云信推送消息到用户手机
   ↓
9. 用户看到回复："建议选择暖色调..."
```

---

**创建日期**：2025-12-22  
**关联模块**：`advisor/views.py` - 复用现有的 `generate_stream_response()` 生成回复
