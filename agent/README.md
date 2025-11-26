# 东方命理决策应用 - 知识库生成系统

## 📱 项目概述

本项目为一款面向北美市场的iOS订阅制应用构建知识库系统。该应用结合**东方命理学**（五行理论、星座、占卜）与**实用决策建议**，帮助有选择困难症的用户在日常生活中做出自信、愉快的决定。

### 🎯 目标用户
- **地域**：北美市场（美国、加拿大）
- **年龄**：18-45岁
- **兴趣**：关注YouTube/Instagram上的星座、东方命理、决策类内容
- **痛点**：在生活各领域面临选择困难，需要指导和建议

### 🗂️ 知识库架构

本系统自动生成四层级知识图谱：

1. **L1 - 领域 (Domain)**：生活的主要类别（例如：职业发展、爱情关系、家庭生活等）
2. **L2 - 场景 (Scenario)**：领域内的具体情况（例如：求职面试、约会交友等）
3. **L3 - 子场景 (Sub-scenario)**：场景中的细分情境（例如：第一次约会准备、面试着装选择等）
4. **L4 - 意图 (User Intention)**：用户的具体问题或目标（例如："第一次约会应该穿什么？"）

## 🚀 功能特性

- ✅ **AI驱动生成**：利用大模型（硅基流动API或本地Ollama）自动生成知识库内容
- ✅ **层级关系管理**：自动建立四层级的父子关系
- ✅ **灵活可配置**：可控制每层级生成的数量（L1最多100条）
- ✅ **去重机制**：自动检测并跳过已存在的条目
- ✅ **MySQL存储**：结构化存储，便于应用集成和查询

## 📋 前置要求

### 1. 环境准备
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- 硅基流动API密钥（或本地Ollama环境）

### 2. 数据库设置

首先创建数据库和表结构：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS decision_app_kb DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE decision_app_kb;

-- 创建知识库表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level INT NOT NULL COMMENT '层级: 1=领域, 2=场景, 3=子场景, 4=意图',
    parent_id INT NULL COMMENT '父级ID，L1层级为NULL',
    name VARCHAR(255) NOT NULL COMMENT '名称（英文）',
    description_en TEXT COMMENT '英文描述',
    description_cn TEXT COMMENT '中文描述（可选）',
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

### 3. 安装Python依赖

```bash
pip install mysql-connector-python python-dotenv requests
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# MySQL数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=decision_app_kb

# 硅基流动API配置
SILICON_FLOW_API_KEY=sk-your-api-key-here
```

## 🎬 使用指南

### 方式一：完整批量生成（推荐）

适合首次生成或需要一次性生成所有层级的场景。

#### 步骤1：生成L1领域（最多100条）

```bash
python create_knowledge_base.py
```

**该脚本将：**
1. 调用大模型，根据产品定位生成全面的L1领域列表（最多100条）
2. 为每个领域生成符合目标用户的英文描述
3. 将领域和描述存入MySQL的 `knowledge_base` 表

**预期输出：**
```
正在调用大模型生成L1领域列表（最多100条）...
成功生成23个L1领域: ['Career & Professional Development', 'Love & Romance', ...]

成功连接到数据库。
正在处理领域: Career & Professional Development...
  -> 正在为 'Career & Professional Development' 生成描述...
  -> 成功插入 'Career & Professional Development' (ID: 1).
...
```

#### 步骤2：批量生成L2、L3、L4（一键完成）

在L1成功生成后，运行此脚本一次性构建完整的知识图谱：

```bash
python generate_sub_levels.py
```

**该脚本将按顺序执行：**
1. **生成L2场景**：为每个L1领域生成场景（默认10个/领域）
2. **生成L3子场景**：为每个L2场景生成子场景（默认8个/场景）
3. **生成L4用户意图**：为每个L3子场景生成意图（默认6个/子场景）

**可在脚本顶部调整数量：**
```python
# 在 generate_sub_levels.py 的 if __name__ == "__main__" 部分
L2_MAX_PER_L1 = 10   # 调整为您需要的数量
L3_MAX_PER_L2 = 8
L4_MAX_PER_L3 = 6
```

**注意事项：**
- ⏱️ 执行时间较长，取决于L1的数量（可能需要数小时）
- 🔄 脚本包含API调用延迟，避免速率限制
- 💾 可随时中断，再次运行时会自动跳过已存在的条目
- 📊 建议先观察L1和L2生成的质量，再决定是否继续

### 方式二：单层级生成（灵活控制）

适合只想生成或重新生成某一个特定层级的场景。

#### 单独生成L2场景

```bash
python generate_single_level.py --level 2 --max 10
```

#### 单独生成L3子场景

```bash
python generate_single_level.py --level 3 --max 8
```

#### 单独生成L4用户意图

```bash
python generate_single_level.py --level 4 --max 6
```

**参数说明：**
- `--level`: 必填，要生成的层级（2、3或4）
- `--max`: 可选，每个父项生成的子项数量（不指定则使用配置文件默认值）

