import os
import mysql.connector
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
SILICON_FLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
LLM_MODEL = "deepseek-ai/DeepSeek-R1"


def call_llm(prompt: str, is_json_output: bool = False) -> str:
    """
    Calls the LLM API.
    """
    if not SILICON_FLOW_API_KEY:
        raise ValueError("Error: SILICON_FLOW_API_KEY environment variable not set.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,  # Lower temperature for classification/routing
    }

    if is_json_output:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            SILICON_FLOW_API_URL, headers=headers, data=json.dumps(payload), timeout=60
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


def find_best_l4_match(user_query, cursor):
    """
    Finds the best matching L4 intention for the user query.
    """
    # 1. Keyword Search (Naive) - Get top 20 candidates based on keyword overlap or just fetch all L4s if count is small.
    # Since we have a limited number of L4s generated so far, we can fetch all L4s that HAVE content.

    cursor.execute(
        """
        SELECT kb.id, kb.name, kb.description_en 
        FROM knowledge_base kb
        JOIN l4_content c ON kb.id = c.l4_id
        WHERE kb.level = 4
    """
    )
    candidates = cursor.fetchall()

    if not candidates:
        return None

    # If we have too many candidates, we might need a better filter.
    # For now, let's assume < 50 candidates and pass them all to LLM.
    # If > 50, we might want to do a keyword filter first.

    if len(candidates) > 50:
        # Simple keyword filter: check if any word in query appears in name/desc
        keywords = user_query.lower().split()
        filtered_candidates = []
        for cid, name, desc in candidates:
            text = (name + " " + (desc or "")).lower()
            score = sum(1 for k in keywords if k in text)
            if score > 0:
                filtered_candidates.append((cid, name, desc, score))

        # Sort by score and take top 20
        filtered_candidates.sort(key=lambda x: x[3], reverse=True)
        candidates = [(c[0], c[1], c[2]) for c in filtered_candidates[:20]]

        # If still no candidates (no keyword match), fallback to random sample or just fail?
        # Let's fallback to top 10 generic ones or just fail.
        if not candidates:
            # Fallback: just take first 10
            cursor.execute(
                """
                SELECT kb.id, kb.name, kb.description_en 
                FROM knowledge_base kb
                JOIN l4_content c ON kb.id = c.l4_id
                WHERE kb.level = 4
                LIMIT 10
            """
            )
            candidates = cursor.fetchall()

    # 2. LLM Selection
    candidates_str = "\n".join([f"ID {c[0]}: {c[1]} ({c[2]})" for c in candidates])

    prompt = f"""
    User Query: "{user_query}"
    
    Available Intentions:
    {candidates_str}
    
    Task: Select the single best matching Intention ID from the list above that addresses the user's query.
    If none are a good match, return 0.
    
    Return ONLY the ID number.
    """

    response = call_llm(prompt)
    if not response:
        return None

    try:
        # Extract number from response
        import re

        match = re.search(r"\d+", response)
        if match:
            best_id = int(match.group())
            return best_id if best_id != 0 else None
    except:
        pass

    return None


def get_l4_content(l4_id, cursor):
    """Retrieves content for a specific L4 ID."""
    cursor.execute(
        """
        SELECT five_elements_insight, action_guide, communication_scripts, energy_harmonization
        FROM l4_content
        WHERE l4_id = %s
    """,
        (l4_id,),
    )
    return cursor.fetchone()


def main():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("--- Personal Energy Management App Interaction Test ---")
        print("Type 'exit' to quit.\n")

        while True:
            user_query = input("User: ")
            if user_query.lower() in ("exit", "quit"):
                break

            print("Thinking...")
            best_l4_id = find_best_l4_match(user_query, cursor)

            if best_l4_id:
                content = get_l4_content(best_l4_id, cursor)
                if content:
                    insight, action, scripts, energy = content

                    # Get L4 Name for context
                    cursor.execute(
                        "SELECT name FROM knowledge_base WHERE id = %s", (best_l4_id,)
                    )
                    l4_name = cursor.fetchone()[0]

                    print(f"\nMatched Intention: {l4_name}\n")
                    print(f"--- Five Elements Insight ---\n{insight}\n")
                    print(f"--- Action Guide ---\n{action}\n")
                    print(f"--- Communication Scripts ---\n{scripts}\n")
                    print(f"--- Energy Harmonization ---\n{energy}\n")
                else:
                    print("Found intention but no content available.")
            else:
                print("Sorry, I couldn't find a relevant topic in the knowledge base.")

            print("-" * 50)

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
