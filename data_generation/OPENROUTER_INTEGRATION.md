# OpenRouter + Gemini 集成完成 ✅

## 更改摘要

已成功为数据生成脚本添加 OpenRouter 支持，现在可以使用 Google Gemini 2.0 Flash 等模型生成知识库数据。

## 修改的文件

### 1. 配置文件
- **`.env`** - 添加 OpenRouter 配置项
  - `OPENROUTER_API_KEY` - OpenRouter API 密钥
  - `MODEL_PROVIDER` - 选择模型提供商 (silicon_flow/openrouter/ollama)
  - `OPENROUTER_MODEL` - 指定使用的 OpenRouter 模型

- **`config.py`** - 添加模型提供商配置
  - 新增 `MODEL_PROVIDERS` 字典，包含各提供商的配置

### 2. 核心脚本
- **`generate_single_level.py`** - 层级生成脚本
  - 支持动态选择 API 提供商
  - 更新 `call_llm()` 函数支持多个 API
  - 添加 OpenRouter 特定的请求头

- **`generate_l4_content.py`** - L4 内容生成脚本
  - 同样支持多提供商切换
  - 保持与其他脚本一致的 API 调用方式

- **`create_knowledge_base.py`** - 知识库初始化脚本
  - 更新配置加载逻辑
  - 支持 OpenRouter API 调用

### 3. 新增文件
- **`test_openrouter.py`** - OpenRouter 连接测试工具
  - 验证 API Key 有效性
  - 测试模型响应
  - 显示 token 使用统计

- **`quick_demo_openrouter.py`** - 快速演示脚本
  - 演示如何使用 OpenRouter 生成数据
  - 生成少量示例数据验证配置

- **`OPENROUTER_GUIDE.md`** - 详细使用指南
  - 配置步骤
  - 可用模型列表
  - 故障排查
  - 成本估算

## 快速开始

### 1. 配置 OpenRouter

编辑 `data_generation/.env`:
```env
MODEL_PROVIDER="openrouter"
OPENROUTER_API_KEY="sk-or-v1-your-key-here"
OPENROUTER_MODEL="google/gemini-2.0-flash-exp:free"
```

### 2. 测试连接
```bash
cd data_generation
python test_openrouter.py
```

### 3. 快速演示
```bash
python quick_demo_openrouter.py
```

### 4. 生成完整数据
```bash
# 生成知识库结构
python create_knowledge_base.py

# 生成子层级
python generate_sub_levels.py

# 生成 L4 详细内容
python generate_l4_content.py
```

## 支持的模型

### 免费模型（推荐用于开发）
- **google/gemini-2.0-flash-exp:free** ⭐ 推荐
- google/gemini-flash-1.5
- meta-llama/llama-3.2-3b-instruct:free

### 付费模型（生产环境）
- google/gemini-pro-1.5 - 更强大的 Gemini
- anthropic/claude-3.5-sonnet - Claude 3.5
- openai/gpt-4o - GPT-4o

查看完整列表: https://openrouter.ai/models

## 优势

✅ **免费 Gemini 模型** - 开发阶段零成本
✅ **多模型选择** - 可随时切换不同模型
✅ **统一接口** - 兼容 OpenAI API 格式
✅ **灵活配置** - 通过环境变量轻松切换
✅ **向后兼容** - 保持对 Silicon Flow 的支持

## 切换提供商

只需修改 `.env` 文件中的 `MODEL_PROVIDER`:

```env
# 使用 OpenRouter (Gemini)
MODEL_PROVIDER="openrouter"

# 或使用 Silicon Flow (中文模型优秀)
MODEL_PROVIDER="silicon_flow"

# 或使用本地 Ollama (完全免费，需硬件)
MODEL_PROVIDER="ollama"
```

## 技术细节

### API 适配
所有脚本的 `call_llm()` 函数现已支持:
- 动态 API URL 选择
- 特定提供商的请求头
- JSON 模式兼容性检查
- 统一的错误处理

### 配置加载
```python
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "silicon_flow")

if MODEL_PROVIDER == "openrouter":
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM_MODEL = os.getenv("OPENROUTER_MODEL")
```

### OpenRouter 特定头
```python
if MODEL_PROVIDER == "openrouter":
    headers["HTTP-Referer"] = "https://github.com/..."
    headers["X-Title"] = "Wu Xing Decision Advisor"
```

## 文档

- 📖 [OpenRouter 使用指南](OPENROUTER_GUIDE.md) - 详细配置和使用说明
- 📖 [主 README](README.md) - 项目总体文档
- 📖 [快速开始](QUICKSTART.md) - 快速上手指南

## 注意事项

1. **国内访问**: OpenRouter 可能需要代理访问
2. **速率限制**: 免费模型有请求频率限制，建议设置 `delay_between_calls`
3. **API Key 安全**: 不要提交 `.env` 文件到 Git

## 测试状态

- ✅ 配置文件更新完成
- ✅ 核心脚本适配完成
- ✅ 测试工具创建完成
- ⏳ 待用户提供 API Key 后测试实际调用

## 下一步

1. 获取 OpenRouter API Key: https://openrouter.ai/keys
2. 更新 `.env` 文件中的 `OPENROUTER_API_KEY`
3. 运行 `python test_openrouter.py` 验证配置
4. 开始生成数据！

---

**更新日期**: 2025-11-27
**版本**: v1.1.0 - OpenRouter 集成
