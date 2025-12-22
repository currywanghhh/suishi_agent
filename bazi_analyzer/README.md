# 🔮 八字算命机

基于 MCP (Model Context Protocol) 的命理分析工具，输入生辰八字，输出详细的排盘报告。

---
🚀 使用步骤
步骤 1：配置 API Key（可选）
如果要用大模型分析：


步骤 2：启动服务

cd G:\泽全实习\suishi_agent\bazi_analyzer\python app.py

步骤 3：访问界面
浏览器打开：http://127.0.0.1:5000

步骤 4：输入信息

## ✨ 功能特性

- ✅ 完整八字排盘（年月日时四柱）
- ✅ 五行统计与分析
- ✅ 大运计算（人生运势阶段）
- ✅ 神煞解读
- ✅ 十神关系分析
- ✅ 生成 JSON 格式完整数据
- ✅ 美化的终端输出

---

## 📦 安装依赖

### 1. Node.js 环境（必须 v22+）

```bash
# 检查版本
node --version

# 如果版本低于 v22，请升级
# 下载：https://nodejs.org/
```

### 2. 安装 bazi-mcp 工具

```bash
npm install -g bazi-mcp
```

### 3. Python 环境

```bash
# 无需额外安装，使用 Python 标准库
```

---

## 🚀 使用方法

### 方式一：直接运行示例

```bash
cd bazi_analyzer
python bazi_fortune_teller.py
```

**输出示例：**
```
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
           八字命理分析报告
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟

============================================================
📋 基本信息
============================================================
性别：男
阳历：1998年7月31日 14:10:00
农历：农历戊寅年六月初九辛未时
生肖：虎 🐯
八字：戊寅 己未 己卯 辛未
日主：己 (你的核心五行)

============================================================
🏛️  四柱详解（年月日时）
============================================================
...
```

---

### 方式二：交互式输入

修改 `bazi_fortune_teller.py` 最后几行：

```python
if __name__ == "__main__":
    # 取消注释这一行
    main()
```

然后运行：

```bash
python bazi_fortune_teller.py
```

会提示你输入：
```
请输入生辰信息：
📅 出生日期（格式：1998-07-31）：
⏰ 出生时间（格式：14:10）：
👤 性别（男/女）：
```

---

### 方式三：作为模块调用

```python
from bazi_fortune_teller import BaziFortuneTeller

teller = BaziFortuneTeller()

# 生成报告
teller.generate_full_report(
    birth_date="1990-01-01",
    birth_time="12:00",
    gender=1,  # 1=男, 0=女
    timezone="+08:00"
)
```

---

## 📁 文件说明

```
bazi_analyzer/
├── README.md                    # 使用文档（本文件）
├── mcp_client.py                # MCP 客户端（底层通信）
├── bazi_fortune_teller.py       # 八字分析器（主程序）
└── bazi_result_YYYYMMDD.json    # 自动生成的排盘结果
```

---

## 📊 输出内容说明

### 1. 基本信息
- 性别、阳历、农历
- 生肖、八字、日主

### 2. 四柱详解
- 年柱、月柱、日柱、时柱
- 每柱的天干、地支、五行、阴阳
- 藏干、纳音、星运

### 3. 五行分析
```
五行数量统计：
  木 ███░░ 3个 (生长、仁慈) - 绿色/东方
  火 ░░░░░ 0个 (热情、礼貌) - 红色/南方
  土 ████░ 4个 (稳重、诚信) - 黄色/中央
  金 █░░░░ 1个 (刚毅、义气) - 白色/西方
  水 ░░░░░ 0个 (智慧、灵活) - 黑色/北方

✨ 五行特征：
  最旺：土 (4个)
  缺失：水、火
```

### 4. 大运分析
```
运势列表：
   1. 庚申 (2001-2010年, 4-13岁) - 伤官
   2. 辛酉 (2011-2020年, 14-23岁) - 食神
👉 3. 壬戌 (2021-2030年, 24-33岁) - 正财  ← 当前大运
   4. 癸亥 (2031-2040年, 34-43岁) - 偏财
```

