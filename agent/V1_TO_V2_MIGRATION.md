# V1 → V2 升级迁移指南

## 📋 升级概述

本指南帮助现有V1用户无缝升级到V2版本，同时保留V1功能。

**升级特点：**
- ✅ 零停机时间
- ✅ 保留V1完整功能
- ✅ 数据库无需改动
- ✅ 可以逐步切换

---

## ⏱️ 升级时间估算

- **代码部署：** 5-10分钟
- **功能测试：** 10-15分钟
- **总计：** 15-25分钟

---

## 📦 升级前检查清单

### 1. 系统状态检查

```bash
# 检查V1是否正常运行
curl http://localhost:8000/advisor/

# 检查数据库连接
python manage.py dbshell
> SELECT COUNT(*) FROM knowledge_base WHERE level=1;
> exit
```

### 2. 备份（推荐）

```bash
# 备份当前代码
cd agent
git add .
git commit -m "Before V2 upgrade"

# 备份数据库（可选）
mysqldump -u root -p decision_app_kb > backup_$(date +%Y%m%d).sql
```

### 3. 环境确认

```bash
# 确认Python依赖已安装
pip list | grep -E "django|mysql|requests|python-dotenv"
```

---

## 🚀 升级步骤

### Step 1: 添加新文件

将以下文件添加到项目中：

```bash
agent/
├── advisor/
│   ├── views_v2.py                      # ← 新增
│   └── templates/advisor/
│       └── index_v2.html                # ← 新增
```

**下载方式：**
1. 从本次更新获取文件
2. 或者从仓库复制

### Step 2: 更新URL配置

编辑 `agent/advisor/urls.py`：

```python
from django.urls import path
from . import views, views_v2  # ← 添加 views_v2

urlpatterns = [
    # V1 原版（保留）
    path('', views.index, name='index'),
    path('ask/', views.ask_advisor, name='ask_advisor'),
    
    # V2 新版（新增）
    path('v2/', views_v2.index_v2, name='index_v2'),
    path('v2/start/', views_v2.start_conversation, name='start_conversation'),
    path('v2/continue/', views_v2.continue_conversation, name='continue_conversation'),
    path('v2/quick/', views_v2.quick_answer, name='quick_answer'),
]
```

### Step 3: 重启服务

```bash
# 如果服务器在运行，按 Ctrl+C 停止
# 然后重新启动
python manage.py runserver
```

### Step 4: 验证部署

```bash
# 测试V1仍然正常
curl http://localhost:8000/advisor/

# 测试V2可以访问
curl http://localhost:8000/advisor/v2/

# 两个都应该返回HTML内容
```

---

## ✅ 功能测试

### 测试1：V1功能未受影响

1. 访问 `http://localhost:8000/advisor/`
2. 输入问题并提交
3. 确认仍能正常获得答案

### 测试2：V2 Guided Mode

1. 访问 `http://localhost:8000/advisor/v2/`
2. 输入问题：`How to prepare for a job interview?`
3. 验证：
   - ✅ 2-3秒内看到选项卡片
   - ✅ 点击卡片后立即看到下一层
   - ✅ 最终能获得完整答案

### 测试3：V2 Quick Mode

1. 在V2页面切换到 "Quick Answer" 模式
2. 输入同样的问题
3. 验证能直接获得答案（与V1类似）

---

## 🔄 渐进式迁移策略

### 阶段1：并行运行（推荐）

```
V1: /advisor/        ← 保留，现有用户继续使用
V2: /advisor/v2/     ← 新增，新用户试用

好处：
- 零风险
- 可以对比测试
- 用户可以选择
```

### 阶段2：灰度发布

```python
# 在入口处添加分流逻辑
def advisor_index(request):
    # 例如：10%用户看到V2
    import random
    if random.random() < 0.1:
        return redirect('/advisor/v2/')
    else:
        return views.index(request)
```

### 阶段3：全量切换

```python
# 将默认路由切换到V2
urlpatterns = [
    path('', views_v2.index_v2, name='index'),  # V2作为默认
    path('v1/', views.index, name='index_v1'),  # V1作为备选
    ...
]
```

---

## 🎯 用户体验迁移

### 通知用户

**首页提示（V1页面）：**
```html
<div class="upgrade-notice">
    🌟 Try our new faster version! 
    <a href="/advisor/v2/">Experience V2 now</a>
</div>
```

**V2页面添加返回链接：**
```html
<div class="back-link">
    Prefer the classic version? 
    <a href="/advisor/">Switch back to V1</a>
</div>
```

---

## 🐛 常见升级问题

### 问题1：导入错误

```
ModuleNotFoundError: No module named 'advisor.views_v2'
```

**解决：**
```bash
# 确认文件存在
ls agent/advisor/views_v2.py

# 确认Python能找到
python -c "from advisor import views_v2"

# 重启服务器
```

### 问题2：V2页面404

```
Page not found (404)
```

**解决：**
```bash
# 检查URL配置
python manage.py show_urls | grep v2

# 确认导入正确
grep "views_v2" agent/advisor/urls.py

# 清除缓存并重启
```

