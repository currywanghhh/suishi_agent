"""
针对指定L1领域生成完整子树的脚本
可以指定某个L1领域（通过名称或ID），为其生成完整的L2→L3→L4层级结构
"""
import os
import mysql.connector
import requests
import json
from dotenv import load_dotenv
import time
import argparse

# 加载环境变量
load_dotenv()

# 导入配置
try:
    from config import L2_CONFIG, L3_CONFIG, L4_CONFIG, API_CONFIG
except ImportError:
    print("警告：未找到config.py，使用默认配置")
    L2_CONFIG = {"max_per_parent": 10}
    L3_CONFIG = {"max_per_parent": 8}
    L4_CONFIG = {"max_per_parent": 6}
    API_CONFIG = {"delay_between_calls": 1}

# 全局配置
SILICON_FLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
LLM_MODEL = "alibaba/Qwen2-7B-Instruct"
API_DELAY = API_CONFIG.get("delay_between_calls", 1)


def get_db_connection():
    """建立并返回数据库连接"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"❌ 数据库连接错误: {err}")
        return None


def call_llm(prompt: str, is_json_output: bool = False) -> str:
    """调用大模型API"""
    if not SILICON_FLOW_API_KEY:
        raise ValueError("错误：环境变量 SILICON_FLOW_API_KEY 未设置。")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
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


def find_l1_domain(search_term: str):
    """
    查找L1领域（支持通过ID或名称模糊搜索）
    :param search_term: L1领域的ID或名称关键词
    :return: L1领域信息字典，或None
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(dictionary=True) as cursor:
            # 首先尝试作为ID搜索
            if search_term.isdigit():
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE level = 1 AND id = %s",
                    (int(search_term),),
                )
                result = cursor.fetchone()
                if result:
                    return result

            # 尝试精确匹配名称
            cursor.execute(
                "SELECT id, name FROM knowledge_base WHERE level = 1 AND name = %s",
                (search_term,),
            )
            result = cursor.fetchone()
            if result:
                return result

            # 尝试模糊匹配（不区分大小写）
            cursor.execute(
                "SELECT id, name FROM knowledge_base WHERE level = 1 AND LOWER(name) LIKE LOWER(%s)",
                (f"%{search_term}%",),
            )
            results = cursor.fetchall()

            if len(results) == 1:
                return results[0]
            elif len(results) > 1:
                print(f"\n⚠️  找到多个匹配的L1领域，请更精确地指定：")
                for r in results:
                    print(f"   ID: {r['id']} - {r['name']}")
                return None
            else:
                print(f"\n❌ 未找到匹配的L1领域：'{search_term}'")
                return None
    finally:
        if conn.is_connected():
            conn.close()


