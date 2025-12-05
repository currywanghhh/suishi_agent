# 知识库生成提示词完整文档

本文档整理了 Wu Xing Decision Advisor 数据生成系统中所有层级的提示词模板。

---

## 产品背景

**应用定位：**
- 基于东方玄学（五行、占星术、东方占卜）结合实用指导的决策辅助应用
- 目标市场：北美用户（主要通过 YouTube 和 Instagram 获客）
- 目标人群：18-45 岁关注占星术、东方哲学或面临决策困扰的年轻及中年成人
- 商业模式：iOS 付费订阅制
- 核心价值：帮助用户对自己的选择感到自信和快乐

---

## 一、L1 领域生成（Life Domains）

### 提示词原文

```
You are a content strategist for a subscription-based iOS app targeting the North American market.

**Product Overview:**
- The app helps users make better life decisions by combining Eastern metaphysics (Five Elements, astrology, Eastern divination) with practical guidance.
- Target audience: North American users who follow astrology, Eastern philosophy, or struggle with decision-making, primarily from YouTube and Instagram.
- The app provides personalized advice to help users feel confident and happy about their choices.
- Service model: Paid subscription (iOS app).

**Your Task:**
Generate a COMPREHENSIVE list of L1 life domains (领域) that cover ALL possible areas where users might seek decision-making guidance.
Think broadly about every aspect of modern life where people face choices and need clarity.

**Requirements:**
1. Output in English only.
2. Domains should be broad life categories (e.g., "Career & Professional Growth", "Love & Romance", "Family & Parenting", "Financial Planning").
3. Cover as many areas as possible: relationships, career, health, money, personal growth, lifestyle, spirituality, etc.
4. Be relatable to young and middle-aged North American adults (18-45 years old).
5. Think about what questions users might ask when facing life decisions.
6. Return as a JSON object with key "domains" containing an array of strings.
7. Generate between 15 and {max_domains} domains to be as comprehensive as possible.

**Example format:**
{
  "domains": [
    "Career & Professional Development",
    "Love & Romantic Relationships", 
    "Family & Parenting",
    "Financial Planning & Wealth",
    "Health & Wellness",
    "Personal Growth & Self-Discovery",
    "Friendships & Social Life",
    "Education & Learning",
    "Home & Living Environment",
    "Travel & Adventure"
  ]
}

Now generate a comprehensive L1 domain list (aim for {max_domains} or fewer):
```

### 中文翻译

```
你是一个面向北美市场的订阅制 iOS 应用的内容策略师。

**产品概述：**
- 该应用通过结合东方玄学（五行、占星术、东方占卜）与实用指导，帮助用户做出更好的人生决策。
- 目标受众：关注占星术、东方哲学或在决策中挣扎的北美用户，主要来自 YouTube 和 Instagram。
- 该应用提供个性化建议，帮助用户对自己的选择感到自信和快乐。
- 服务模式：付费订阅（iOS 应用）。

**你的任务：**
生成一个全面的 L1 生活领域列表，涵盖用户可能寻求决策指导的所有可能领域。
广泛思考现代生活的各个方面，人们在哪些地方面临选择并需要清晰认知。

**要求：**
1. 仅用英文输出。
2. 领域应该是广泛的生活类别（例如："职业与专业成长"、"爱情与浪漫关系"、"家庭与育儿"、"财务规划"）。
3. 尽可能涵盖多个领域：关系、职业、健康、金钱、个人成长、生活方式、灵性等。
4. 要与 18-45 岁的北美年轻及中年成人产生共鸣。
5. 思考用户在面临人生决策时可能会问什么问题。
6. 以 JSON 对象返回，键名为 "domains"，包含字符串数组。
7. 生成 15 到 {max_domains} 个领域，力求全面覆盖。

**示例格式：**
{
  "domains": [
    "职业与专业发展",
    "爱情与浪漫关系", 
    "家庭与育儿",
    "财务规划与财富",
    "健康与保健",
    "个人成长与自我发现",
    "友谊与社交生活",
    "教育与学习",
    "家居与生活环境",
    "旅行与冒险"
  ]
}

现在生成一个全面的 L1 领域列表（目标 {max_domains} 个或更少）：
```

---

## 二、L2 场景生成（Scenarios）

### 提示词原文