### 5. 神煞
```
年柱：国印、亡神
月柱：天德合、月德合、天乙贵人...
日柱：天德合、月德合、桃花...
时柱：天乙贵人、太极贵人...
```

### 6. JSON 完整数据
自动保存到 `bazi_result_YYYYMMDD.json`，包含：
- 所有天干地支详情
- 十神关系
- 纳音五行
- 神煞完整列表
- 大运详细数据

---

## 🎮 好玩的扩展想法

### 1. 批量分析
```python
# 分析多个人的八字
people = [
    ("张三", "1990-01-01", "12:00", 1),
    ("李四", "1995-05-15", "08:30", 0),
]

for name, date, time, gender in people:
    print(f"\n分析 {name} 的命盘：")
    teller.generate_full_report(date, time, gender)
```

### 2. 合婚分析
```python
# 比较两个人的八字五行互补性
def marriage_analysis(bazi1, bazi2):
    # 分析五行是否互补
    # 分析大运是否同步
    # 分析生肖相合
    pass
```

### 3. 流年运势
```python
# 计算2025年的运势
def yearly_fortune(bazi_result, year=2025):
    # 根据流年天干地支
    # 与命盘的相互作用
    pass
```

### 4. 起名分析
```python
# 根据八字缺失推荐名字
def name_suggestion(bazi_result):
    # 分析五行缺失
    # 推荐补充的字
    pass
```

### 5. 可视化图表
```python
# 生成五行雷达图
import matplotlib.pyplot as plt

def plot_wuxing(bazi_result):
    # 五行数量 → 雷达图
    pass
```

---

## 🐛 常见问题

### 1. MCP 调用失败

**问题：** `MCP 服务器无响应`

**解决：**
```bash
# 检查 bazi-mcp 是否安装
npx bazi-mcp --help

# 如果没有，重新安装
npm install -g bazi-mcp

# 检查 Node.js 版本（必须 v22+）
node --version
```

### 2. 编码错误

**问题：** `UnicodeDecodeError: 'gbk' codec...`

**解决：** 已在代码中添加 `encoding='utf-8'`，如果还有问题：
```python
# 在 mcp_client.py 开头添加
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### 3. 超时问题

**问题：** MCP 调用超过 15 秒

**解决：** 增加超时时间
```python
# 在 mcp_client.py 中修改
stdout, stderr = process.communicate(input=request_json + "\n", timeout=30)
```

---

## 📚 技术原理

### MCP 通信流程
```
Python                          Node.js
  │                               │
  ├──── subprocess.Popen() ───────┤ 启动进程
  │                               │
  ├──── stdin 发送请求 ────────────┤ 接收请求
  │    (JSON-RPC 2.0)             │
  │                               │
  │                               ├─ 计算八字
  │                               ├─ 计算大运
  │                               └─ 计算神煞
  │                               │
  │ ◄──── stdout 返回结果 ────────┤ 返回 JSON
  │    (嵌套 JSON 格式)           │
  │                               │
  └─ 解析 result.content[0].text  │
     得到八字数据                 │
```

---

## 🎯 下一步计划

- [ ] 添加 Web 界面（Flask/Streamlit）
- [ ] 实现合婚分析功能
- [ ] 添加流年运势计算
- [ ] 生成 PDF 报告
- [ ] 五行可视化图表
- [ ] 多语言支持（英文排盘）

---

## 📄 许可证

MIT License - 仅供学习和娱乐使用，请勿用于商业算命！

---

## 🙏 致谢

- [bazi-mcp](https://www.npmjs.com/package/bazi-mcp) - 提供八字计算功能
- MCP Protocol - 统一的工具调用协议

---

**免责声明：** 本工具仅供娱乐和学习命理知识使用，不构成任何人生建议。人生由自己掌握！🌟
