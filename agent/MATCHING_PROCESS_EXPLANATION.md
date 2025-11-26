# 🎯 知识库匹配流程详解

整个思路：
1. 用户输入问题
2. 通过大模型匹配到L1领域
3. 在该L1下查询所有L2场景，再匹配
4. 在选中的L2下查询所有L3子场景，再匹配
5. 在选中的L3下查询所有L4意图，匹配并返回内容

**整个过程需要调用4次LLM API。**

---

## 🔄 完整流程图解

```
用户问题: "How to balance work and relationships?"
         ↓
┌────────────────────────────────────────────────────┐
│ 第1次 LLM 调用：匹配 L1 领域                          │
├────────────────────────────────────────────────────┤
│ 数据库查询:                                          │
│   SELECT * FROM knowledge_base WHERE level = 1     │
│                                                    │
│ 查询结果（假设6个L1）:                               │
│   ID 1: Career & Professional Development         │
│   ID 2: Love & Romantic Relationships             │
│   ID 3: Family & Parenting                        │
│   ID 4: Health & Wellness                         │
│   ID 5: Financial Planning                        │
│   ID 6: Personal Growth                           │
│                                                    │
│ 提示词发给LLM:                                       │
│   User Query: "How to balance work and relationships?"│
│   Available Life Domains (L1):                    │
│   ID 1: Career & Professional Development...      │
│   ID 2: Love & Romantic Relationships...          │
│   ... [所有6个L1]                                  │
│   Task: Select the most relevant ID.              │
│                                                    │
│ LLM返回: 1                                          │
└────────────────────────────────────────────────────┘
         ↓ 确定了 L1 = Career (ID: 1)
         ↓
┌────────────────────────────────────────────────────┐
│ 第2次 LLM 调用：匹配 L2 场景                          │
├────────────────────────────────────────────────────┤
│ 数据库查询（只查L1=1下的L2）:                         │
│   SELECT * FROM knowledge_base                    │
│   WHERE level = 2 AND parent_id = 1               │
│                                                    │
│ 查询结果（假设该L1下有10个L2）:                       │
│   ID 11: Job Interview Preparation                │
│   ID 12: Work-Life Balance Management  ← 最相关    │
│   ID 13: Career Transition Planning               │
│   ID 14: Workplace Relationship Dynamics          │
│   ID 15: Professional Skill Development           │
│   ... [总共10个L2]                                 │
│                                                    │
│ 提示词发给LLM:                                       │
│   User Query: "How to balance work and relationships?"│
│   Available Scenarios (L2):                       │
│   ID 11: Job Interview Preparation...             │
│   ID 12: Work-Life Balance Management...          │
│   ... [所有10个L2]                                 │
│   Task: Select the most relevant Scenario ID.    │
│                                                    │
│ LLM返回: 12                                         │
└────────────────────────────────────────────────────┘
         ↓ 确定了 L2 = Work-Life Balance (ID: 12)
         ↓
┌────────────────────────────────────────────────────┐
│ 第3次 LLM 调用：匹配 L3 子场景                        │
├────────────────────────────────────────────────────┤
│ 数据库查询（只查L2=12下的L3）:                        │
│   SELECT * FROM knowledge_base                    │
│   WHERE level = 3 AND parent_id = 12              │
│                                                    │
│ 查询结果（假设该L2下有8个L3）:                        │
│   ID 45: Balancing Work Hours with Personal Time  │
│   ID 46: Managing Work Stress During Personal Time│
│   ID 47: Setting Boundaries with Colleagues       │
│   ID 48: Dealing with Overwork and Burnout        │
│   ... [总共8个L3]                                  │
│                                                    │
│ 提示词发给LLM:                                       │
│   User Query: "How to balance work and relationships?"│
│   Available Sub-scenarios (L3):                   │
│   ID 45: Balancing Work Hours with Personal Time...│
│   ID 46: Managing Work Stress...                  │
│   ... [所有8个L3]                                  │
│   Task: Select the most relevant Sub-scenario ID.│
│                                                    │
│ LLM返回: 45                                         │
└────────────────────────────────────────────────────┘
         ↓ 确定了 L3 = Balancing Work Hours (ID: 45)
         ↓
┌────────────────────────────────────────────────────┐
│ 第4次 LLM 调用：匹配 L4 意图                          │
├────────────────────────────────────────────────────┤
│ 数据库查询（只查L3=45下且有内容的L4）:                 │
│   SELECT kb.* FROM knowledge_base kb              │
│   JOIN l4_content c ON kb.id = c.l4_id            │
│   WHERE kb.level = 4 AND kb.parent_id = 45        │
│                                                    │
│ 查询结果（假设该L3下有6个L4）:                        │
│   ID 58: How can I balance work hours for partner?│
│   ID 59: Strategies to negotiate flexible hours?  │
│   ID 60: Manage work hours in long-distance?      │
│   ID 61: Best practices for setting boundaries?   │
│   ... [总共6个L4]                                  │
│                                                    │
│ 提示词发给LLM:                                       │
│   User Query: "How to balance work and relationships?"│
│   Available User Intentions (L4):                 │
│   ID 58: How can I balance work hours for partner?│
│   ID 59: Strategies to negotiate flexible hours?  │
│   ... [所有6个L4]                                  │
│   Task: Select the ID that EXACTLY matches user's need.│
│                                                    │
│ LLM返回: 58                                         │
└────────────────────────────────────────────────────┘
         ↓ 确定了 L4 = ID 58
         ↓
┌────────────────────────────────────────────────────┐
│ 查询 L4 详细内容（不需要LLM）                         │
├────────────────────────────────────────────────────┤
│ 数据库查询:                                          │
│   SELECT * FROM l4_content WHERE l4_id = 58       │
│                                                    │
│ 返回4个部分:                                         │
│   - five_elements_insight: "Your relationship..."│
│   - action_guide: "1. Schedule quality time..."  │
│   - communication_scripts: "I need to..."        │
│   - energy_harmonization: "Wear blue colors..."  │
└────────────────────────────────────────────────────┘
         ↓
    流式输出给用户
```