**使用场景举例：**
- 只想为已有的L1生成L2，但不生成L3和L4
- L2已经生成完，现在想单独生成L3
- L3生成时出错了，想重新生成L3但不影响其他层级

### 方式三：指定L1领域生成（精准控制）⭐

**最灵活的方式**：为某个特定的L1领域生成完整的子树（L2→L3→L4）。

#### 第一步：查看所有L1领域

```bash
python generate_for_l1.py --list
```

输出示例：
```
📋 当前数据库中的所有L1领域（共6个）：
======================================================================
  ID:   1 | Career & Professional Development
  ID:   2 | Love & Romantic Relationships
  ID:   3 | Family & Parenting
  ID:   4 | Health & Wellness
  ID:   5 | Financial Planning & Wealth
  ID:   6 | Personal Growth & Self-Discovery
======================================================================
```

#### 第二步：为指定L1生成子树

**通过ID指定：**
```bash
# 为ID为1的L1领域生成完整子树（L2→L3→L4）
python generate_for_l1.py --l1 1
```

**通过名称模糊搜索（不区分大小写）：**
```bash
# 自动匹配包含"Career"的L1领域
python generate_for_l1.py --l1 "Career"

# 自动匹配包含"Love"的L1领域
python generate_for_l1.py --l1 "Love"
```

#### 高级用法

**自定义各层级数量：**
```bash
# 为"Career"生成：15个L2、10个L3/L2、8个L4/L3
python generate_for_l1.py --l1 "Career" --max-l2 15 --max-l3 10 --max-l4 8
```

**只生成部分层级：**
```bash
# 只生成L2场景，不生成L3和L4
python generate_for_l1.py --l1 1 --skip-l3 --skip-l4

# 只生成L2和L3，跳过L4
python generate_for_l1.py --l1 1 --skip-l4

# 假设L2已存在，只生成L3和L4
python generate_for_l1.py --l1 1 --skip-l2
```

**完整参数说明：**
- `--list`: 列出所有L1领域
- `--l1 <ID或名称>`: 指定L1领域（必填）
- `--max-l2 <数量>`: L2场景数量（默认10）
- `--max-l3 <数量>`: 每个L2生成的L3数量（默认8）
- `--max-l4 <数量>`: 每个L3生成的L4数量（默认6）
- `--skip-l2`: 跳过L2生成
- `--skip-l3`: 跳过L3生成
- `--skip-l4`: 跳过L4生成

**使用场景举例：**
- 🎯 **重点领域深度开发**：为"Career"领域生成更多内容（20个L2场景）
- 🔄 **单领域重新生成**：删除某个L1的所有子节点后重新生成
- 📊 **逐步验证质量**：先为一个L1生成L2，检查质量后再继续生成L3、L4
- 🧪 **AB测试不同参数**：为不同L1使用不同的生成数量配置

### 方式四：生成L4详细内容

生成L4意图的详细内容（五行洞察、行动指南、沟通话术、能量调和）：

```bash
python generate_l4_content.py
```

该脚本会自动查找尚未生成内容的L4条目，并调用大模型生成结构化内容存入 `l4_content` 表。

### 方式五：测试交互

模拟用户提问并测试内容检索：

```bash
python test_l4_interaction.py
```

在终端输入用户问题（英文），系统将：
1. 搜索最匹配的L4意图
2. 展示生成的详细建议内容

### 步骤3：验证数据

查询数据库确认生成结果：

```sql
-- 查看每层级的数量
SELECT level, COUNT(*) as count FROM knowledge_base GROUP BY level;

-- 查看L1领域
SELECT id, name, description_en FROM knowledge_base WHERE level = 1 LIMIT 10;

-- 查看某个L1领域下的L2场景
SELECT id, name FROM knowledge_base WHERE level = 2 AND parent_id = 1;

-- 查看完整的层级关系（某个L1的树状结构）
SELECT 
    l1.name as L1_Domain,
    l2.name as L2_Scenario,
    l3.name as L3_SubScenario,
    l4.name as L4_Intention
FROM knowledge_base l1
LEFT JOIN knowledge_base l2 ON l2.parent_id = l1.id AND l2.level = 2
LEFT JOIN knowledge_base l3 ON l3.parent_id = l2.id AND l3.level = 3
LEFT JOIN knowledge_base l4 ON l4.parent_id = l3.id AND l4.level = 4
WHERE l1.level = 1 AND l1.id = 1
LIMIT 20;
```

## 🛠️ 高级配置

### 方法一：使用配置文件（推荐）

编辑 `config.py` 文件，可以集中管理所有参数：

```python
# L1 领域生成配置
L1_CONFIG = {
    'max_domains': 100,           # 调整L1数量上限
    'temperature': 0.7,
}

# L2 场景生成配置
L2_CONFIG = {
    'max_per_parent': 10,         # 每个L1领域生成的L2数量
    'temperature': 0.7,
}

# L3 子场景生成配置
L3_CONFIG = {
    'max_per_parent': 8,          # 每个L2场景生成的L3数量
}

# L4 用户意图生成配置
L4_CONFIG = {
    'max_per_parent': 6,          # 每个L3子场景生成的L4数量
}
```

