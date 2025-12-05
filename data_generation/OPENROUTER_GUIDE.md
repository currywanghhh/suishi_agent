# OpenRouter 集成指南

## 概述

数据生成脚本现已支持 OpenRouter 作为 LLM 提供商，可以使用 Google Gemini 2.0 Flash 等模型生成知识库数据。

## 配置步骤

### 1. 获取 OpenRouter API Key

1. 访问 [OpenRouter](https://openrouter.ai)
2. 注册/登录账户
3. 进入 [API Keys](https://openrouter.ai/keys) 页面
4. 创建新的 API Key
5. 复制 API Key

### 2. 配置环境变量

编辑 `data_generation/.env` 文件：

```env
# 选择使用 OpenRouter
MODEL_PROVIDER="openrouter"

# 设置 OpenRouter API Key
OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxxxxxxxxx"

# 选择模型（推荐使用免费的 Gemini 2.0 Flash）
OPENROUTER_MODEL="google/gemini-2.0-flash-exp:free"
```

### 3. 可用模型

OpenRouter 支持多种模型：

#### 免费模型
- `google/gemini-2.0-flash-exp:free` - Gemini 2.0 Flash (推荐)
- `google/gemini-flash-1.5` - Gemini 1.5 Flash
- `meta-llama/llama-3.2-3b-instruct:free` - Llama 3.2 3B

#### 付费模型
- `google/gemini-pro-1.5` - Gemini 1.5 Pro (更强大)
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet
- `openai/gpt-4o` - GPT-4o

查看完整模型列表：https://openrouter.ai/models

### 4. 测试连接

运行测试脚本验证配置：

```bash
cd data_generation
python test_openrouter.py
```

成功输出示例：
```
✅ API 调用成功!
📝 模型响应:
[生成的内容...]
📊 Token 使用统计:
   Prompt tokens: 45
   Completion tokens: 120
   Total tokens: 165
```

## 使用方法

### 生成知识库结构

使用 OpenRouter + Gemini 生成完整的知识库：

```bash
cd data_generation

# 1. 创建数据库表结构并生成 L1 领域
python create_knowledge_base.py

# 2. 为特定 L1 ID 生成子层级 (L2, L3, L4)
python generate_single_level.py --level 2 --parent 1

# 3. 批量生成所有层级
python generate_sub_levels.py
```

### 生成 L4 内容

为用户意图生成详细的五行建议内容：

```bash
python generate_l4_content.py
```

## 优势对比

| 特性 | Silicon Flow | OpenRouter | Ollama |
|------|--------------|-----------|--------|
| **免费额度** | 有限 | Gemini 免费模型 | 完全免费 |
| **模型选择** | 中文模型优秀 | 最多选择 | 需本地部署 |
| **响应速度** | 快 | 快 | 取决于硬件 |
| **无需硬件** | ✅ | ✅ | ❌ |
| **国内访问** | ✅ | 需代理 | ✅ |

## 成本估算

使用 Gemini 2.0 Flash (免费版本):
- **完全免费**，有速率限制
- 适合开发和小规模数据生成

使用 Gemini 1.5 Pro (付费):
- Input: $0.00125 / 1K tokens
- Output: $0.005 / 1K tokens
- 生成 1000 条 L4 内容约需 $2-5

## 切换回 Silicon Flow

如需切换回原来的 Silicon Flow：

```env
# 修改 .env 文件
MODEL_PROVIDER="silicon_flow"
```

## 故障排查

### 问题: API Key 无效
```
❌ 错误: 401 Unauthorized
```
**解决**: 检查 API Key 是否正确，确认账户状态

### 问题: 模型不存在
```
❌ 错误: Model not found
```
**解决**: 访问 https://openrouter.ai/models 确认模型名称

### 问题: 超出配额
```
❌ 错误: 429 Too Many Requests
```
**解决**: 
- 免费模型有速率限制，等待后重试
- 考虑升级到付费模型
- 在 `config.py` 中增加 `delay_between_calls`

### 问题: 网络连接失败
```
❌ 请求错误: Connection error
```
**解决**: 
- 国内用户需配置代理访问 OpenRouter
- 或使用 Silicon Flow (国内服务)

## 性能优化

### 1. 调整延迟
```python
# config.py
API_CONFIG = {
    "delay_between_calls": 2,  # 增加到 2 秒避免速率限制
}
```

### 2. 批量生成
```bash
# 并行生成多个 L1 的子层级
for i in {1..10}; do
    python generate_single_level.py --level 2 --parent $i &
done
wait
```

### 3. 错误恢复
```bash
# 设置不在错误时停止
python generate_sub_levels.py --continue-on-error
```

## 更多信息

- OpenRouter 文档: https://openrouter.ai/docs
- Gemini API 文档: https://ai.google.dev/docs
- 项目主文档: [../README.md](../README.md)