---

## 🔢 为什么需要4次API调用？

### **原因1：逐层精准定位**
- 如果一次性把所有L4（可能上百个）都给LLM选择，容易出错
- 分4层匹配，每层候选数量少（6→10→8→6），LLM更准确

### **原因2：利用层级结构**
```
不用层级（一次查询所有L4）:
┌──────────────────────────┐
│ 所有L4（假设100个）          │
│ ↓                        │
│ LLM一次性选择 → 容易混淆    │
└──────────────────────────┘

使用层级（分4次查询）:
┌──────────────────────────┐
│ L1: 6个候选               │
│ ↓ LLM选择 → 确定1个        │
│ L2: 10个候选（该L1下）     │
│ ↓ LLM选择 → 确定1个        │
│ L3: 8个候选（该L2下）      │
│ ↓ LLM选择 → 确定1个        │
│ L4: 6个候选（该L3下）      │
│ ↓ LLM选择 → 确定1个        │
│ = 最终精准匹配             │
└──────────────────────────┘
```

### **原因3：数据库设计决定**
- 你的数据库是**树状结构**：每个节点有parent_id
- 必须先知道父节点ID，才能查询子节点
- 例如：不知道L2的ID，就查不到它下面的L3

---

## 💰 成本和时间

### **API调用次数：4次**
- 每次调用参数：
  - `max_tokens`: 50（只需要返回1个数字）
  - `temperature`: 0.3（低温度，更确定性）
  - 成本很低（每次约0.001元）

### **总响应时间：约5-10秒**
```
匹配L1: 1-2秒
匹配L2: 1-2秒  
匹配L3: 1-2秒
匹配L4: 1-2秒
流式输出内容: 2-3秒
─────────────────
总计: 7-11秒
```

