# 🌟 Wu Xing Decision Advisor - 五行决策顾问

## 📱 项目概述

本项目为一款面向北美市场的决策建议应用，结合**东方命理学**（五行理论、星座、占卜）与**实用决策建议**，帮助有选择困难症的用户在日常生活中做出自信、愉快的决定。

### 🎯 目标用户
- **地域**：北美市场（美国、加拿大）
- **年龄**：18-45岁
- **兴趣**：关注YouTube/Instagram上的星座、东方命理、决策类内容
- **痛点**：在生活各领域面临选择困难，需要指导和建议

### 🗂️ 知识库架构

本系统包含四层级知识图谱：

1. **L1 - 领域 (Domain)**：生活的主要类别（职业发展、爱情关系、家庭生活等）
2. **L2 - 场景 (Scenario)**：领域内的具体情况（求职面试、约会交友等）
3. **L3 - 子场景 (Sub-scenario)**：场景中的细分情境（第一次约会准备、面试着装选择等）
4. **L4 - 意图 (User Intention)**：用户的具体问题或目标（"第一次约会应该穿什么？"）

---

## 📁 项目结构

```
agent/
├── data_generation/          # 📊 数据生成工具集
│   ├── create_knowledge_base.py
│   ├── generate_for_l1.py
│   ├── generate_single_level.py
│   ├── generate_sub_levels.py
│   ├── generate_l4_content.py
│   ├── test_l4_interaction.py
│   ├── config.py
│   ├── .env
│   └── README.md            # 数据生成详细文档
│
├── web_app/                 # 🌐 Web 应用
│   ├── wu_xing_advisor/     # Django 项目配置
│   ├── advisor/             # 主应用（视图、模板）
│   ├── manage.py
│   ├── .env
│   └── README.md            # Web 应用详细文档
│
├── .env                     # 共享环境变量
├── config.py                # 共享配置
├── requirements.txt         # Python 依赖
├── README.md                # 本文档
├── MATCHING_PROCESS_EXPLANATION.md  # 匹配流程详解
└── QUICKSTART.md            # 快速开始指南
```

---

## 🚀 快速开始

### 方式 1：完整流程（推荐首次使用）

1. **安装依赖**
   ```powershell
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   
   编辑根目录的 `.env` 文件：
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=你的密码
   DB_NAME=wu_xing_advisor
   SILICON_FLOW_API_KEY=你的API密钥
   ```

3. **生成知识库数据**
   ```powershell
   cd data_generation
   python create_knowledge_base.py
   python generate_for_l1.py
   python generate_l4_content.py
   ```

4. **运行 Web 应用**
   ```powershell
   cd ../web_app
   python manage.py migrate
   python manage.py runserver
   ```

5. **访问应用**
   
   打开浏览器访问：http://127.0.0.1:8000/

### 方式 2：分步操作

- **只生成数据**：查看 [`data_generation/README.md`](./data_generation/README.md)
- **只运行 Web 应用**：查看 [`web_app/README.md`](./web_app/README.md)

---

## 🎯 核心功能

### 1. 数据生成系统 (`data_generation/`)

- ✅ **AI驱动生成**：利用 LLM 自动生成知识库内容
- ✅ **层级关系管理**：自动建立四层级的父子关系
- ✅ **灵活可配置**：可控制每层级生成的数量
- ✅ **去重机制**：自动检测并跳过已存在的条目
- ✅ **详细内容生成**：为 L4 生成五行洞察、行动指南、沟通话术、能量调和

### 2. Web 应用系统 (`web_app/`)

- ✅ **层级化匹配**：L1 → L2 → L3 → L4 逐层精准匹配
- ✅ **SSE 流式输出**：实时显示匹配进度和内容
- ✅ **聊天式界面**：类似 ChatGPT 的对话体验
- ✅ **响应时间显示**：透明展示处理时长
- ✅ **示例问题**：快捷输入常见问题

---

## 📋 环境要求

- **Python**: 3.8+
- **MySQL**: 5.7+ 或 8.0+
- **API**: 硅基流动 API 密钥

---

## 📚 详细文档

### 核心文档