```
You are a content strategist for a decision-making app based on Eastern metaphysics, targeting North American users.

**Current Task:**
Generate specific SCENARIOS (场景) within the L1 Domain "{parent_name}".
Scenarios are common situations or contexts where users need to make decisions.

Examples for "Love & Romance": 
- "Dating & Finding a Partner"
- "Relationship Conflicts"
- "Long-Distance Relationships"

**Parent Context:** "{parent_name}"

**Requirements:**
1. Output in English only.
2. Each item should be a specific, relatable situation for North American users.
3. Think about what real users would search for or ask about.
4. Return as JSON: {"items": ["item1", "item2", ...]}
5. Generate 5-{max_items} items.

Generate the L2 场景(Scenarios):
```

### 中文翻译

```
你是一个基于东方玄学的决策应用的内容策略师，目标用户是北美用户。

**当前任务：**
在 L1 领域 "{parent_name}" 中生成具体的场景。
场景是用户需要做决策的常见情境或背景。

示例（针对"爱情与浪漫"领域）：
- "约会与寻找伴侣"
- "关系冲突"
- "异地恋"

**父级背景：** "{parent_name}"

**要求：**
1. 只用英文输出。
2. 每个项目应该是北美用户可以产生共鸣的具体情境。
3. 考虑真实用户会搜索或询问什么。
4. 以 JSON 格式返回：{"items": ["item1", "item2", ...]}
5. 生成 5-{max_items} 个项目。

生成 L2 场景(Scenarios)：
```

---

## 三、L3 子场景生成（Sub-scenarios）

### 提示词原文

```
You are a content strategist for a decision-making app based on Eastern metaphysics, targeting North American users.

**Current Task:**
Generate specific SUB-SCENARIOS (子场景) within the L2 Scenario "{parent_name}".
Sub-scenarios are more detailed, actionable situations within a scenario.

Examples for L2 "Dating & Finding a Partner":
- "First Date Preparation"
- "Online Dating Profile"
- "Expressing Romantic Interest"

**Parent Context:** "{parent_name}"

**Requirements:**
1. Output in English only.
2. Each item should be a specific, relatable situation for North American users.
3. Think about what real users would search for or ask about.
4. Return as JSON: {"items": ["item1", "item2", ...]}
5. Generate 5-{max_items} items.

Generate the L3 子场景(Sub-scenarios):
```

### 中文翻译

```
你是一个基于东方玄学的决策应用的内容策略师，目标用户是北美用户。

**当前任务：**
在 L2 场景 "{parent_name}" 中生成具体的子场景。
子场景是场景内更详细、可操作的具体情境。

示例（针对 L2 "约会与寻找伴侣"）：
- "第一次约会准备"
- "在线约会资料"
- "表达浪漫兴趣"

**父级背景：** "{parent_name}"

**要求：**
1. 只用英文输出。
2. 每个项目应该是北美用户可以产生共鸣的具体情境。
3. 考虑真实用户会搜索或询问什么。
4. 以 JSON 格式返回：{"items": ["item1", "item2", ...]}
5. 生成 5-{max_items} 个项目。

生成 L3 子场景(Sub-scenarios)：
```

---

## 四、L4 用户意图生成（User Intentions）

### 提示词原文

```
You are a content strategist for a decision-making app based on Eastern metaphysics, targeting North American users.

**Current Task:**
Generate specific USER INTENTIONS (意图) within the L3 Sub-scenario "{parent_name}".
Intentions are concrete questions or goals users have in this context.

Examples for L3 "First Date Preparation":
- "What should I wear on the first date?"
- "How do I make a good first impression?"
- "Should I suggest a second date?"

**Parent Context:** "{parent_name}"

**Requirements:**
1. Output in English only.
2. Each item should be a specific, relatable situation for North American users.
3. Think about what real users would search for or ask about.
4. Return as JSON: {"items": ["item1", "item2", ...]}
5. Generate 5-{max_items} items.

Generate the L4 意图(User Intentions):
```

### 中文翻译

```
你是一个基于东方玄学的决策应用的内容策略师，目标用户是北美用户。

**当前任务：**
在 L3 子场景 "{parent_name}" 中生成具体的用户意图。
意图是用户在这个情境下具体的问题或目标。

示例（针对 L3 "第一次约会准备"）：
- "第一次约会我应该穿什么？"
- "我如何留下良好的第一印象？"
- "我应该建议第二次约会吗？"

**父级背景：** "{parent_name}"

**要求：**
1. 只用英文输出。
2. 每个项目应该是北美用户可以产生共鸣的具体情境。
3. 考虑真实用户会搜索或询问什么。
4. 以 JSON 格式返回：{"items": ["item1", "item2", ...]}
5. 生成 5-{max_items} 个项目。

生成 L4 用户意图(User Intentions)：
```

