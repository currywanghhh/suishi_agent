"""
独立的层级生成脚本
可以单独运行，用于生成指定的某一个层级（L2、L3或L4）
"""
import os
import sys
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
            # Normalize each item to a plain string. Sometimes the LLM returns
            # objects like {"name": "..."} or other dicts; convert them safely.
            normalized = []
            for it in items:
                if isinstance(it, dict):
                    # try common keys that might contain the human-readable title
                    for k in ("name", "title", "text", "item"):
                        if k in it and isinstance(it[k], (str, int, float)):
                            normalized.append(str(it[k]))
                            break
                    else:
                        # fallback: serialize the dict to JSON (keeps content readable)
                        normalized.append(json.dumps(it, ensure_ascii=False))
                else:
                    normalized.append(str(it))

            items = normalized[:max_items]
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


def generate_specific_level(target_level: int, max_items: int):
    """
    生成指定的层级
    :param target_level: 目标层级 (2, 3, 或 4)
    :param max_items: 每个父项生成的子项数量
    """
    parent_level = target_level - 1
    level_names = {1: "L1领域", 2: "L2场景", 3: "L3子场景"}
    parent_name = level_names.get(parent_level, f"L{parent_level}")
    child_name = level_names.get(target_level, f"L{target_level}")

    print(f"\n{'='*60}")
    print(f"开始生成 {child_name}（每个{parent_name}最多生成{max_items}个）")
    print(f"{'='*60}\n")

    # 从数据库获取父级项目
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, name FROM knowledge_base WHERE level = %s", (parent_level,)
            )
            parent_items = cursor.fetchall()

            if not parent_items:
                print(f"❌ 数据库中没有{parent_name}，无法生成{child_name}。")
                return

            print(f"📊 找到 {len(parent_items)} 个{parent_name}，开始批量生成...\n")
            total_generated = 0

            for idx, parent in enumerate(parent_items, 1):
                parent_id = parent["id"]
                parent_name_str = parent["name"]
                print(
                    f"[{idx}/{len(parent_items)}] 处理: {parent_name_str} (ID: {parent_id})"
                )

                # 生成子项列表
                sub_items = generate_sub_items(
                    parent_level, parent_name_str, target_level, max_items=max_items
                )
                time.sleep(API_DELAY)

                if not sub_items:
                    print(f"  ⚠️  未能生成，跳过\n")
                    continue

                # 为每个子项生成描述并插入
                for item_name in sub_items:
                    # Ensure item_name is a plain string before using in SQL
                    if isinstance(item_name, dict):
                        # try common keys
                        for k in ("name", "title", "text", "item"):
                            if k in item_name and isinstance(item_name[k], (str, int, float)):
                                item_name_str = str(item_name[k])
                                break
                        else:
                            item_name_str = json.dumps(item_name, ensure_ascii=False)
                    else:
                        item_name_str = str(item_name)

                    cursor.execute(
                        "SELECT id FROM knowledge_base WHERE level = %s AND parent_id = %s AND name = %s",
                        (target_level, parent_id, item_name_str),
                    )
                    if cursor.fetchone():
                        print(f"  ⏭️  '{item_name_str}' 已存在，跳过")
                        continue

                    description = get_item_description(
                        item_name_str, target_level, parent_name_str
                    )
                    time.sleep(API_DELAY)

                    if description:
                        sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                        cursor.execute(
                            sql, (target_level, parent_id, item_name_str, description)
                        )
                        conn.commit()
                        total_generated += 1
                        print(f"  ✅ 成功插入: '{item_name}' (ID: {cursor.lastrowid})")
                    else:
                        print(f"  ❌ 未能生成描述，跳过: '{item_name}'")
                print()

            print(f"\n{'='*60}")
            print(f"🎉 {child_name}生成完成！共生成 {total_generated} 个")
            print(f"{'='*60}\n")

    except mysql.connector.Error as err:
        print(f"❌ 数据库错误: {err}")
    finally:
        if conn.is_connected():
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成指定层级的知识库内容")
    parser.add_argument(
        "--level",
        type=int,
        choices=[2, 3, 4],
        required=True,
        help="要生成的层级: 2(L2场景), 3(L3子场景), 4(L4意图)",
    )
    parser.add_argument(
        "--max", type=int, default=None, help="每个父项生成的子项数量（默认：L2=10, L3=8, L4=6）"
    )

    args = parser.parse_args()

    # 根据层级使用默认配置
    if args.max is None:
        default_max = {
            2: L2_CONFIG["max_per_parent"],
            3: L3_CONFIG["max_per_parent"],
            4: L4_CONFIG["max_per_parent"],
        }
        args.max = default_max.get(args.level, 10)

    print("\n" + "=" * 60)
    print("东方命理决策应用 - 单层级生成工具")
    print("=" * 60)

    generate_specific_level(args.level, args.max)

    print("\n💡 提示: 运行以下SQL查看生成结果:")
    print(f"   SELECT COUNT(*) FROM knowledge_base WHERE level = {args.level};")
