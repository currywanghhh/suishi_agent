# 📊 数据生成工具集

本文件夹包含所有用于生成和填充知识库数据的脚本。

## 📁 文件说明

### 核心生成脚本

- **`create_knowledge_base.py`** - 创建数据库表结构（knowledge_base 和 l4_content）
- **`generate_for_l1.py`** - 生成所有层级（L1→L2→L3→L4）的完整知识库
- **`generate_single_level.py`** - 单独生成指定层级（L2、L3 或 L4）
- **`generate_sub_levels.py`** - 批量生成子层级
- **`generate_l4_content.py`** - 为 L4 意图生成详细内容（五行洞察、行动指南、沟通话术、能量调和）

### 测试工具

- **`test_l4_interaction.py`** - 命令行测试工具，模拟用户查询并返回匹配的 L4 内容

### 配置文件

- **`config.py`** - 生成配置（每层生成数量、API 延迟等）
- **`.env`** - 环境变量（数据库连接、API 密钥）

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```powershell
pip install mysql-connector-python requests python-dotenv
```

### 2️⃣ 配置环境变量

编辑 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=wu_xing_advisor

# LLM API 配置
SILICON_FLOW_API_KEY=你的API密钥
```

### 3️⃣ 创建数据库表

```powershell
python create_knowledge_base.py
```

### 4️⃣ 生成知识库数据

**方式1：完整生成（推荐首次使用）**

```powershell
python generate_for_l1.py
```

这将生成所有 4 个层级的数据。

**方式2：单独生成某个层级**

```powershell
# 生成 L2 场景（每个 L1 下生成 10 个）
python generate_single_level.py --level 2 --max 10

# 生成 L3 子场景（每个 L2 下生成 8 个）
python generate_single_level.py --level 3 --max 8

# 生成 L4 意图（每个 L3 下生成 6 个）
python generate_single_level.py --level 4 --max 6
```

### 5️⃣ 生成 L4 详细内容

```powershell
python generate_l4_content.py
```

这将为所有 L4 意图生成四个部分的详细内容：
- 【五行洞察】Five Elements Insight
- 【行动指南】Action Guide
- 【沟通话术】Communication Scripts
- 【能量调和】Energy Harmonization

---

## 🧪 测试生成结果

```powershell
python test_l4_interaction.py
```

输入测试问题，查看匹配的 L4 内容。

---

## 📊 数据库结构

### `knowledge_base` 表
存储 4 层知识结构：

```
L1 (领域) → L2 (场景) → L3 (子场景) → L4 (用户意图)
```

字段：
- `id` - 主键
- `level` - 层级 (1-4)
- `parent_id` - 父节点 ID
- `name` - 名称
- `description_en` - 英文描述
- `five_element_association` - 五行关联

### `l4_content` 表
存储 L4 的详细内容：

- `l4_id` - 对应 L4 的 ID（唯一）
- `five_elements_insight` - 五行洞察
- `action_guide` - 行动指南
- `communication_scripts` - 沟通话术
- `energy_harmonization` - 能量调和

---

## ⚙️ 配置说明

编辑 `config.py` 调整生成参数：

```python
L2_CONFIG = {"max_per_parent": 10}  # 每个 L1 下生成 10 个 L2
L3_CONFIG = {"max_per_parent": 8}   # 每个 L2 下生成 8 个 L3
L4_CONFIG = {"max_per_parent": 6}   # 每个 L3 下生成 6 个 L4

API_CONFIG = {
    "delay_between_calls": 1,  # API 调用间隔（秒）
}
```

---

## ⚠️ 常见问题

### 1. MySQL 类型转换错误

**错误信息：** `_mysql_connector.MySQLInterfaceError: Python type dict cannot be converted`

**原因：** LLM 返回了结构化对象而不是简单字符串。

**解决方案：** 已在脚本中添加类型转换逻辑，会自动处理 dict/list 类型。

### 2. API 超时

**错误信息：** `Read timed out`

**解决方案：**
- 增加 `timeout` 参数（已设为 120 秒）
- 检查网络连接
- 失败的项会被记录，可以重新运行脚本

### 3. 生成内容不理想

**解决方案：**
- 调整 `config.py` 中的 `temperature` 参数
- 修改提示词（prompt）以获得更好的结果
- 切换不同的 LLM 模型

---

## 💡 最佳实践

1. **首次生成**：使用 `generate_for_l1.py` 完整生成
2. **增量更新**：使用 `generate_single_level.py` 针对性生成
3. **定期备份**：导出数据库备份
4. **监控日志**：查看生成过程中的错误和警告
5. **测试验证**：使用 `test_l4_interaction.py` 验证生成质量

---

## 📈 生成进度追踪

使用以下 SQL 查询查看生成进度：

```sql
-- 查看各层级数量
SELECT level, COUNT(*) as count 
FROM knowledge_base 
GROUP BY level;

-- 查看有内容的 L4 数量
SELECT COUNT(*) FROM l4_content;

-- 查看特定 L1 下的完整树
SELECT * FROM knowledge_base 
WHERE parent_id IN (
    SELECT id FROM knowledge_base WHERE level = 1 AND name = 'Career & Professional Development'
);
```

---

## 🔗 相关文档

- 主项目 README：`../README.md`
- Web 应用文档：`../web_app/README.md`
- 匹配流程说明：`../MATCHING_PROCESS_EXPLANATION.md`
