# 八字算命机 - 配置说明

## 环境变量配置

### Silicon Flow API Key（可选）

如果你想使用**大模型分析命盘**功能，需要配置 Silicon Flow API Key。

#### 1. 获取 API Key

访问：https://siliconflow.cn/
- 注册账号
- 获取 API Key

#### 2. 设置环境变量

**Windows (PowerShell):**
```powershell
# 临时设置（当前会话有效）
$env:SILICON_FLOW_API_KEY="你的API_KEY"

# 永久设置（推荐）
[System.Environment]::SetEnvironmentVariable('SILICON_FLOW_API_KEY', '你的API_KEY', 'User')
```

**Windows (CMD):**
```cmd
set SILICON_FLOW_API_KEY=你的API_KEY
```

**Linux/Mac:**
```bash
export SILICON_FLOW_API_KEY="你的API_KEY"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export SILICON_FLOW_API_KEY="你的API_KEY"' >> ~/.bashrc
source ~/.bashrc
```

#### 3. 验证配置

启动 Flask 应用时会提示：

```
============================================================
🔮 八字算命机 Web 服务启动
============================================================

访问地址：http://127.0.0.1:5000
✅ 大模型 API 已配置    ← 成功！
```

如果看到：
```
⚠️  大模型 API 未配置（可选功能）
```
说明环境变量未生效，请重新设置。

---

## 使用说明

### 基础功能（无需 API Key）

- ✅ 八字排盘
- ✅ 四柱详解
- ✅ 五行分析
- ✅ 大运计算
- ✅ 神煞展示
- ✅ 原始 JSON 数据查看/下载

### 高级功能（需要 API Key）

- 🤖 大模型命理分析
  - 性格特征分析
  - 五行格局分析
  - 事业财运倾向
  - 人际关系与健康
  - 大运流年建议

---

## 其他配置

### 修改大模型

编辑 `app.py` 第 12 行：

```python
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"  # 改成其他模型
```

可选模型：
- `Qwen/Qwen2.5-7B-Instruct` - 快速，适合实时分析
- `Qwen/Qwen2.5-14B-Instruct` - 更准确
- `deepseek-ai/DeepSeek-V2.5` - 推理能力强

### 修改端口

编辑 `app.py` 最后一行：

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # 改成其他端口
```

---

## 常见问题

### Q1: 大模型分析很慢？

**A:** 正常现象，LLM 推理需要 5-15 秒。可以：
- 换更快的模型（Qwen2.5-7B）
- 减少分析字数（修改 prompt）

### Q2: 提示 API Key 无效？

**A:** 检查：
1. Key 是否正确复制（前后无空格）
2. 账户余额是否充足
3. API 限流问题（稍后重试）

### Q3: 不使用大模型可以吗？

**A:** 完全可以！不勾选"使用大模型分析"即可，其他功能正常使用。

---

## 技术支持

如有问题，请检查：
1. Node.js 版本 >= v22
2. `bazi-mcp` 是否正确安装
3. Flask 是否正确安装
4. 端口 5000 是否被占用
