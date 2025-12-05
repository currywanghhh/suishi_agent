import os
import mysql.connector
import requests
import json
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 配置区域 ---

# --- 全局配置 ---
# 根据环境变量选择 API 提供商
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "silicon_flow").lower()

if MODEL_PROVIDER == "openrouter":
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    LLM_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    SUPPORTS_JSON_MODE = True
elif MODEL_PROVIDER == "ollama":
    API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1/chat/completions")
    API_KEY = None
    LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    SUPPORTS_JSON_MODE = False
else:  # silicon_flow
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEY = os.getenv("SILICON_FLOW_API_KEY")
    LLM_MODEL = os.getenv("SILICON_FLOW_MODEL", "deepseek-ai/DeepSeek-R1")
    SUPPORTS_JSON_MODE = True

print(f"ℹ️ 使用模型提供商: {MODEL_PROVIDER}")
print(f"ℹ️ 使用模型: {LLM_MODEL}")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


# --- 函数定义 ---


def call_llm(prompt: str, is_json_output: bool = False) -> str:
    """
    调用大模型API的通用函数。
    :param prompt: 发送给大模型的提示词。
    :param is_json_output: 是否期望返回JSON格式的响应。
    :return: 大模型的响应内容字符串。
    """
    if MODEL_PROVIDER != "ollama" and not API_KEY:
        raise ValueError(f"错误：API Key 环境变量未设置。请检查 {MODEL_PROVIDER.upper()}_API_KEY")

    headers = {
        "Content-Type": "application/json",
    }

    # 添加认证头
    if API_KEY:
        if MODEL_PROVIDER == "openrouter":
            headers["Authorization"] = f"Bearer {API_KEY}"
            headers["HTTP-Referer"] = "https://github.com/yourusername/wu-xing-advisor"
            headers["X-Title"] = "Wu Xing Decision Advisor Data Generation"
        else:
            headers["Authorization"] = f"Bearer {API_KEY}"

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.7,
    }
    
    # 只在支持的提供商上启用 JSON 模式
    if is_json_output and SUPPORTS_JSON_MODE:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            API_URL, headers=headers, data=json.dumps(payload), timeout=60
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        return None


def generate_l1_domains(max_domains: int = 100) -> list:
    """
    调用大模型生成L1领域的列表。
    :param max_domains: 生成的领域数量上限，默认100条。
    """
    print(f"正在调用大模型生成L1领域列表（最多{max_domains}条）...")
    prompt = f"""
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
    {{
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
    }}
    
    Now generate a comprehensive L1 domain list (aim for {max_domains} or fewer):
    """

    response_str = call_llm(prompt, is_json_output=True)
    if not response_str:
        print("未能从大模型获取L1领域列表。")
        return []

    try:
        # 解析JSON响应
        data = json.loads(response_str)
        domains = data.get("domains", [])
        if isinstance(domains, list) and all(isinstance(item, str) for item in domains):
            # 限制数量不超过max_domains
            domains = domains[:max_domains]
            print(f"成功生成{len(domains)}个L1领域: {domains}")
            return domains
        else:
            print("错误：大模型返回的JSON格式不正确。")
            return []
    except json.JSONDecodeError:
        print(f"错误：无法解析大模型返回的JSON: {response_str}")
        return []


def get_domain_description(domain_name: str) -> str:
    """
    调用大模型为给定的领域生成描述。
    """
    print(f"  -> 正在为 '{domain_name}' 生成描述...")
    prompt = f"""
    You are a content writer for a subscription-based iOS app that helps North American users make life decisions using Eastern metaphysics and practical guidance.
    
    **Product Context:**
    - The app combines Eastern divination (Five Elements theory, astrology) with actionable advice.
    - Users are primarily from YouTube/Instagram who are interested in astrology, Eastern philosophy, and need help with decision-making.
    - The goal is to help users feel confident and happy about their life choices.
    
    **Your Task:**
    Write a short, engaging, and empowering description for the L1 Domain: "{domain_name}".
    
    **Requirements:**
    1. Write in English, 2-3 sentences.
    2. Speak directly to users who struggle with choices in this area.
    3. Emphasize how the app helps them gain clarity and make confident decisions.
    4. Use warm, encouraging, and accessible language (not overly mystical or academic).
    5. Make it relatable to modern North American life.
    
    **Example for "Career & Professional Development":**
    "Feeling stuck in your career or unsure about your next move? Discover your professional path aligned with your cosmic energy. Get clear, actionable guidance to make career decisions that lead to fulfillment and success."
    
    Now write the description for: "{domain_name}"
    """

    description = call_llm(prompt)
    if description and description.startswith('"') and description.endswith('"'):
        description = description[1:-1]
    return description


def setup_database():
    """
    连接数据库，生成并插入L1领域知识。
    """
    # 1. 首先，动态生成L1领域
    l1_domains = generate_l1_domains()
    if not l1_domains:
        print("无法继续，因为L1领域列表为空。")
        return

    try:
        # 2. 连接数据库并插入数据
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("\n成功连接到数据库。")

        # 遍历动态生成的L1领域列表
        for domain in l1_domains:
            print(f"正在处理领域: {domain}...")

            # 检查数据库中是否已存在该领域
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE level = 1 AND name = %s", (domain,)
            )
            if cursor.fetchone():
                print(f"-> 领域 '{domain}' 已存在，跳过。")
                continue

            # 3. 为每个领域生成描述
            description = get_domain_description(domain)

            if description:
                # 4. 插入数据到数据库
                sql = "INSERT INTO knowledge_base (level, parent_id, name, description_en) VALUES (%s, %s, %s, %s)"
                val = (1, None, domain, description)
                cursor.execute(sql, val)
                conn.commit()
                print(f"  -> 成功插入 '{domain}' (ID: {cursor.lastrowid}).")
            else:
                print(f"  -> 未能为 '{domain}' 生成描述，跳过插入。")

    except mysql.connector.Error as err:
        if err.errno == 1049:  # Unknown database
            print(f"数据库错误: 数据库 '{DB_CONFIG['database']}' 不存在。请先创建数据库。")
        elif err.errno == 1045:  # Access denied
            print(f"数据库错误: 用户 '{DB_CONFIG['user']}' 访问被拒绝。请检查您的 .env 文件中的用户名和密码。")
        else:
            print(f"数据库错误: {err}")
    except ValueError as ve:
        print(ve)
    finally:
        # 关闭连接
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("\n数据库连接已关闭。")


# --- 主程序入口 ---
if __name__ == "__main__":
    setup_database()
