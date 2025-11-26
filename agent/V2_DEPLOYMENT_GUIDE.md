# V2 快速部署指南

## 🚀 5分钟快速部署

### 前置条件
- ✅ 已完成V1的基础配置（数据库、API密钥、知识库生成）
- ✅ Django项目可以正常运行

### 部署步骤

#### 1. 确认新文件已添加
```bash
# 检查文件是否存在
ls agent/advisor/views_v2.py
ls agent/advisor/templates/advisor/index_v2.html
```

#### 2. 更新URL配置
已自动更新 `agent/advisor/urls.py`，无需手动修改。

#### 3. 重启Django服务器
```bash
cd agent
python manage.py runserver
```

#### 4. 访问V2版本
```
浏览器打开：http://localhost:8000/advisor/v2/
```

## 🧪 测试V2功能

### 测试用例1：Guided Mode（推荐）

1. 打开 `http://localhost:8000/advisor/v2/`
2. 确保选择了 "🧭 Guided" 模式
3. 输入问题：`How to prepare for a job interview?`
4. 点击 "Ask"
5. 观察：
   - ✅ 2-3秒内应该看到L2场景选项卡片
   - ✅ 点击一个卡片后立即看到L3选项
   - ✅ 继续选择L3、L4
   - ✅ 最终看到完整的指导内容

### 测试用例2：Quick Mode

1. 切换到 "⚡ Quick Answer" 模式
2. 输入同样的问题：`How to prepare for a job interview?`
3. 点击 "Ask"
4. 观察：
   - ✅ 会有8-10秒的等待时间（与V1相似）
   - ✅ 直接返回最终答案，无中间选择步骤

### 测试用例3：API测试

#### 测试 start_conversation
```bash
curl -X POST http://localhost:8000/advisor/v2/start/ \
  -H "Content-Type: application/json" \
  -d '{"query": "How to improve my communication skills?"}'
```

预期响应：
```json
{
  "session_id": "session_1732618234567",
  "step": "select_scenario",
  "domain": "Personal Development",
  "message": "Great! This seems related to Personal Development. Which specific situation fits best?",
  "options": [
    {
      "id": 15,
      "name": "Communication Skills",
      "description": "Improving verbal and non-verbal communication"
    },
    ...
  ]
}
```

#### 测试 continue_conversation
```bash
curl -X POST http://localhost:8000/advisor/v2/continue/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_1732618234567",
    "selected_id": 15,
    "step": "l2_selected"
  }'
```

## 🔍 故障排查

### 问题1：访问 /advisor/v2/ 报404
**原因：** URL配置未生效  
**解决：**
```bash
# 1. 检查urls.py是否正确导入views_v2
cat agent/advisor/urls.py

# 2. 确认Django已重启
# 按 Ctrl+C 停止服务器
python manage.py runserver
```

### 问题2：点击选项后报错 "Invalid session"
**原因：** 会话已过期或服务器重启  
**解决：**
- 刷新页面，重新开始对话
- 生产环境建议使用Redis存储会话

### 问题3：首次LLM分类失败
**原因：** API密钥或网络问题  
**解决：**
```bash
# 1. 检查API密钥
cat .env | grep SILICON_FLOW_API_KEY

# 2. 测试API连接
curl -X POST https://api.siliconflow.cn/v1/chat/completions \
  -H "Authorization: Bearer $SILICON_FLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-ai/DeepSeek-R1","messages":[{"role":"user","content":"Hi"}]}'

# 3. 查看Django日志
# 控制台应显示错误详情
```

### 问题4：选项卡片显示为空
**原因：** 知识库数据不完整  
**解决：**
```sql
-- 检查各层级数据量
SELECT level, COUNT(*) as count 
FROM knowledge_base 
GROUP BY level;

-- 应该看到：
-- level | count
-- ------|------
--   1   |  8-10
--   2   |  80+
--   3   |  400+
--   4   |  2000+

-- 如果某层级为0，需要重新生成
```

## 📊 性能验证

### 验证响应时间

#### V1 (对比基准)
```bash
# 访问 http://localhost:8000/advisor/
# 输入：How to handle workplace stress?
# 记录从提交到看到内容的时间
# 预期：15-25秒
```

#### V2 Guided Mode
```bash
# 访问 http://localhost:8000/advisor/v2/
# 选择 Guided 模式
# 输入：How to handle workplace stress?
# 记录从提交到看到第一批选项的时间
# 预期：2-4秒 ✅
```

#### V2 Quick Mode
```bash
# 切换到 Quick Answer 模式
# 输入：How to handle workplace stress?
# 记录总响应时间
# 预期：8-12秒（比V1稍快）
```

## 🎯 生产环境部署建议

### 1. 使用Redis存储会话

**安装Redis：**
```bash
# Windows (使用WSL或下载Windows版本)
# Linux
sudo apt-get install redis-server

# macOS
brew install redis

# 启动Redis
redis-server
```

**修改 views_v2.py：**
```python
import redis
import json

# 初始化Redis客户端
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# 替换内存存储
def save_session(session_id, data):
    redis_client.setex(
        f"session:{session_id}",
        3600,  # 1小时过期
        json.dumps(data)
    )

def get_session(session_id):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None
```

### 2. 配置Nginx反向代理

```nginx
# /etc/nginx/sites-available/wuxing_advisor
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/agent/static/;
    }
}
```

### 3. 使用Gunicorn部署

```bash
# 安装Gunicorn
pip install gunicorn

# 启动（生产环境）
cd agent
gunicorn wu_xing_advisor.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120
```

### 4. 配置环境变量

```bash
# .env.production
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 数据库配置
DB_HOST=your-db-host
DB_USER=your-db-user
DB_PASSWORD=your-secure-password
DB_NAME=decision_app_kb

# API配置
SILICON_FLOW_API_KEY=your-api-key

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 📈 监控和日志

### 添加日志记录

在 `settings.py` 中添加：
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/advisor_v2.log',
        },
    },
    'loggers': {
        'advisor': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 性能监控

```python
# 在 views_v2.py 添加
import time
import logging

logger = logging.getLogger('advisor')

def start_conversation(request):
    start_time = time.time()
    
    # ...原有代码...
    
    duration = time.time() - start_time
    logger.info(f"start_conversation took {duration:.2f}s")
    
    return response
```

## ✅ 部署检查清单

- [ ] V1版本正常运行
- [ ] 知识库数据已生成（至少包含L1-L4）
- [ ] API密钥配置正确
- [ ] 新文件已添加（views_v2.py, index_v2.html）
- [ ] URL配置已更新
- [ ] Django服务器已重启
- [ ] 能访问 /advisor/v2/ 页面
- [ ] Guided Mode 测试通过
- [ ] Quick Mode 测试通过
- [ ] 响应时间符合预期（<5秒首次响应）
- [ ] （可选）Redis已配置
- [ ] （可选）日志记录已配置
- [ ] （可选）生产环境已部署

## 🎉 部署成功！

如果所有测试通过，恭喜你成功部署了V2版本！

**下一步：**
1. 体验两个版本的差异
2. 根据实际需求选择合适的模式
3. 查看 `V2_ITERATION_README.md` 了解更多优化建议
4. 根据用户反馈继续改进

**技术支持：**
- 查看 `V2_ITERATION_README.md` 获取详细文档
- 检查控制台日志了解错误详情
- 参考"故障排查"部分解决常见问题