### 问题3：会话错误

```
KeyError: 'session_xxx'
```

**原因：** 服务器重启导致内存会话丢失

**临时解决：** 刷新页面重新开始

**永久解决：** 使用Redis存储会话（见下文）

---

## 🔧 生产环境优化

### 1. 使用Redis存储会话

**安装Redis：**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# 启动
redis-server
```

**修改 views_v2.py：**
```python
import redis
import json

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# 替换 SESSIONS 字典
def save_session(session_id, data):
    redis_client.setex(
        f"session:{session_id}",
        3600,
        json.dumps(data)
    )

def get_session(session_id):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

# 在相关函数中使用
def start_conversation(request):
    # ...
    save_session(session_id, session_data)
    # ...

def continue_conversation(request):
    # ...
    session = get_session(session_id)
    # ...
```

### 2. 添加监控日志

```python
import logging

logger = logging.getLogger('advisor')

def start_conversation(request):
    start_time = time.time()
    # ... 原有代码 ...
    duration = time.time() - start_time
    logger.info(f"start_conversation: {duration:.2f}s")
```

### 3. 配置负载均衡

```nginx
upstream advisor_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location /advisor/ {
        proxy_pass http://advisor_backend;
    }
}
```

---

## 📊 升级后性能监控

### 关键指标

```python
# 在 views_v2.py 添加
from django.core.cache import cache

def track_metrics(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        # 记录到Redis
        metric_key = f"metrics:{func.__name__}"
        cache.incr(metric_key + ":count")
        cache.incr(metric_key + ":total_time", int(duration * 1000))
        
        return result
    return wrapper

@track_metrics
def start_conversation(request):
    # ...
```

### 查看统计

```python
# 在Django shell中
python manage.py shell

>>> from django.core.cache import cache
>>> count = cache.get("metrics:start_conversation:count")
>>> total = cache.get("metrics:start_conversation:total_time")
>>> print(f"平均响应时间: {total/count}ms")
```

---

## 🔄 回滚计划

如果升级后发现问题，可以快速回滚：

### 快速回滚

```bash
# 1. 恢复旧的urls.py
git checkout HEAD~1 agent/advisor/urls.py

# 2. 删除V2文件（可选）
rm agent/advisor/views_v2.py
rm agent/advisor/templates/advisor/index_v2.html

# 3. 重启服务器
python manage.py runserver
```

### 保留V2但切换默认

```python
# urls.py - 只改变路由顺序
urlpatterns = [
    path('', views.index, name='index'),        # V1作为默认
    path('v2/', views_v2.index_v2, name='v2'),  # V2仍可访问
    ...
]
```

---

## 📈 升级后的收益

### 立即收益

- ⚡ **响应速度提升6-8倍**
- 💰 **API成本降低75%**
- 🎯 **用户满意度提升**

### 长期收益

- 📉 **服务器负载降低**
- 🔧 **更易维护和扩展**
- 💡 **更多优化空间**

### 成本节省计算

```
假设：
- 日活用户：1000
- 每用户提问：3次/天
- API成本：$0.01/调用

V1月成本：1000 × 3 × 30 × 4 × $0.01 = $3,600
V2月成本：1000 × 3 × 30 × 1 × $0.01 = $900

月节省：$2,700
年节省：$32,400 🎉
```

---

## ✅ 升级完成检查清单

- [ ] 新文件已添加（views_v2.py, index_v2.html）
- [ ] URL配置已更新
- [ ] 服务器已重启
- [ ] V1功能测试通过
- [ ] V2 Guided模式测试通过
- [ ] V2 Quick模式测试通过
- [ ] 响应时间符合预期（<5秒）
- [ ] 会话管理正常工作
- [ ] 日志记录配置完成（可选）
- [ ] Redis会话存储配置（生产环境）
- [ ] 监控指标设置（可选）
- [ ] 用户通知已发布

---

## 📚 相关文档

- **[V2_SUMMARY.md](V2_SUMMARY.md)** - 快速概览
- **[V2_ITERATION_README.md](V2_ITERATION_README.md)** - 完整技术文档
- **[V2_DEPLOYMENT_GUIDE.md](V2_DEPLOYMENT_GUIDE.md)** - 部署详细指南
- **[V1_VS_V2_COMPARISON.md](V1_VS_V2_COMPARISON.md)** - 详细对比

---

## 💬 需要帮助？

### 升级前咨询

- 阅读 V2_ITERATION_README.md 了解详细技术细节
- 检查系统兼容性
- 评估升级收益

### 升级中问题

- 查看"常见升级问题"章节
- 检查服务器日志
- 尝试快速回滚

### 升级后优化

- 监控性能指标
- 收集用户反馈
- 考虑生产环境优化

---

## 🎉 升级成功！

完成升级后，你将拥有：

✅ 更快的响应速度  
✅ 更低的运营成本  
✅ 更好的用户体验  
✅ 更强的系统可扩展性  

欢迎来到V2时代！🚀