---

## 🎯 代码对应关系

### **代码中的4次调用位置：**

```python
def find_best_l4_match(user_query):
    # 第1次调用
    cursor.execute("SELECT * FROM knowledge_base WHERE level = 1")
    l1_candidates = cursor.fetchall()
    best_l1_id = call_llm_for_selection(l1_prompt)  # ← LLM调用1
    
    # 第2次调用
    cursor.execute("... WHERE level = 2 AND parent_id = %s", (best_l1_id,))
    l2_candidates = cursor.fetchall()
    best_l2_id = call_llm_for_selection(l2_prompt)  # ← LLM调用2
    
    # 第3次调用
    cursor.execute("... WHERE level = 3 AND parent_id = %s", (best_l2_id,))
    l3_candidates = cursor.fetchall()
    best_l3_id = call_llm_for_selection(l3_prompt)  # ← LLM调用3
    
    # 第4次调用
    cursor.execute("... WHERE level = 4 AND parent_id = %s", (best_l3_id,))
    l4_candidates = cursor.fetchall()
    best_l4_id = call_llm_for_selection(l4_prompt)  # ← LLM调用4
    
    return best_l4_id
```

### **统一的LLM调用函数：**

```python
def call_llm_for_selection(prompt):
    """所有4次调用都用这个函数"""
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50,
        "temperature": 0.3
    }
    response = requests.post(SILICON_FLOW_API_URL, ...)
    # 提取返回的数字ID
    match = re.search(r'\d+', response_text)
    return int(match.group())
```

---

## 🔧 如果想减少API调用次数？

### **方案1：跳过中间层（不推荐）**
```python
# 只匹配L1和L4（跳过L2、L3）
best_l1_id = call_llm(...)  # 1次
cursor.execute("SELECT * FROM knowledge_base WHERE level = 4 AND parent_id IN (SELECT id FROM ... parent_id = %s)", best_l1_id)
best_l4_id = call_llm(...)  # 1次
# 总共2次调用，但准确率下降
```

**缺点：**
- L1下可能有很多L4（几十个），LLM难以准确选择
- 失去了L2、L3的语义细化

### **方案2：使用向量检索（需要额外工具）**
```python
# 用embedding模型把所有L4转成向量
# 用户问题也转成向量
# 计算余弦相似度，找最接近的L4
# 只需要1次LLM调用（生成embedding）
```

**需要：**
- 向量数据库（如Pinecone、Milvus）
- Embedding模型（如text-embedding-ada-002）
- 更复杂的架构

### **方案3：混合方式（推荐的优化）**
```python
# L1用LLM匹配（1次）
# L2、L3用关键词匹配（不用LLM）
# L4用LLM精准匹配（1次）
# 总共2次调用，平衡速度和准确性
```

---

## 📊 当前实现的优势

✅ **准确性高**：4层逐步筛选，每层候选少
✅ **可追溯**：知道完整路径 L1→L2→L3→L4
✅ **可调试**：每层都有print输出
✅ **可扩展**：未来可以添加更多层级
✅ **充分利用数据库结构**：发挥树状层级的优势

---

## 🎓 总结

你的理解是**完全正确**的！

- 用户输入 → L1匹配（API 1） → L2匹配（API 2） → L3匹配（API 3） → L4匹配（API 4） → 返回内容
- 每次都是：**查数据库 → 给LLM选择 → 用结果查下一层**
- 4次API调用是必需的，因为需要**逐层确定父节点ID**才能查询子节点
- 这是**树状数据库结构**决定的，不是代码设计问题

如果你觉得4次调用太慢或成本高，可以考虑：
1. 缓存热门问题的匹配结果
2. 使用向量检索替代部分LLM调用
3. 调整为L1 + L4两次匹配（牺牲一些准确性）

当前的4层匹配是**准确性和性能的最佳平衡**！