---

## 五、描述生成（Descriptions for L2/L3/L4）

### 提示词原文

```
You are a content writer for a decision-making iOS app using Eastern metaphysics for North American users.

**Your Task:**
Write a brief, encouraging description for this {item_type}: "{name}"
Parent category: "{parent_name}"

**Requirements:**
1. Write in English, 1-2 sentences.
2. Speak to users facing this specific situation.
3. Emphasize gaining clarity and making confident choices.
4. Use warm, accessible language (not overly mystical).

Write the description:
```

### 中文翻译

```
你是一个使用东方玄学为北美用户提供决策帮助的 iOS 应用的内容撰写者。

**你的任务：**
为这个 {item_type}（L2 场景/L3 子场景/L4 用户意图）撰写简短、鼓励性的描述："{name}"
父级类别："{parent_name}"

**要求：**
1. 用英文撰写，1-2 句话。
2. 针对面临这种具体情境的用户说话。
3. 强调获得清晰认知和做出自信选择。
4. 使用温暖、平易近人的语言（不要过于神秘）。

撰写描述：
```

---

## 六、L4 详细内容生成（五行建议）

### 提示词原文

```
You are an expert content creator for a "Personal Energy Management" app based on Eastern Five Elements (Wu Xing) metaphysics.

**Context:**
- Domain (L1): {L1_name} ({L1_desc})
- Scenario (L2): {L2_name} ({L2_desc})
- Sub-scenario (L3): {L3_name} ({L3_desc})
- User Intention (L4): {L4_name} ({L4_desc})

**Task:**
Generate detailed, actionable, and empathetic content for this specific user intention.
The content must be divided into exactly these four sections:

1. **Five Elements Insight (五行洞察)**: 
   Analyze the situation using Five Elements theory (Wood, Fire, Earth, Metal, Water). 
   Explain the energy dynamics at play. 
   Which element is weak? Which is strong? What is the conflict?

2. **Action Guide (行动指南)**: 
   Provide 3-5 concrete, practical steps the user can take immediately. 
   These should be real-world actions, not just abstract advice.

3. **Communication Scripts (沟通话术)**: 
   Provide 2-3 specific scripts or phrases the user can say to others involved in this situation 
   (or to themselves as affirmations).

4. **Energy Harmonization (能量调和)**: 
   Suggest small rituals, colors to wear, directions to face, or mindset shifts to balance the energy.

**Requirements:**
- Output MUST be in **JSON format**.
- Keys: "five_elements_insight", "action_guide", "communication_scripts", "energy_harmonization".
- Language: **English** (as the target market is North America).
- Tone: Empathetic, wise, practical, modern, and supportive. 
  Avoid overly mystical jargon without explanation.
```

### 中文翻译

```
你是一个基于东方五行（Wu Xing）玄学的"个人能量管理"应用的专家内容创作者。

**背景信息：**
- 领域（L1）：{L1名称}（{L1描述}）
- 场景（L2）：{L2名称}（{L2描述}）
- 子场景（L3）：{L3名称}（{L3描述}）
- 用户意图（L4）：{L4名称}（{L4描述}）

**任务：**
为这个特定的用户意图生成详细、可操作、富有同理心的内容。
内容必须精确地分为以下四个部分：

1. **五行洞察 (Five Elements Insight)**：
   使用五行理论（木、火、土、金、水）分析情境。
   解释当前的能量动态。
   哪个元素弱？哪个元素强？冲突在哪里？

2. **行动指南 (Action Guide)**：
   提供 3-5 个具体、实用的步骤，用户可以立即采取行动。
   这些应该是现实世界的行动，而不仅仅是抽象的建议。

3. **沟通话术 (Communication Scripts)**：
   提供 2-3 个具体的脚本或短语，用户可以对参与此情境的其他人说
   （或作为自我肯定对自己说）。

4. **能量调和 (Energy Harmonization)**：
   建议小型仪式、要穿的颜色、要面对的方向，
   或心态转变来平衡能量。

**要求：**
- 输出必须是 **JSON 格式**。
- 键名："five_elements_insight"、"action_guide"、"communication_scripts"、"energy_harmonization"。
- 语言：**英文**（因为目标市场是北美）。
- 语气：富有同理心、智慧、实用、现代、支持性。
  避免过度神秘的术语而不加解释。
```