def list_all_l1_domains():
    """列出所有L1领域"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, name FROM knowledge_base WHERE level = 1 ORDER BY id"
            )
            domains = cursor.fetchall()

            if not domains:
                print("\n❌ 数据库中还没有L1领域，请先运行 create_knowledge_base.py")
                return

            print(f"\n📋 当前数据库中的所有L1领域（共{len(domains)}个）：")
            print("=" * 70)
            for domain in domains:
                print(f"  ID: {domain['id']:3d} | {domain['name']}")
            print("=" * 70)
    finally:
        if conn.is_connected():
            conn.close()


def generate_sub_items(
    parent_level: int, parent_name: str, child_level: int, max_items: int = 10
) -> list:
    """为给定的父项生成子项列表"""
    level_map = {
        2: "L2 场景(Scenarios)",
        3: "L3 子场景(Sub-scenarios)",
        4: "L4 意图(User Intentions)",
    }
    child_type = level_map.get(child_level, "items")

    if child_level == 2:
        task_description = f"""
        Generate specific SCENARIOS (场景) within the L1 Domain "{parent_name}".
        Scenarios are common situations or contexts where users need to make decisions.
        
        Examples for "Love & Romance": 
        - "Dating & Finding a Partner"
        - "Relationship Conflicts"
        - "Long-Distance Relationships"
        """
    elif child_level == 3:
        task_description = f"""
        Generate specific SUB-SCENARIOS (子场景) within the L2 Scenario "{parent_name}".
        Sub-scenarios are more detailed, actionable situations within a scenario.
        
        Examples for L2 "Dating & Finding a Partner":
        - "First Date Preparation"
        - "Online Dating Profile"
        - "Expressing Romantic Interest"
        """
    else:  # child_level == 4
        task_description = f"""
        Generate specific USER INTENTIONS (意图) within the L3 Sub-scenario "{parent_name}".
        Intentions are concrete questions or goals users have in this context.
        
        Examples for L3 "First Date Preparation":
        - "What should I wear on the first date?"
        - "How do I make a good first impression?"
        - "Should I suggest a second date?"
        """

    prompt = f"""
    You are a content strategist for a decision-making app based on Eastern metaphysics, targeting North American users.
    
    **Current Task:**
    {task_description}
    
    **Parent Context:** "{parent_name}"
    
    **Requirements:**
    1. Output in English only.
    2. Each item should be a specific, relatable situation for North American users.
    3. Think about what real users would search for or ask about.
    4. Return as JSON: {{"items": ["item1", "item2", ...]}}
    5. Generate 5-{max_items} items.
    
    Generate the {child_type}:
    """

    response_str = call_llm(prompt, is_json_output=True)
    if not response_str:
        return []

    try:
        data = json.loads(response_str)
        items = data.get("items") or data.get(list(data.keys())[0], [])
        if isinstance(items, list):
            items = items[:max_items]
            return items
        return []
    except (json.JSONDecodeError, IndexError):
        print(f"  -> 无法解析JSON: {response_str}")
        return []


def get_item_description(name: str, level: int, parent_name: str) -> str:
    """为给定的项生成描述"""
    level_map = {2: "L2 场景", 3: "L3 子场景", 4: "L4 用户意图"}
    item_type = level_map.get(level, "Item")

    prompt = f"""
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
    """
    description = call_llm(prompt)
    if description and description.startswith('"') and description.endswith('"'):
        description = description[1:-1]
    return description


def generate_for_specific_l1(
    l1_id: int,
    l1_name: str,
    generate_l2: bool = True,
    max_l2: int = 10,
    generate_l3: bool = True,
    max_l3: int = 8,
    generate_l4: bool = True,
    max_l4: int = 6,
):
    """
    为指定的L1领域生成完整的子树
    """
    print(f"\n{'='*70}")
    print(f"🎯 开始为L1领域生成完整子树")
    print(f"{'='*70}")
    print(f"📌 目标领域: {l1_name} (ID: {l1_id})")
    print(f"📊 生成配置:")
    if generate_l2:
        print(f"   ✅ L2场景: 最多 {max_l2} 个")
    if generate_l3:
        print(f"   ✅ L3子场景: 每个L2最多 {max_l3} 个")
    if generate_l4:
        print(f"   ✅ L4意图: 每个L3最多 {max_l4} 个")
    print(f"{'='*70}\n")

    conn = get_db_connection()
    if not conn:
        return

    stats = {"l2": 0, "l3": 0, "l4": 0}

    try:
        with conn.cursor(dictionary=True) as cursor:
            # ========== 步骤1: 生成L2场景 ==========
            if generate_l2:
                print(f"\n{'─'*70}")
                print(f"📍 步骤1: 生成L2场景")
                print(f"{'─'*70}")

                scenarios = generate_sub_items(1, l1_name, 2, max_items=max_l2)
                time.sleep(API_DELAY)

                if scenarios:
                    print(f"💡 为 '{l1_name}' 生成了 {len(scenarios)} 个场景\n")
                    for idx, scenario_name in enumerate(scenarios, 1):
                        cursor.execute(
                            "SELECT id FROM knowledge_base WHERE level = 2 AND parent_id = %s AND name = %s",
                            (l1_id, scenario_name),
                        )
                        if cursor.fetchone():
                            print(
                                f"  [{idx}/{len(scenarios)}] ⏭️  '{scenario_name}' 已存在"
                            )
                            continue

                        description = get_item_description(scenario_name, 2, l1_name)
                        time.sleep(API_DELAY)

                        if description:
                            sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                            cursor.execute(sql, (2, l1_id, scenario_name, description))
                            conn.commit()
                            stats["l2"] += 1
                            print(
                                f"  [{idx}/{len(scenarios)}] ✅ '{scenario_name}' (ID: {cursor.lastrowid})"
                            )
                else:
                    print(f"⚠️  未能生成L2场景")

            # ========== 步骤2: 生成L3子场景 ==========
            if generate_l3:
                print(f"\n{'─'*70}")
                print(f"📍 步骤2: 生成L3子场景")
                print(f"{'─'*70}")

                # 获取该L1下的所有L2
                cursor.execute(
                    "SELECT id, name FROM knowledge_base WHERE level = 2 AND parent_id = %s",
                    (l1_id,),
                )
                l2_items = cursor.fetchall()

                if not l2_items:
                    print(f"⚠️  该L1领域下没有L2场景，跳过L3生成")
                else:
                    print(f"💡 找到 {len(l2_items)} 个L2场景，开始生成L3\n")
                    for l2_idx, l2_item in enumerate(l2_items, 1):
                        l2_id = l2_item["id"]
                        l2_name = l2_item["name"]
                        print(f"  [{l2_idx}/{len(l2_items)}] 处理L2: {l2_name}")

                        subscenarios = generate_sub_items(
                            2, l2_name, 3, max_items=max_l3
                        )
                        time.sleep(API_DELAY)

                        if subscenarios:
                            for subscenario_name in subscenarios:
                                cursor.execute(
                                    "SELECT id FROM knowledge_base WHERE level = 3 AND parent_id = %s AND name = %s",
                                    (l2_id, subscenario_name),
                                )
                                if cursor.fetchone():
                                    print(f"    ⏭️  '{subscenario_name}' 已存在")
                                    continue

                                description = get_item_description(
                                    subscenario_name, 3, l2_name
                                )
                                time.sleep(API_DELAY)

                                if description:
                                    sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                                    cursor.execute(
                                        sql, (3, l2_id, subscenario_name, description)
                                    )
                                    conn.commit()
                                    stats["l3"] += 1
                                    print(
                                        f"    ✅ '{subscenario_name}' (ID: {cursor.lastrowid})"
                                    )
                        print()

            # ========== 步骤3: 生成L4用户意图 ==========
            if generate_l4:
                print(f"\n{'─'*70}")
                print(f"📍 步骤3: 生成L4用户意图")
                print(f"{'─'*70}")

                # 获取该L1下的所有L3（通过L2关联）
                cursor.execute(
                    """
                    SELECT l3.id, l3.name 
                    FROM knowledge_base l3
                    JOIN knowledge_base l2 ON l3.parent_id = l2.id
                    WHERE l3.level = 3 AND l2.parent_id = %s
                """,
                    (l1_id,),
                )
                l3_items = cursor.fetchall()

                if not l3_items:
                    print(f"⚠️  该L1领域下没有L3子场景，跳过L4生成")
                else:
                    print(f"💡 找到 {len(l3_items)} 个L3子场景，开始生成L4\n")
                    for l3_idx, l3_item in enumerate(l3_items, 1):
                        l3_id = l3_item["id"]
                        l3_name = l3_item["name"]
                        print(f"  [{l3_idx}/{len(l3_items)}] 处理L3: {l3_name}")

                        intentions = generate_sub_items(3, l3_name, 4, max_items=max_l4)
                        time.sleep(API_DELAY)

                        if intentions:
                            for intention_name in intentions:
                                cursor.execute(
                                    "SELECT id FROM knowledge_base WHERE level = 4 AND parent_id = %s AND name = %s",
                                    (l3_id, intention_name),
                                )
                                if cursor.fetchone():
                                    print(f"    ⏭️  '{intention_name}' 已存在")
                                    continue

                                description = get_item_description(
                                    intention_name, 4, l3_name
                                )
                                time.sleep(API_DELAY)

                                if description:
                                    sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                                    cursor.execute(
                                        sql, (4, l3_id, intention_name, description)
                                    )
                                    conn.commit()
                                    stats["l4"] += 1
                                    print(
                                        f"    ✅ '{intention_name}' (ID: {cursor.lastrowid})"
                                    )
                        print()

    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()

    # 总结
    print(f"\n{'='*70}")
    print(f"🎉 生成完成！")
    print(f"{'='*70}")
    print(f"📊 统计信息:")
    print(f"   • L2场景: 新增 {stats['l2']} 个")
    print(f"   • L3子场景: 新增 {stats['l3']} 个")
    print(f"   • L4意图: 新增 {stats['l4']} 个")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="为指定的L1领域生成完整的L2→L3→L4子树",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 列出所有L1领域
  python generate_for_l1.py --list

  # 通过ID指定L1领域，生成完整子树
  python generate_for_l1.py --l1 1

  # 通过名称模糊搜索（不区分大小写）
  python generate_for_l1.py --l1 "Career"

  # 自定义各层级数量
  python generate_for_l1.py --l1 1 --max-l2 15 --max-l3 10 --max-l4 8

  # 只生成L2，不生成L3和L4
  python generate_for_l1.py --l1 1 --skip-l3 --skip-l4
        """,
    )

    parser.add_argument("--list", action="store_true", help="列出所有L1领域及其ID")
    parser.add_argument("--l1", type=str, help="L1领域的ID或名称（支持模糊搜索）")
    parser.add_argument(
        "--max-l2",
        type=int,
        default=L2_CONFIG["max_per_parent"],
        help=f'L2场景数量（默认: {L2_CONFIG["max_per_parent"]}）',
    )
    parser.add_argument(
        "--max-l3",
        type=int,
        default=L3_CONFIG["max_per_parent"],
        help=f'每个L2生成的L3数量（默认: {L3_CONFIG["max_per_parent"]}）',
    )
    parser.add_argument(
        "--max-l4",
        type=int,
        default=L4_CONFIG["max_per_parent"],
        help=f'每个L3生成的L4数量（默认: {L4_CONFIG["max_per_parent"]}）',
    )
    parser.add_argument("--skip-l2", action="store_true", help="跳过L2生成")
    parser.add_argument("--skip-l3", action="store_true", help="跳过L3生成")
    parser.add_argument("--skip-l4", action="store_true", help="跳过L4生成")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("🎯 东方命理决策应用 - 指定L1领域生成工具")
    print("=" * 70)

    # 如果只是列出L1
    if args.list:
        list_all_l1_domains()
        print("\n💡 使用 --l1 参数指定要生成的领域，例如:")
        print("   python generate_for_l1.py --l1 1")
        print('   python generate_for_l1.py --l1 "Career"')
        exit(0)

    # 必须指定L1
    if not args.l1:
        parser.print_help()
        print("\n❌ 错误: 必须使用 --l1 参数指定L1领域，或使用 --list 查看所有领域")
        exit(1)

    # 查找L1领域
    l1_domain = find_l1_domain(args.l1)
    if not l1_domain:
        print("\n💡 提示: 使用 --list 参数查看所有可用的L1领域")
        exit(1)

    # 开始生成
    generate_for_specific_l1(
        l1_id=l1_domain["id"],
        l1_name=l1_domain["name"],
        generate_l2=not args.skip_l2,
        max_l2=args.max_l2,
        generate_l3=not args.skip_l3,
        max_l3=args.max_l3,
        generate_l4=not args.skip_l4,
        max_l4=args.max_l4,
    )
