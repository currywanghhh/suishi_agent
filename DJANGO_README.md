# Django Web Application for Wu Xing Decision Advisor

## 启动指南

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

确保 `.env` 文件包含以下配置：
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=decision_app_kb
SILICON_FLOW_API_KEY=your_api_key
```

### 3. 运行数据库迁移

```bash
python manage.py migrate
```

### 4. 启动开发服务器

```bash
python manage.py runserver
```

### 5. 访问应用

在浏览器中打开: http://127.0.0.1:8000/

## 功能特性

### 🌟 五行决策助手 (Wu Xing Decision Advisor)

这是一个面向北美用户的五行决策助手网页应用，提供以下功能：

1. **智能问题匹配**：用户输入问题后，系统会自动匹配知识库中最相关的L4意图
2. **流式输出**：答案以流式方式逐字显示，提供类似ChatGPT的用户体验
3. **结构化建议**：每个回答包含四个部分：
   - 🔮 **五行洞察** (Five Elements Insight)
   - ✅ **行动指南** (Action Guide)
   - 💬 **沟通话术** (Communication Scripts)
   - 🌟 **能量调和** (Energy Harmonization)

### 技术架构

- **后端**: Django 5.2.8
- **流式输出**: Server-Sent Events (SSE)
- **数据库**: MySQL (使用现有的 `knowledge_base` 和 `l4_content` 表)
- **AI模型**: Silicon Flow API (DeepSeek-R1)

### 页面设计

- **响应式设计**: 适配桌面端和移动端
- **五行主题**: 使用渐变色和五行元素图标
- **友好交互**: 预设示例问题，一键填入
- **流畅体验**: 逐字显示答案，模拟真人对话

## 目录结构

```
agent/
├── wu_xing_advisor/          # Django项目配置
│   ├── settings.py           # 项目设置（已添加advisor应用）
│   └── urls.py               # 路由配置
├── advisor/                  # Django应用
│   ├── views.py              # 视图逻辑（流式输出、LLM调用）
│   ├── urls.py               # 应用路由
│   └── templates/advisor/
│       └── index.html        # 前端页面
├── manage.py                 # Django管理脚本
└── requirements.txt          # 依赖列表
```

## API端点

- `GET /` - 主页面（问答界面）
- `POST /advisor/ask/` - 流式回答接口（SSE）

## 使用说明

1. 在输入框中输入你的问题（英文）
2. 点击 "Get Guidance" 按钮
3. 系统会显示匹配的意图名称
4. 答案会以流式方式逐字显示，分为四个部分

### 示例问题

- "How can I balance work and personal time?"
- "Tips for maintaining a long-distance relationship"
- "How to communicate boundaries at work?"
- "How to handle cultural differences in dating?"

## 注意事项

- 确保已运行 `generate_l4_content.py` 生成了L4详细内容
- 流式输出速度可在 `views.py` 中调整 `time.sleep()` 参数
- 前端使用原生JavaScript实现SSE，无需额外框架
