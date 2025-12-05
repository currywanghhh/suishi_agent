import os
import mysql.connector
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
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


def call_llm(prompt: str, is_json_output: bool = False) -> str:
    """
    Calls the LLM API.
    """
    if MODEL_PROVIDER != "ollama" and not API_KEY:
        raise ValueError(f"Error: API Key environment variable not set for {MODEL_PROVIDER}.")

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
        "max_tokens": 2048,  # Increased for detailed content
        "temperature": 0.7,
    }

    # 只在支持的提供商上启用 JSON 模式
    if is_json_output and SUPPORTS_JSON_MODE:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            API_URL, headers=headers, data=json.dumps(payload), timeout=120
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        return None


def setup_l4_content_table(cursor):
    """Creates the l4_content table if it doesn't exist."""
    sql = """
    CREATE TABLE IF NOT EXISTS l4_content (
        id INT AUTO_INCREMENT PRIMARY KEY,
        l4_id INT NOT NULL,
        five_elements_insight TEXT,
        action_guide TEXT,
        communication_scripts TEXT,
        energy_harmonization TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (l4_id) REFERENCES knowledge_base(id) ON DELETE CASCADE,
        UNIQUE KEY unique_l4 (l4_id)
    )
    """
    cursor.execute(sql)
    print("Ensured table 'l4_content' exists.")


def get_full_path(cursor, l4_id):
    """Retrieves the full path (L1 > L2 > L3 > L4) for a given L4 ID."""
    # Get L4
    cursor.execute(
        "SELECT name, parent_id, description_en FROM knowledge_base WHERE id = %s",
        (l4_id,),
    )
    l4 = cursor.fetchone()
    if not l4:
        return None
    l4_name, l3_id, l4_desc = l4

    # Get L3
    cursor.execute(
        "SELECT name, parent_id, description_en FROM knowledge_base WHERE id = %s",
        (l3_id,),
    )
    l3 = cursor.fetchone()
    if not l3:
        return None
    l3_name, l2_id, l3_desc = l3

    # Get L2
    cursor.execute(
        "SELECT name, parent_id, description_en FROM knowledge_base WHERE id = %s",
        (l2_id,),
    )
    l2 = cursor.fetchone()
    if not l2:
        return None
    l2_name, l1_id, l2_desc = l2

    # Get L1
    cursor.execute(
        "SELECT name, description_en FROM knowledge_base WHERE id = %s", (l1_id,)
    )
    l1 = cursor.fetchone()
    if not l1:
        return None
    l1_name, l1_desc = l1

    return {
        "L1": {"name": l1_name, "desc": l1_desc},
        "L2": {"name": l2_name, "desc": l2_desc},
        "L3": {"name": l3_name, "desc": l3_desc},
        "L4": {"name": l4_name, "desc": l4_desc},
    }


def generate_content_for_l4(path_info):
    """Generates the 4 sections of content for an L4 intention."""

    prompt = f"""
    You are an expert content creator for a "Personal Energy Management" app based on Eastern Five Elements (Wu Xing) metaphysics.
    
    **Context:**
    - Domain (L1): {path_info['L1']['name']} ({path_info['L1']['desc']})
    - Scenario (L2): {path_info['L2']['name']} ({path_info['L2']['desc']})
    - Sub-scenario (L3): {path_info['L3']['name']} ({path_info['L3']['desc']})
    - User Intention (L4): {path_info['L4']['name']} ({path_info['L4']['desc']})
    
    **Task:**
    Generate detailed, actionable, and empathetic content for this specific user intention.
    The content must be divided into exactly these four sections:
    
    1. **Five Elements Insight (五行洞察)**: Analyze the situation using Five Elements theory (Wood, Fire, Earth, Metal, Water). Explain the energy dynamics at play. Which element is weak? Which is strong? What is the conflict?
    2. **Action Guide (行动指南)**: Provide 3-5 concrete, practical steps the user can take immediately. These should be real-world actions, not just abstract advice.
    3. **Communication Scripts (沟通话术)**: Provide 2-3 specific scripts or phrases the user can say to others involved in this situation (or to themselves as affirmations).
    4. **Energy Harmonization (能量调和)**: Suggest small rituals, colors to wear, directions to face, or mindset shifts to balance the energy.
    
    **Requirements:**
    - Output MUST be in **JSON format**.
    - Keys: "five_elements_insight", "action_guide", "communication_scripts", "energy_harmonization".
    - Language: **English** (as the target market is North America).
    - Tone: Empathetic, wise, practical, modern, and supportive. Avoid overly mystical jargon without explanation.
    """

    response = call_llm(prompt, is_json_output=True)
    if not response:
        return None

    try:
        # Clean up potential markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        return json.loads(response)
    except json.JSONDecodeError:
        print("Failed to parse JSON response.")
        return None


def main():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        setup_l4_content_table(cursor)

        # Find L4 items that don't have content yet
        print("Fetching L4 items without content...")
        cursor.execute(
            """
            SELECT kb.id, kb.name 
            FROM knowledge_base kb
            LEFT JOIN l4_content c ON kb.id = c.l4_id
            WHERE kb.level = 4 AND c.id IS NULL
        """
        )
        l4_items = cursor.fetchall()

        print(f"Found {len(l4_items)} L4 items needing content.")

        for l4_id, l4_name in l4_items:
            print(f"\nProcessing L4 ID {l4_id}: {l4_name}...")

            path_info = get_full_path(cursor, l4_id)
            if not path_info:
                print(f"Could not retrieve full path for L4 ID {l4_id}. Skipping.")
                continue

            content = generate_content_for_l4(path_info)

            if content:
                # Helper to ensure string format
                def to_str(val):
                    if isinstance(val, list):
                        return "\n".join(str(v) for v in val)
                    if isinstance(val, dict):
                        return json.dumps(val, ensure_ascii=False)
                    return str(val)

                # Insert into database
                sql = """
                INSERT INTO l4_content 
                (l4_id, five_elements_insight, action_guide, communication_scripts, energy_harmonization)
                VALUES (%s, %s, %s, %s, %s)
                """
                val = (
                    l4_id,
                    to_str(content.get("five_elements_insight", "")),
                    to_str(content.get("action_guide", "")),
                    to_str(content.get("communication_scripts", "")),
                    to_str(content.get("energy_harmonization", "")),
                )
                cursor.execute(sql, val)
                conn.commit()
                print(f"Successfully generated and saved content for '{l4_name}'.")
            else:
                print(f"Failed to generate content for '{l4_name}'.")

            # Sleep to avoid rate limits
            time.sleep(1)

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
