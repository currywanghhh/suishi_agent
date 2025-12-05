# 🌐 Wu Xing Decision Advisor - Web 应用

基于五行命理的决策建议 Web 应用（Django 后端 + SSE 流式前端）

## 📁 项目结构

```
web_app/
├── wu_xing_advisor/      # Django 项目配置
│   ├── settings.py       # 项目设置
│   ├── urls.py           # 主路由
│   └── wsgi.py          # WSGI 配置
├── advisor/             # 主应用
│   ├── views.py         # 视图逻辑（SSE 流式输出、LLM 匹配）
│   ├── urls.py          # 应用路由
│   └── templates/       # 前端模板
│       └── advisor/
│           └── index.html  # 聊天界面
├── manage.py            # Django 管理脚本
├── db.sqlite3          # Django 默认数据库（会话等）
├── .env                # 环境变量（数据库、API 密钥）
└── README.md           # 本文档
```

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```powershell
pip install django mysql-connector-python requests python-dotenv
```

### 2️⃣ 配置环境变量

编辑 `.env` 文件：

```env
# 数据库配置（连接到知识库）
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=wu_xing_advisor

# LLM API 配置
SILICON_FLOW_API_KEY=你的API密钥
```

### 3️⃣ 运行数据库迁移

```powershell
python manage.py migrate
```

### 4️⃣ 启动开发服务器

```powershell
python manage.py runserver
```

### 5️⃣ 访问应用

打开浏览器访问：http://127.0.0.1:8000/

---

## 🎯 核心功能

### 1. 层级化 LLM 匹配

用户提问 → L1 → L2 → L3 → L4（共 4 次 LLM 调用）

**优势：**
- 精准匹配（每层候选少，准确率高）
- 可追溯路径
- 充分利用树状知识库结构

详见：`../MATCHING_PROCESS_EXPLANATION.md`

### 2. SSE 流式输出

- 实时显示匹配进度
- 分段流式输出内容（五行洞察、行动指南、沟通话术、能量调和）
- 显示响应时间

### 3. 聊天式界面

- 类似 ChatGPT 的对话体验
- 示例问题快捷输入
- 打字指示器
- 响应时间显示

---

## 🔧 核心代码说明

### `advisor/views.py`

#### `index(request)`
渲染主页面（聊天界面）。

#### `find_best_l4_match(user_query)`
层级化匹配逻辑：

```python
def find_best_l4_match(user_query):
    # 1. 查询所有 L1，用 LLM 选择最匹配的
    best_l1_id = call_llm_for_selection(l1_prompt)
    
    # 2. 查询该 L1 下的所有 L2，用 LLM 选择
    best_l2_id = call_llm_for_selection(l2_prompt)
    
    # 3. 查询该 L2 下的所有 L3，用 LLM 选择
    best_l3_id = call_llm_for_selection(l3_prompt)
    
    # 4. 查询该 L3 下的所有 L4，用 LLM 选择
    best_l4_id = call_llm_for_selection(l4_prompt)
    
    return best_l4_id
```

#### `generate_stream_response(user_query)`
SSE 流式响应生成器：

```python
def generate_stream_response(user_query):
    # 发送状态消息
    yield f"data: {json.dumps({'status': 'Analyzing...'})}\n\n"
    
    # 匹配 L4
    l4_id = find_best_l4_match(user_query)
    
    # 查询内容
    content = get_l4_content(l4_id)
    
    # 流式输出 4 个部分
    for section in ['five_elements_insight', 'action_guide', ...]:
        yield f"data: {json.dumps({'section': title, 'content': text})}\n\n"
    
    # 发送完成信号
    yield "data: [DONE]\n\n"
```

### `advisor/templates/advisor/index.html`

前端聊天界面（HTML + CSS + JS 一体）：

- **SSE 接收：** 使用 `EventSource` 读取流式响应
- **动态渲染：** 逐段显示内容
- **响应时间：** 计算从发送到 `[DONE]` 的时长

---

## ⚙️ 配置与优化

### 修改 LLM 模型

编辑 `advisor/views.py`：

```python
# 当前使用快速模型
model = "alibaba/Qwen2.5-7B-Instruct"

# 如需更智能但较慢的模型
# model = "deepseek-ai/DeepSeek-R1"
```

### 调整流式输出速度

编辑 `advisor/views.py` 的 `generate_stream_response`：

```python
# 当前每 0.003 秒发送一个块
time.sleep(0.003)

# 更快：0.001 秒
# 更慢：0.01 秒
```

### 缓存常见问题

在 `views.py` 添加缓存逻辑：

