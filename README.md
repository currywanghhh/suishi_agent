# suishi_agent
东方命理决策应用 - Wu Xing Advisor

## 🌟 最新更新：V2 多轮对话优化版本

**重大性能提升！** 新版本通过多轮引导式对话将响应时间从 15-30秒 优化至 **2-3秒**，提升 **6-8倍性能**！

### 快速体验 V2
```bash
cd agent
python manage.py runserver
# 访问：http://localhost:8000/advisor/v2/
```

### V1 vs V2 对比

| 特性 | V1 (原版) | V2 (新版) |
|-----|----------|----------|
| 首次响应 | 15-25秒 | **2-3秒** ⚡ |
| LLM调用 | 4次 | **1次** 💰 |
| 用户体验 | 长时间等待 | **持续交互** 🎯 |
| API成本 | 高 | **降低75%** 💵 |

### 📚 详细文档

- **[V2_SUMMARY.md](agent/V2_SUMMARY.md)** - 快速概览
- **[V2_ITERATION_README.md](agent/V2_ITERATION_README.md)** - 完整技术文档 ⭐
- **[V2_DEPLOYMENT_GUIDE.md](agent/V2_DEPLOYMENT_GUIDE.md)** - 部署指南
- **[agent/README.md](agent/README.md)** - 原版知识库文档

---

## 项目简介

知识库开发系统，结合东方五行理论为用户提供决策建议。