### 输出格式示例

```json
{
  "five_elements_insight": "在第一次约会的情境中，你的木元素（代表成长和自信）可能因焦虑而受到抑制，而水元素（情感流动）可能过于活跃。火元素（热情和表达）需要被点燃，以平衡过度的水能量...",
  
  "action_guide": "1. 提前选择一个让你感到舒适的场所，这样可以减少木元素的焦虑。\n2. 穿着能提升你自信的衣服，选择绿色或蓝色调增强木和水的平衡。\n3. 提前准备3个你感兴趣的话题，这样对话会更自然流畅。\n4. 深呼吸练习：约会前做5次深呼吸，想象自己散发出温暖的光芒。\n5. 设定一个积极的意图：'我值得爱，我会真实地展现自己。'",
  
  "communication_scripts": "1. 开场白：'我很高兴我们能见面，我一直想更了解你。'\n2. 表达兴趣：'你刚才说的那个真有趣，能再多告诉我一些吗？'\n3. 自我肯定（对自己说）：'我值得爱和被爱，我会真实地展现自己，吸引对的人。'",
  
  "energy_harmonization": "- 颜色选择：穿绿色或蓝色（木、水元素）增强自信和情感流动，加一点红色配饰（火元素）增加热情。\n- 方向建议：约会前面向东方（木的方向）深呼吸3次，想象朝阳的能量流入你的身体。\n- 小仪式：约会当天早晨，点一支薰衣草香薰，对着镜子说：'我散发出真实而吸引人的能量。'\n- 心态调整：将焦虑重新定义为兴奋，它们的身体感觉是相似的，但意图不同。告诉自己：'这是一次探索的机会，而不是一场考试。'"
}
```

---

## 七、层级关系与设计逻辑

### 层级结构

```
L1 (Life Domains) - 生活领域
  └─ L2 (Scenarios) - 具体场景
      └─ L3 (Sub-scenarios) - 子场景
          └─ L4 (User Intentions) - 用户意图
              └─ L4 Content - 详细建议内容
                  ├─ Five Elements Insight - 五行洞察
                  ├─ Action Guide - 行动指南
                  ├─ Communication Scripts - 沟通话术
                  └─ Energy Harmonization - 能量调和
```

### 示例路径

```
L1: Career & Professional Development (职业与专业发展)
  └─ L2: Job Interview Preparation (求职面试准备)
      └─ L3: First Round Interview (首轮面试)
          └─ L4: "What should I wear to make a good impression?" 
                 (我应该穿什么给面试官留下好印象？)
              └─ Content:
                  - 五行洞察：分析职场能量，土元素（稳重）和金元素（专业）的平衡
                  - 行动指南：选择职业装、准备作品集、提前到达
                  - 沟通话术：自我介绍模板、回答问题的框架
                  - 能量调和：穿蓝色或灰色、面向西方冥想
```

### 设计原则

1. **层级递进**：从宽泛到具体，逐级细化
2. **用户导向**：基于真实用户的搜索和提问习惯
3. **可操作性**：越深入层级，内容越具体可执行
4. **文化适配**：结合东方智慧与北美用户的生活方式
5. **现代表达**：避免过度玄学，保持实用和温暖的语气

---

## 八、使用指南

### 生成顺序

1. **L1 生成**：运行 `create_knowledge_base.py`
2. **L2-L4 生成**：运行 `generate_single_level.py` 或 `generate_sub_levels.py`
3. **L4 内容生成**：运行 `generate_l4_content.py`

### 参数配置

在 `config.py` 中可调整：
- `L2_CONFIG["max_per_parent"]` - 每个L1生成的L2数量（默认10）
- `L3_CONFIG["max_per_parent"]` - 每个L2生成的L3数量（默认8）
- `L4_CONFIG["max_per_parent"]` - 每个L3生成的L4数量（默认6）
- `API_CONFIG["temperature"]` - 模型创造性（0.0-1.0，越高越随机）

### 质量控制建议

1. **L1阶段**：确保领域覆盖全面，参考竞品和用户调研
2. **L2-L3阶段**：检查场景是否贴近真实用户场景
3. **L4阶段**：验证问题是否自然、具体
4. **内容阶段**：确保建议实用、不过度玄学、语言温暖

---

**文档版本**: v1.0  
**最后更新**: 2025-11-27  
**适用系统**: Wu Xing Decision Advisor Data Generation Scripts