```python
from django.core.cache import cache

def find_best_l4_match(user_query):
    cache_key = f"match_{hash(user_query)}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 原有匹配逻辑...
    result = ...
    
    cache.set(cache_key, result, timeout=3600)  # 缓存 1 小时
    return result
```

---

## 🐛 调试技巧

### 查看匹配路径

在 `views.py` 的 `find_best_l4_match` 函数中，已添加调试输出：

```python
print(f"[Match] L1 Domain ID: {best_l1_id}")
print(f"[Match] L2 Scenario ID: {best_l2_id}")
print(f"[Match] L3 Sub-scenario ID: {best_l3_id}")
print(f"[Match] L4 Intention ID: {best_l4_id}")
```

运行服务器时在终端查看。

### 测试单次匹配

使用命令行工具（在 `../data_generation/` 目录）：

```powershell
cd ../data_generation
python test_l4_interaction.py
```

输入问题，查看匹配结果和内容。

### 性能分析

添加计时器：

```python
import time

start = time.time()
l4_id = find_best_l4_match(user_query)
elapsed = time.time() - start
print(f"[Timing] Matching took {elapsed:.2f} seconds")
```

---

## 📊 数据库依赖

Web 应用依赖以下表（由数据生成脚本创建）：

1. **`knowledge_base`** - 4 层知识结构
2. **`l4_content`** - L4 详细内容

**重要：** 在运行 Web 应用前，必须先运行数据生成脚本填充数据。

参见：`../data_generation/README.md`

---

## 🚀 部署指南

### 生产环境配置

1. **使用生产级服务器：**
   ```powershell
   pip install gunicorn
   gunicorn wu_xing_advisor.wsgi:application --bind 0.0.0.0:8000
   ```

2. **配置静态文件：**
   ```python
   # settings.py
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   ```
   ```powershell
   python manage.py collectstatic
   ```

3. **使用环境变量管理密钥：**
   ```python
   # settings.py
   SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

4. **使用 HTTPS：**
   - 配置 Nginx 或 Caddy 反向代理
   - 获取 SSL 证书（Let's Encrypt）

---

## 🔐 安全建议

1. **保护 API 密钥：** 不要将 `.env` 提交到版本控制
2. **限制请求频率：** 使用 Django 限流中间件
3. **输入验证：** 对用户输入进行清洗和验证
4. **CORS 配置：** 生产环境中限制允许的来源

---

## 📈 性能优化方案

### 1. 向量检索替代 LLM 匹配

使用 embedding + 向量数据库：

```python
# 伪代码
embeddings = get_embeddings_for_all_l4()
query_embedding = get_embedding(user_query)
best_l4_id = find_most_similar(query_embedding, embeddings)
```

**优势：** 从 4 次 LLM 调用降为 0 次，响应时间 < 1 秒

**需要：** Pinecone / Milvus / FAISS + OpenAI Embeddings API

### 2. 混合方式

- L1 用 LLM（6 个候选，快速）
- L2-L3 用关键词匹配
- L4 用 LLM 精准匹配

**优势：** 平衡速度和准确性，2 次 LLM 调用

### 3. 缓存热门问题

- 将高频问题的匹配结果缓存
- 使用 Redis 存储

---

## 🧪 测试

### 单元测试

```python
# advisor/tests.py
from django.test import TestCase

class MatchingTestCase(TestCase):
    def test_l1_matching(self):
        # 测试 L1 匹配逻辑
        pass
```

运行测试：

```powershell
python manage.py test
```

### 性能测试

使用 Apache Bench：

```powershell
ab -n 100 -c 10 http://127.0.0.1:8000/advisor/ask/
```

---

## 🔗 相关文档

- **数据生成文档：** `../data_generation/README.md`
- **匹配流程详解：** `../MATCHING_PROCESS_EXPLANATION.md`
- **项目主 README：** `../README.md`

---

## ❓ 常见问题

### Q: 为什么响应这么慢？

A: 需要 4 次 LLM API 调用。优化方案：
- 切换到更快的模型（Qwen2.5-7B）
- 使用向量检索
- 缓存常见问题

### Q: 如何查看匹配了哪个 L4？

A: 查看终端日志，有 `[Match] L4 Intention ID: X` 的输出。

### Q: 前端显示 "未找到相关内容"

A: 检查：
1. 数据库中是否有 `l4_content` 数据
2. 终端是否有匹配错误日志
3. 运行 `test_l4_interaction.py` 验证数据

---

## 📞 支持

如有问题，请查看：
1. 终端日志（Django 开发服务器输出）
2. 浏览器控制台（前端错误）
3. 数据库查询结果（验证数据完整性）
