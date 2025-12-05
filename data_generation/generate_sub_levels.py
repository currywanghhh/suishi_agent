import os
import mysql.connector
import requests
import json
from dotenv import load_dotenv
import time

# 加载 .env 文件
load_dotenv()

# --- 全局配置 ---
SILICON_FLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
LLM_MODEL = "alibaba/Qwen2-7B-Instruct"
# API请求之间的延迟（秒），以避免速率限制
API_DELAY = 1

# --- 数据库操作 ---
def get_db_connection():
    """建立并返回数据库连接。"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        if err.errno == 1049:
            print(f"数据库错误: 数据库 '{DB_CONFIG['database']}' 不存在。请先创建。")
        elif err.errno == 1045:
            print(f"数据库错误: 用户 '{DB_CONFIG['user']}' 访问被拒绝。请检查 .env 文件。")
        else:
            print(f"数据库连接错误: {err}")
        return None


def get_items_from_db(level: int, parent_id: int = None):
    """从数据库获取指定层级和父ID的项目。"""
    conn = get_db_connection()
    if not conn:
        return []

    items = []
    try:
        with conn.cursor(dictionary=True) as cursor:
            if parent_id:
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE level = %s AND parent_id = %s",
                    (level, parent_id),
                )
            else:
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE level = %s", (level,)
                )
            items = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"数据库查询错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()
    return items


# --- 大模型交互 ---
def call_llm(prompt: str, is_json_output: bool = False) -> str:
    """调用大模型API的通用函数。"""
    # ... (此函数与 generate_l1.py 中的相同)
    if not SILICON_FLOW_API_KEY:
        raise ValueError("错误：环境变量 SILICON_FLOW_API_KEY 未设置。")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,  # 增加max_tokens以容纳更长的列表
        "temperature": 0.5,
    }
    if is_json_output:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            SILICON_FLOW_API_URL, headers=headers, data=json.dumps(payload), timeout=120
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.RequestException as e:
        print(f"  -> LLM API 调用错误: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"  -> 解析LLM响应时出错: {e}")
        return None


def generate_sub_items(
    parent_level: int, parent_name: str, child_level: int, max_items: int = 10
) -> list:
    """为给定的父项生成子项列表。"""
    level_map = {
        2: "L2 场景(Scenarios)",
        3: "L3 子场景(Sub-scenarios)",
        4: "L4 意图(User Intentions)",
    }
    child_type = level_map.get(child_level, "items")
    parent_type = (
        level_map.get(parent_level, "L1 领域(Domain)")
        if parent_level > 1
        else "L1 领域(Domain)"
    )

    print(f"  -> 正在为 '{parent_name}' ({parent_type}) 生成 {child_type}...")

    # 根据层级定制提示词
    if child_level == 2:
        task_description = f"""
        Generate specific SCENARIOS (场景) within the L1 Domain "{parent_name}".
        Scenarios are common situations or contexts where users need to make decisions.
        
        Examples for "Love & Romance": 
        - "Dating & Finding a Partner"
        - "Relationship Conflicts"
        - "Long-Distance Relationships"
        - "Marriage & Commitment"
        - "Breakup & Moving On"
        """
    elif child_level == 3:
        task_description = f"""
        Generate specific SUB-SCENARIOS (子场景) within the L2 Scenario "{parent_name}".
        Sub-scenarios are more detailed, actionable situations within a scenario.
        
        Examples for L2 "Dating & Finding a Partner":
        - "First Date Preparation"
        - "Online Dating Profile"
        - "Expressing Romantic Interest"
        - "Meeting Partner's Family"
        """
    else:  # child_level == 4
        task_description = f"""
        Generate specific USER INTENTIONS (意图) within the L3 Sub-scenario "{parent_name}".
        Intentions are concrete questions or goals users have in this context.
        
        Examples for L3 "First Date Preparation":
        - "What should I wear on the first date?"
        - "How do I make a good first impression?"
        - "Should I suggest a second date?"
        - "How to handle first date nervousness?"
        """

    prompt = f"""
    You are a content strategist for a decision-making app based on Eastern metaphysics, targeting North American users.
    
    **Product Context:**
    - Subscription iOS app helping users make confident life decisions.
    - Combines Eastern divination (Five Elements, astrology) with practical guidance.
    - Users: Young/middle-aged North Americans interested in astrology and needing decision support.
    
    **Current Task:**
    {task_description}
    
    **Parent Context:** {parent_type} = "{parent_name}"
    
    **Requirements:**
    1. Output in English only.
    2. Each item should be a specific, relatable situation for North American users.
    3. Think about what real users would search for or ask about.
    4. Be practical and cover diverse situations within the parent category.
    5. Return as JSON: {{"items": ["item1", "item2", ...]}}
    6. Generate 5-{max_items} items.
    
    Generate the {child_type} for "{parent_name}":
    """

    response_str = call_llm(prompt, is_json_output=True)
    if not response_str:
        return []

    try:
        data = json.loads(response_str)
        # 尝试多个可能的key
        items = (
            data.get("items")
            or data.get(child_type.lower().replace(" ", "_"))
            or data.get(list(data.keys())[0], [])
        )
        if isinstance(items, list):
            items = items[:max_items]  # 限制数量
            print(f"  -> 成功生成{len(items)}个: {items}")
            return items
        return []
    except (json.JSONDecodeError, IndexError):
        print(f"  -> 无法解析JSON: {response_str}")
        return []


def get_item_description(name: str, level: int, parent_name: str) -> str:
    """为给定的项生成描述。"""
    level_map = {2: "L2 场景", 3: "L3 子场景", 4: "L4 用户意图"}
    item_type = level_map.get(level, "Item")

    print(f"    -> 正在为 '{name}' 生成描述...")

    prompt = f"""
    You are a content writer for a decision-making iOS app using Eastern metaphysics for North American users.
    
    **App Context:**
    - Helps users make confident decisions through Eastern divination + practical guidance.
    - Target: North Americans interested in astrology/Eastern philosophy, struggling with choices.
    - Goal: Users feel clear and happy about their decisions.
    
    **Your Task:**
    Write a brief, encouraging description for this {item_type}: "{name}"
    Parent category: "{parent_name}"
    
    **Requirements:**
    1. Write in English, 1-2 sentences.
    2. Speak to users facing this specific situation.
    3. Emphasize gaining clarity and making confident choices.
    4. Use warm, accessible language (not overly mystical).
    5. Be practical and relatable.
    
    **Example for L2 Scenario "Job Interview Preparation":**
    "Get ready to shine in your interview with cosmic guidance tailored to your energy. Make decisions about what to say, wear, and how to present yourself with confidence."
    
    Write the description for {item_type} "{name}" under "{parent_name}":
    """
    description = call_llm(prompt)
    if description and description.startswith('"') and description.endswith('"'):
        description = description[1:-1]
    return description


# --- 主逻辑 ---
def generate_l2_scenarios(max_scenarios_per_domain: int = 10):
    """
    根据L1领域生成L2场景。
    :param max_scenarios_per_domain: 每个L1领域生成的L2场景数量上限
    """
    print(f"\n{'='*60}")
    print(f"开始生成 L2 场景（每个L1领域最多生成{max_scenarios_per_domain}个场景）")
    print(f"{'='*60}\n")

    parent_items = get_items_from_db(level=1)
    if not parent_items:
        print("数据库中没有L1领域，无法生成L2场景。")
        return

    conn = get_db_connection()
    if not conn:
        return

    total_generated = 0
    try:
        with conn.cursor() as cursor:
            for idx, parent in enumerate(parent_items, 1):
                parent_id = parent["id"]
                parent_name = parent["name"]
                print(
                    f"[{idx}/{len(parent_items)}] 处理L1领域: {parent_name} (ID: {parent_id})"
                )

                # 生成L2场景列表
                scenarios = generate_sub_items(
                    1, parent_name, 2, max_items=max_scenarios_per_domain
                )
                time.sleep(API_DELAY)

                if not scenarios:
                    print(f"  ⚠️  未能生成场景，跳过\n")
                    continue

                # 为每个场景生成描述并插入
                for scenario_name in scenarios:
                    cursor.execute(
                        "SELECT id FROM knowledge_base WHERE level = 2 AND parent_id = %s AND name = %s",
                        (parent_id, scenario_name),
                    )
                    if cursor.fetchone():
                        print(f"  ⏭️  场景 '{scenario_name}' 已存在，跳过")
                        continue

                    description = get_item_description(scenario_name, 2, parent_name)
                    time.sleep(API_DELAY)

                    if description:
                        sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (2, parent_id, scenario_name, description))
                        conn.commit()
                        total_generated += 1
                        print(f"  ✅ 成功插入场景: '{scenario_name}' (ID: {cursor.lastrowid})")
                    else:
                        print(f"  ❌ 未能生成描述，跳过: '{scenario_name}'")
                print()  # 空行分隔
    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()

    print(f"\n{'='*60}")
    print(f"L2场景生成完成！共生成 {total_generated} 个场景")
    print(f"{'='*60}\n")


def generate_l3_subscenarios(max_subscenarios_per_scenario: int = 8):
    """
    根据L2场景生成L3子场景。
    :param max_subscenarios_per_scenario: 每个L2场景生成的L3子场景数量上限
    """
    print(f"\n{'='*60}")
    print(f"开始生成 L3 子场景（每个L2场景最多生成{max_subscenarios_per_scenario}个子场景）")
    print(f"{'='*60}\n")

    parent_items = get_items_from_db(level=2)
    if not parent_items:
        print("数据库中没有L2场景，无法生成L3子场景。")
        return

    conn = get_db_connection()
    if not conn:
        return

    total_generated = 0
    try:
        with conn.cursor() as cursor:
            for idx, parent in enumerate(parent_items, 1):
                parent_id = parent["id"]
                parent_name = parent["name"]
                print(
                    f"[{idx}/{len(parent_items)}] 处理L2场景: {parent_name} (ID: {parent_id})"
                )

                # 生成L3子场景列表
                subscenarios = generate_sub_items(
                    2, parent_name, 3, max_items=max_subscenarios_per_scenario
                )
                time.sleep(API_DELAY)

                if not subscenarios:
                    print(f"  ⚠️  未能生成子场景，跳过\n")
                    continue

                # 为每个子场景生成描述并插入
                for subscenario_name in subscenarios:
                    cursor.execute(
                        "SELECT id FROM knowledge_base WHERE level = 3 AND parent_id = %s AND name = %s",
                        (parent_id, subscenario_name),
                    )
                    if cursor.fetchone():
                        print(f"  ⏭️  子场景 '{subscenario_name}' 已存在，跳过")
                        continue

                    description = get_item_description(subscenario_name, 3, parent_name)
                    time.sleep(API_DELAY)

                    if description:
                        sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                        cursor.execute(
                            sql, (3, parent_id, subscenario_name, description)
                        )
                        conn.commit()
                        total_generated += 1
                        print(
                            f"  ✅ 成功插入子场景: '{subscenario_name}' (ID: {cursor.lastrowid})"
                        )
                    else:
                        print(f"  ❌ 未能生成描述，跳过: '{subscenario_name}'")
                print()  # 空行分隔
    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()

    print(f"\n{'='*60}")
    print(f"L3子场景生成完成！共生成 {total_generated} 个子场景")
    print(f"{'='*60}\n")


def generate_l4_intentions(max_intentions_per_subscenario: int = 6):
    """
    根据L3子场景生成L4用户意图。
    :param max_intentions_per_subscenario: 每个L3子场景生成的L4意图数量上限
    """
    print(f"\n{'='*60}")
    print(f"开始生成 L4 用户意图（每个L3子场景最多生成{max_intentions_per_subscenario}个意图）")
    print(f"{'='*60}\n")

    parent_items = get_items_from_db(level=3)
    if not parent_items:
        print("数据库中没有L3子场景，无法生成L4意图。")
        return

    conn = get_db_connection()
    if not conn:
        return

    total_generated = 0
    try:
        with conn.cursor() as cursor:
            for idx, parent in enumerate(parent_items, 1):
                parent_id = parent["id"]
                parent_name = parent["name"]
                print(
                    f"[{idx}/{len(parent_items)}] 处理L3子场景: {parent_name} (ID: {parent_id})"
                )

                # 生成L4意图列表
                intentions = generate_sub_items(
                    3, parent_name, 4, max_items=max_intentions_per_subscenario
                )
                time.sleep(API_DELAY)

                if not intentions:
                    print(f"  ⚠️  未能生成意图，跳过\n")
                    continue

                # 为每个意图生成描述并插入
                for intention_name in intentions:
                    cursor.execute(
                        "SELECT id FROM knowledge_base WHERE level = 4 AND parent_id = %s AND name = %s",
                        (parent_id, intention_name),
                    )
                    if cursor.fetchone():
                        print(f"  ⏭️  意图 '{intention_name}' 已存在，跳过")
                        continue

                    description = get_item_description(intention_name, 4, parent_name)
                    time.sleep(API_DELAY)

                    if description:
                        sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                        cursor.execute(sql, (4, parent_id, intention_name, description))
                        conn.commit()
                        total_generated += 1
                        print(
                            f"  ✅ 成功插入意图: '{intention_name}' (ID: {cursor.lastrowid})"
                        )
                    else:
                        print(f"  ❌ 未能生成描述，跳过: '{intention_name}'")
                print()  # 空行分隔
    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()

    print(f"\n{'='*60}")
    print(f"L4用户意图生成完成！共生成 {total_generated} 个意图")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("东方命理决策应用 - 知识库批量生成系统")
    print("=" * 60)

    # ========== 配置区域 ==========
    # 您可以根据需要调整每个层级的生成数量

    # L2: 每个L1领域生成的场景数量（建议: 5-15）
    L2_MAX_PER_L1 = 10

    # L3: 每个L2场景生成的子场景数量（建议: 5-10）
    L3_MAX_PER_L2 = 8

    # L4: 每个L3子场景生成的意图数量（建议: 5-8）
    L4_MAX_PER_L3 = 6

    # ==============================

    print(f"\n📊 生成配置:")
    print(f"  • L2场景: 每个L1领域最多 {L2_MAX_PER_L1} 个")
    print(f"  • L3子场景: 每个L2场景最多 {L3_MAX_PER_L2} 个")
    print(f"  • L4意图: 每个L3子场景最多 {L4_MAX_PER_L3} 个")
    print()

    # 批量生成所有层级
    start_time = time.time()

    # 步骤1: 生成L2场景
    generate_l2_scenarios(max_scenarios_per_domain=L2_MAX_PER_L1)

    # 步骤2: 生成L3子场景
    generate_l3_subscenarios(max_subscenarios_per_scenario=L3_MAX_PER_L2)

    # 步骤3: 生成L4用户意图
    generate_l4_intentions(max_intentions_per_subscenario=L4_MAX_PER_L3)

    # 总结
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 所有层级生成完毕！总耗时: {elapsed_time/60:.2f} 分钟")
    print("=" * 60)
    print("\n💡 提示: 运行以下SQL查看生成结果:")
    print("   SELECT level, COUNT(*) as count FROM knowledge_base GROUP BY level;")
    print()
