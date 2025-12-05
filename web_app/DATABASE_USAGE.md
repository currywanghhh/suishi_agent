# 📊 Web 应用使用的数据库表

## 🎯 核心表结构

Web 应用 (`web_app/`) 使用 **2 张主要表**：

### 1. `knowledge_base` 表
存储 4 层知识结构（L1-L4）

**字段**:
- `id` - 主键
- `level` - 层级 (1=领域, 2=场景, 3=子场景, 4=意图)
- `parent_id` - 父节点 ID
- `name` - 名称（英文）
- `description_en` - 英文描述
- `five_element_association` - 五行关联（可选）
- `created_at` - 创建时间
- `updated_at` - 更新时间

### 2. `l4_content` 表
存储 L4 意图的详细内容

**字段**:
- `id` - 主键
- `l4_id` - 关联的 L4 意图 ID（外键 → `knowledge_base.id`）
- `five_elements_insight` - 五行洞察（TEXT）
- `action_guide` - 行动指南（TEXT）
- `communication_scripts` - 沟通话术（TEXT）
- `energy_harmonization` - 能量调和（TEXT）
- `created_at` - 创建时间

---

## 🔍 代码中的使用位置

### 文件：`web_app/advisor/views.py`

#### 1️⃣ 查询 L1 领域（第 93 行）
```python
cursor.execute("SELECT id, name, description_en FROM knowledge_base WHERE level = 1")
l1_candidates = cursor.fetchall()
```

#### 2️⃣ 查询 L2 场景（第 118-121 行）
```python
cursor.execute("""
    SELECT id, name, description_en 
    FROM knowledge_base 
    WHERE level = 2 AND parent_id = %s
""", (best_l1_id,))
l2_candidates = cursor.fetchall()
```

#### 3️⃣ 查询 L3 子场景（第 144-147 行）
```python
cursor.execute("""
    SELECT id, name, description_en 
    FROM knowledge_base 
    WHERE level = 3 AND parent_id = %s
""", (best_l2_id,))
l3_candidates = cursor.fetchall()
```

#### 4️⃣ 查询 L4 意图（第 170-173 行）
```python
cursor.execute("""
    SELECT kb.id, kb.name, kb.description_en 
    FROM knowledge_base kb
    JOIN l4_content c ON kb.id = c.l4_id
    WHERE kb.level = 4 AND kb.parent_id = %s
""", (best_l3_id,))
l4_candidates = cursor.fetchall()
```
**注意**: 这里 **JOIN** 了 `l4_content` 表，只返回有详细内容的 L4。

#### 5️⃣ 获取 L4 详细内容（第 256-259 行）
```python
cursor.execute("""
    SELECT kb.name, c.five_elements_insight, c.action_guide, 
           c.communication_scripts, c.energy_harmonization
    FROM l4_content c
    JOIN knowledge_base kb ON c.l4_id = kb.id
    WHERE c.l4_id = %s
""", (l4_id,))
```

返回结果示例：
```python
{
    'intention_name': '第一次约会应该穿什么？',
    'five_elements_insight': '您的...',
    'action_guide': '1. 选择...',
    'communication_scripts': '我想...',
    'energy_harmonization': '佩戴...'
}
```

---

## 🔄 完整匹配流程

```
用户问题 
    ↓
查询 knowledge_base (level=1) → LLM 选择 → L1 ID
    ↓
查询 knowledge_base (level=2, parent_id=L1) → LLM 选择 → L2 ID
    ↓
查询 knowledge_base (level=3, parent_id=L2) → LLM 选择 → L3 ID
    ↓
查询 knowledge_base (level=4, parent_id=L3) 
  JOIN l4_content (确保有内容) → LLM 选择 → L4 ID
    ↓
查询 l4_content (l4_id=L4) 
  JOIN knowledge_base (获取名称) → 返回详细内容
```

---

## 📋 数据库配置

### 当前配置（`web_app/.env`）
```env
DB_HOST="localhost"
DB_USER="root"
DB_PASSWORD="123456"
DB_NAME="mysql"  ← 当前数据库名
```

### ⚠️ 重要提醒

你的 `DB_NAME="mysql"` 是 MySQL 的系统数据库名。

**应该改为你创建的知识库数据库名**，例如：
```env
DB_NAME="wu_xing_advisor"
```

或者如果你在 `mysql` 数据库中创建了这两张表，则保持不变。

### 验证表是否存在

```sql
-- 切换到你的数据库
USE mysql;  -- 或 USE wu_xing_advisor;

-- 查看表
SHOW TABLES;

-- 应该能看到：
-- knowledge_base
-- l4_content

-- 检查 L4 内容数量
SELECT COUNT(*) FROM l4_content;

-- 检查各层级数量
SELECT level, COUNT(*) as count 
FROM knowledge_base 
GROUP BY level;
```

---

## 🧪 测试连接

运行以下命令测试数据库连接：

```powershell
cd web_app
python -c "import mysql.connector; from dotenv import load_dotenv; import os; load_dotenv(); conn = mysql.connector.connect(host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME')); print('连接成功！'); cursor = conn.cursor(); cursor.execute('SHOW TABLES'); print('表列表:', [t[0] for t in cursor.fetchall()]); conn.close()"
```

应该输出：
```
连接成功！
表列表: ['knowledge_base', 'l4_content', ...]
```

---

## 🔧 如果表不存在

需要先运行数据生成脚本：

```powershell
cd data_generation
python create_knowledge_base.py
python generate_for_l1.py
python generate_l4_content.py
```

---

## 📝 总结

- **使用的表**: `knowledge_base` + `l4_content`
- **连接位置**: `web_app/advisor/views.py`
- **查询次数**: 5 次（L1、L2、L3、L4 结构查询 + L4 内容查询）
- **当前配置**: 数据库名是 `mysql`（建议改为专用数据库如 `wu_xing_advisor`）