### 方法二：直接修改脚本

#### 调整L1生成数量

编辑 `create_knowledge_base.py`，修改函数调用：

```python
# 在 setup_database() 函数中
l1_domains = generate_l1_domains(max_domains=100)  # 修改这里的数字
```

#### 调整L2-L4批量生成数量

编辑 `generate_sub_levels.py`，修改主程序入口的配置区域：

```python
if __name__ == "__main__":
    # 配置区域
    L2_MAX_PER_L1 = 10   # 修改这里
    L3_MAX_PER_L2 = 8    # 修改这里
    L4_MAX_PER_L3 = 6    # 修改这里
```

### 调整API调用参数

编辑 `config.py` 的API配置：

```python
API_CONFIG = {
    'delay_between_calls': 1,     # 增加延迟避免限流
    'timeout': 120,               # 调整超时时间
    'max_tokens': 2048            # 调整token上限
}

### 切换到本地Ollama

如果您希望使用本地Ollama而非硅基流动API：

1. 确保Ollama服务正在运行
2. 修改两个脚本中的 `call_llm` 函数，调整API URL和请求格式
3. 参考Ollama官方文档进行配置

## 📊 项目结构

```
agent/
├── create_knowledge_base.py    # ⭐ L1领域生成脚本
├── generate_sub_levels.py      # ⭐ L2-L4批量生成脚本（三个独立函数）
├── generate_single_level.py    # 🔧 单层级生成工具
├── generate_for_l1.py           # 🎯 指定L1领域生成工具（推荐）
├── config.py                    # ⚙️ 集中配置文件
├── .env                         # 🔐 环境变量配置（需自行创建）
├── .env.example                 # 📝 环境变量示例
├── README.md                    # 📖 本文档
└── requirements.txt             # 📦 Python依赖
```

### 脚本功能对比

| 脚本 | 功能 | 适用场景 |
|------|------|----------|
| `create_knowledge_base.py` | 生成L1领域 | 初始化知识库 |
| `generate_sub_levels.py` | 批量生成全部L2→L3→L4 | 一次性生成所有内容 |
| `generate_single_level.py` | 生成指定层级（L2/L3/L4） | 重新生成某个层级 |
| `generate_for_l1.py` | 为指定L1生成子树 | **精准控制，推荐使用** ⭐ |

## ❓ 常见问题

**Q: 为什么L1只生成了几个领域，而不是100个？**  
A: 大模型会根据实际需求生成合理数量的领域。100是上限，实际生成数量通常在15-30之间，这已经能覆盖大部分用户需求场景。

**Q: 我只想为某个特定的L1领域（比如"Career"）生成内容，怎么做？**  
A: 使用 `generate_for_l1.py` 脚本！
```bash
# 查看所有L1领域
python generate_for_l1.py --list

# 为指定L1生成完整子树
python generate_for_l1.py --l1 "Career"
```

**Q: 可以重新生成某一层级吗？**  
A: 可以。删除数据库中对应层级的数据后重新运行脚本即可。
```sql
-- 删除所有L2数据
DELETE FROM knowledge_base WHERE level = 2;

-- 或删除某个L1下的所有L2
DELETE FROM knowledge_base WHERE level = 2 AND parent_id = 1;
```

**Q: 如何为不同的L1领域设置不同的生成数量？**  
A: 使用 `generate_for_l1.py` 的 `--max-l2/l3/l4` 参数：
```bash
# 为"Career"生成更多内容
python generate_for_l1.py --l1 "Career" --max-l2 20 --max-l3 12

# 为"Health"生成较少内容
python generate_for_l1.py --l1 "Health" --max-l2 8 --max-l3 6
```

**Q: 如何提高生成内容的质量？**  
A: 可以在提示词中增加更多产品细节，或调整 `temperature` 参数（降低以获得更稳定的输出，提高以获得更多样化的内容）。

**Q: 生成过程中断了怎么办？**  
A: 脚本有去重机制，直接重新运行即可，已生成的内容会被跳过。

**Q: 如何查看某个L1领域下有哪些L2场景？**  
A: 使用SQL查询：
```sql
-- 查看ID为1的L1领域下的所有L2
SELECT id, name FROM knowledge_base WHERE level = 2 AND parent_id = 1;

-- 查看"Career"领域下的所有L2
SELECT l2.id, l2.name 
FROM knowledge_base l2
JOIN knowledge_base l1 ON l2.parent_id = l1.id
WHERE l1.level = 1 AND l1.name LIKE '%Career%' AND l2.level = 2;
```

## 📞 技术支持

如有问题，请检查：
1. `.env` 配置是否正确
2. MySQL数据库是否已创建并可连接
3. API密钥是否有效且有足够额度
4. Python依赖是否全部安装

## 📝 版本历史

- **v1.0** (2025-11-17)
  - 初始版本
  - 支持四层级知识图谱自动生成
  - 支持硅基流动API
  - L1最多生成100条

## 📄 许可证

本项目仅供内部使用。
