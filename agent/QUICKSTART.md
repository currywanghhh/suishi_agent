# 快速使用指南

## 🚀 最常用的工作流

### 场景1：首次生成完整知识库

```bash
# 步骤1: 生成L1领域
python create_knowledge_base.py

# 步骤2: 批量生成所有L2→L3→L4
python generate_sub_levels.py
```

### 场景2：只为某个L1领域生成内容 ⭐（推荐）

```bash
# 查看所有L1领域
python generate_for_l1.py --list

# 为"Career"领域生成完整子树
python generate_for_l1.py --l1 "Career"

# 为"Love"领域生成，自定义数量
python generate_for_l1.py --l1 "Love" --max-l2 15 --max-l3 10 --max-l4 8
```

### 场景3：重新生成某个层级

```bash
# 删除所有L2数据
# SQL: DELETE FROM knowledge_base WHERE level = 2;

# 重新生成L2
python generate_single_level.py --level 2 --max 12
```

### 场景4：逐步生成，验证质量

```bash
# 先为某个L1只生成L2
python generate_for_l1.py --l1 1 --skip-l3 --skip-l4

# 检查L2质量后，再生成L3和L4
python generate_for_l1.py --l1 1 --skip-l2
```

## 📊 常用SQL查询

```sql
-- 查看各层级数量统计
SELECT level, COUNT(*) as count FROM knowledge_base GROUP BY level;

-- 查看所有L1领域
SELECT id, name FROM knowledge_base WHERE level = 1;

-- 查看某个L1（ID=1）的完整树状结构
SELECT 
    l1.name as L1_Domain,
    l2.name as L2_Scenario,
    l3.name as L3_SubScenario,
    l4.name as L4_Intention
FROM knowledge_base l1
LEFT JOIN knowledge_base l2 ON l2.parent_id = l1.id AND l2.level = 2
LEFT JOIN knowledge_base l3 ON l3.parent_id = l2.id AND l3.level = 3
LEFT JOIN knowledge_base l4 ON l4.parent_id = l3.id AND l4.level = 4
WHERE l1.level = 1 AND l1.id = 1;

-- 删除某个L1（ID=1）下的所有子节点
DELETE FROM knowledge_base WHERE id = 1 OR parent_id = 1 
  OR parent_id IN (SELECT id FROM knowledge_base WHERE parent_id = 1)
  OR parent_id IN (SELECT id FROM knowledge_base WHERE parent_id IN 
      (SELECT id FROM knowledge_base WHERE parent_id = 1));
```

## 🎯 推荐工作流

### 方案A：小步快跑（推荐新手）

1. 生成L1领域
2. **选择1-2个重点L1领域**，使用 `generate_for_l1.py` 生成子树
3. 验证内容质量，调整参数
4. 逐步为其他L1领域生成内容

### 方案B：一次性批量（适合有经验用户）

1. 生成L1领域
2. 直接运行 `generate_sub_levels.py` 批量生成所有内容
3. 后期针对质量不佳的领域重新生成

## ⚙️ 参数调优建议

### 按领域重要性调整数量

**核心领域（如Career、Love）：**
```bash
python generate_for_l1.py --l1 "Career" --max-l2 15 --max-l3 12 --max-l4 8
```

**次要领域（如Travel、Hobbies）：**
```bash
python generate_for_l1.py --l1 "Travel" --max-l2 8 --max-l3 6 --max-l4 5
```

### 根据API配额调整速度

编辑 `config.py`:
```python
API_CONFIG = {
    'delay_between_calls': 2,     # 增加延迟避免限流（默认1秒）
}
```

## 🔍 调试技巧

### 查看生成进度

```bash
# 实时查看数据库记录数
watch -n 5 'mysql -u root -p -e "SELECT level, COUNT(*) FROM knowledge_base GROUP BY level;"'
```

### 查看最近生成的内容

```sql
-- 查看最近10条L2场景
SELECT id, name, created_at FROM knowledge_base 
WHERE level = 2 
ORDER BY created_at DESC 
LIMIT 10;
```

### 查找生成失败的记录

```sql
-- 查找没有描述的记录
SELECT level, name FROM knowledge_base 
WHERE description_en IS NULL OR description_en = '';
```

## 💡 最佳实践

1. **先小规模测试**：为1-2个L1生成内容，验证质量
2. **分批生成**：不要一次性生成所有内容，避免浪费API配额
3. **定期备份数据库**：在大规模生成前备份数据
4. **监控API使用**：注意API调用次数和余额
5. **灵活使用 `generate_for_l1.py`**：这是最灵活的工具，适合大多数场景

## 🆘 遇到问题？

1. 检查 `.env` 配置是否正确
2. 确认数据库连接正常
3. 验证API密钥有效且有余额
4. 查看终端输出的错误信息
5. 使用 `--list` 参数检查数据库状态