- **[数据生成工具文档](./data_generation/README.md)** - 如何生成和管理知识库数据
- **[Web 应用文档](./web_app/README.md)** - 如何运行和配置 Web 应用
- **[匹配流程详解](./MATCHING_PROCESS_EXPLANATION.md)** - 理解层级化匹配逻辑
- **[快速开始指南](./QUICKSTART.md)** - 5 分钟上手指南

### 数据库结构

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS wu_xing_advisor DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wu_xing_advisor;

-- 创建知识库表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level INT NOT NULL COMMENT '层级: 1=领域, 2=场景, 3=子场景, 4=意图',
    parent_id INT NULL COMMENT '父级ID，L1层级为NULL',
    name VARCHAR(255) NOT NULL COMMENT '名称（英文）',
    description_en TEXT COMMENT '英文描述',
    five_element_association VARCHAR(50) COMMENT '五行属性（可选）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_level (level),
    INDEX idx_parent_id (parent_id),
    FOREIGN KEY (parent_id) REFERENCES knowledge_base(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库四层级表';

-- 创建L4详细内容表
CREATE TABLE IF NOT EXISTS l4_content (
    id INT AUTO_INCREMENT PRIMARY KEY,
    l4_id INT NOT NULL COMMENT '关联的L4意图ID',
    five_elements_insight TEXT COMMENT '五行洞察',
    action_guide TEXT COMMENT '行动指南',
    communication_scripts TEXT COMMENT '沟通话术',
    energy_harmonization TEXT COMMENT '能量调和',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (l4_id) REFERENCES knowledge_base(id) ON DELETE CASCADE,
    UNIQUE KEY unique_l4 (l4_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='L4意图详细内容表';
```

---

## ⚙️ 环境变量配置

根目录 `.env` 文件示例：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=wu_xing_advisor

# LLM API 配置
SILICON_FLOW_API_KEY=your_api_key_here

# Django 配置（仅 web_app 需要）
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
```

---

## 🔧 开发指南

### 添加新的 L1 领域

1. 编辑 `data_generation/config.py`
2. 运行 `python generate_for_l1.py`
3. 运行 `python generate_l4_content.py` 生成详细内容

### 自定义 LLM 模型

编辑 `data_generation/` 或 `web_app/advisor/views.py` 中的模型配置：

```python
LLM_MODEL = "alibaba/Qwen2.5-7B-Instruct"  # 快速
# LLM_MODEL = "deepseek-ai/DeepSeek-R1"    # 更智能但较慢
```

### 调整生成数量

编辑 `data_generation/config.py`：

```python
L2_CONFIG = {"max_per_parent": 10}  # 每个 L1 生成 10 个 L2
L3_CONFIG = {"max_per_parent": 8}   # 每个 L2 生成 8 个 L3
L4_CONFIG = {"max_per_parent": 6}   # 每个 L3 生成 6 个 L4
```

---

## 🐛 常见问题

### Q: MySQL 类型转换错误

**错误**: `_mysql_connector.MySQLInterfaceError: Python type dict cannot be converted`

**解决**: 已在脚本中添加类型转换逻辑，确保使用最新版本的生成脚本。

### Q: LLM API 超时

**解决**:
- 检查网络连接
- 增加 `timeout` 参数（已设为 120 秒）
- 使用更稳定的 LLM 模型

### Q: Web 应用响应慢

**原因**: 需要 4 次 LLM API 调用（L1 → L2 → L3 → L4）

**优化方案**:
1. 切换到更快的模型（Qwen2.5-7B）
2. 使用向量检索替代部分 LLM 调用
3. 缓存常见问题的匹配结果

详见：[`MATCHING_PROCESS_EXPLANATION.md`](./MATCHING_PROCESS_EXPLANATION.md)

---

## 📊 项目统计

生成完整知识库后的数据量示例：

```
L1 (领域):        6 个
L2 (场景):       60 个 (每个 L1 约 10 个)
L3 (子场景):    480 个 (每个 L2 约 8 个)
L4 (意图):    2,880 个 (每个 L3 约 6 个)
─────────────────────────────
总计:        ~3,426 条知识点
```

每个 L4 包含 4 部分详细内容，共约 11,520 段文本。

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 支持与反馈

如有问题或建议，请：

1. 查看相关文档（`data_generation/README.md`、`web_app/README.md`）
2. 检查 [常见问题](#-常见问题) 部分
3. 提交 Issue 或联系项目维护者

---

## 🙏 致谢
