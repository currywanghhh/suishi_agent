import os
import json
import time
import mysql.connector
import requests
from django.shortcuts import render
from django.http import StreamingHttpResponse
from dotenv import load_dotenv

load_dotenv()

# Configuration
# LLM Provider: 'silicon_flow' or 'ollama'
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama').strip('"').strip("'").lower()

# Silicon Flow Configuration
SILICON_FLOW_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'
SILICON_FLOW_API_KEY = os.getenv('SILICON_FLOW_API_KEY')
if SILICON_FLOW_API_KEY:
    SILICON_FLOW_API_KEY = SILICON_FLOW_API_KEY.strip('"').strip("'")

# Ollama Configuration
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/chat').strip('"').strip("'")
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'gemma3:4b').strip('"').strip("'")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost').strip('"').strip("'"),
    'user': os.getenv('DB_USER', 'root').strip('"').strip("'"),
    'password': os.getenv('DB_PASSWORD', '').strip('"').strip("'"),
    'database': os.getenv('DB_NAME', 'mysql').strip('"').strip("'"),
    'pool_name': 'mypool',
    'pool_size': 5,
    'pool_reset_session': True,
    'autocommit': True
}

# LLM Model (根据provider自动选择)
if LLM_PROVIDER == 'ollama':
    LLM_MODEL = OLLAMA_MODEL
    LLM_API_URL = OLLAMA_API_URL
    LLM_API_KEY = None  # Ollama不需要API Key
else:
    LLM_MODEL = "Qwen/Qwen3-32B"
    LLM_API_URL = SILICON_FLOW_API_URL
    LLM_API_KEY = SILICON_FLOW_API_KEY

# 会话管理：存储多轮对话历史（生产环境应使用 Redis/数据库）
SESSION_STORE = {}
# 结构: {session_id: {'history': [{'role': 'user', 'content': '...'}, ...], 'l4_id': int, 'l4_content': dict}}

def get_or_create_session(session_id):
    """获取或创建会话"""
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {
            'history': [],
            'l4_id': None,
            'l4_content': None
        }
    return SESSION_STORE[session_id]

def add_to_history(session_id, role, content):
    """添加消息到会话历史"""
    session = get_or_create_session(session_id)
    session['history'].append({'role': role, 'content': content})
    # 限制历史长度（保留最近10轮）
    if len(session['history']) > 20:  # 10轮对话 = 20条消息
        session['history'] = session['history'][-20:]


def index(request):
    """Render the main advisor interface"""
    return render(request, 'advisor/index.html')

# ========== 简化版配置（移除复杂的人格映射） ==========
# 直接、简单的决策顾问 - 不需要复杂的人格切换

# ========== V4 新增：文化映射表加载 ==========
def load_cultural_mapping():
    """加载50州文化映射表"""
    try:
        mapping_path = os.path.join(os.path.dirname(__file__), 'cultural_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[Cultural] Failed to load mapping: {e}")
        return None

def get_cultural_context(state_name):
    """根据用户所在州获取文化上下文提示"""
    mapping = load_cultural_mapping()
    if not mapping:
        return ""
    
    if state_name and state_name in mapping.get('states', {}):
        state_info = mapping['states'][state_name]
        return f"""
=== Cultural Context - FOR YOUR REFERENCE ONLY ===
{state_info['prompt_text']}

IMPORTANT: Use this cultural background to INFORM your advice style, but:
- DO NOT mention the state name (e.g., "Since you're from Kentucky...")
- DO NOT explicitly reference their location
- Instead, naturally adapt your tone, examples, and suggestions to resonate with their background
- Say things like "given your values" or "based on what matters to you" if needed
===
"""
    return ""

def build_contextualized_prompt(user_query, l4_info, conversation_history, bazi_text=None, user_state=None):
    """构建基于五行理论的直接决策 prompt"""
    
    # 系统角色：五行决策顾问
    system_role = """You are a Wu Xing (Five Elements) personal growth advisor who empowers users to become their strongest, best selves.

Core Mission:
Every piece of advice you give should help the user GROW STRONGER, make BETTER DECISIONS, and become a MORE CAPABLE person. Frame your guidance as tools for self-improvement and personal mastery.

Five Elements Principles (use the CONCEPTS, not the labels):
- Wood: Growth, boldness, forward motion - describe as "moving forward", "taking initiative", "expanding your potential"
- Fire: Passion, visibility, expression - describe as "stepping into your power", "being magnetic", "expressing your authentic self"
- Earth: Stability, grounding, centering - describe as "building your foundation", "staying grounded", "cultivating inner strength"
- Metal: Clarity, structure, boundaries - describe as "sharpening your focus", "setting clear boundaries", "making decisive moves"
- Water: Flow, adaptability, intuition - describe as "trusting your instincts", "adapting with wisdom", "flowing through challenges"

Your approach:
1. Diagnose the situation using Five Elements principles (internally)
2. Give ONE clear directive that makes them STRONGER
3. Explain how this action builds their capability or character
4. Keep it under 80 words total

Style rules:
- Say "Do this" NOT "You could try..." - be confident and empowering
- DON'T say "water energy" or "earth energy" - say "you're building strength" or "you're developing clarity"
- Be like a wise coach who believes in their potential
- Every answer should leave them feeling MORE capable, not dependent

Example:
"Wear beige or brown. Right now you're scattered - these grounded tones will help you center your power. Add one gold piece for sharp focus. You're not trying to impress anyone; you're showing up as someone who knows their own strength."
"""
    
    # === V2 新增：八字信息（如果有） ===
    bazi_context = ""
    if bazi_text:
        bazi_context = f"""
=== User's Bazi (Birth Chart) - FOR YOUR REFERENCE ONLY ===
{bazi_text}

IMPORTANT: Use this Bazi information as BACKGROUND CONTEXT to inform your advice, but:
- DO NOT mention specific Bazi terms like "己亥", "甲木", "大运" etc. in your response
- DO NOT say "based on your Bazi" or "your birth chart shows"
- Instead, say things like "based on your natural tendencies" or "given your strengths"
- Weave the insights naturally without revealing the source
===
"""
    
    # === V4 新增：文化上下文（如果有） ===
    cultural_context = get_cultural_context(user_state)
    
    # 话题范围和五行背景
    topic_context = f"""
Topic: {l4_info['l4_name']}
Context: {l4_info['l1_name']} > {l4_info['l2_name']} > {l4_info['l3_name']}

Apply Five Elements wisdom to give guidance. Use the qualities naturally in your language.
"""

    # 对话历史（如果有）
    history_text = ""
    if conversation_history:
        recent_history = conversation_history[-20:]  # 最近10轮
        history_text = "\nPrevious conversation:\n"
        for msg in recent_history:
            role_label = "User" if msg['role'] == 'user' else "You"
            history_text += f"{role_label}: {msg['content']}\n"
    
    # 当前问题
    current_question = f"""
User question: "{user_query}"

Give your direct answer now (under 80 words). Be natural and conversational:"""
    
    # 组合完整 prompt
    full_prompt = system_role + bazi_context + cultural_context + topic_context + history_text + current_question
    
    return full_prompt


def build_general_prompt(user_query, conversation_history, bazi_text=None, user_state=None):
    """构建通用五行 prompt - 当没有匹配到知识库时使用"""
    
    # 系统角色：五行决策顾问（通用版）
    system_role = """You are a Wu Xing (Five Elements) personal growth advisor who empowers users to become their strongest, best selves.

Core Mission:
Every piece of advice you give should help the user GROW STRONGER, make BETTER DECISIONS, and become a MORE CAPABLE person. Frame your guidance as tools for self-improvement and personal mastery.

Five Elements Principles (use the CONCEPTS, not the labels):
- Wood: Growth, boldness, forward motion - describe as "moving forward", "taking initiative", "expanding your potential"
- Fire: Passion, visibility, expression - describe as "stepping into your power", "being magnetic", "expressing your authentic self"
- Earth: Stability, grounding, centering - describe as "building your foundation", "staying grounded", "cultivating inner strength"
- Metal: Clarity, structure, boundaries - describe as "sharpening your focus", "setting clear boundaries", "making decisive moves"
- Water: Flow, adaptability, intuition - describe as "trusting your instincts", "adapting with wisdom", "flowing through challenges"

Your approach:
1. Diagnose the situation using Five Elements principles (internally)
2. Give ONE clear directive that makes them STRONGER
3. Explain how this action builds their capability or character
4. Keep it under 80 words total

Style rules:
- Say "Do this" NOT "You could try..." - be confident and empowering
- DON'T say "water energy" or "earth energy" - say "you're building strength" or "you're developing clarity"
- Be like a wise coach who believes in their potential
- Every answer should leave them feeling MORE capable, not dependent

Example:
"Wear beige or brown. Right now you're scattered - these grounded tones will help you center your power. Add one gold piece for sharp focus. You're not trying to impress anyone; you're showing up as someone who knows their own strength."
"""

    # === V2 新增：八字信息（如果有） ===
    bazi_context = ""
    if bazi_text:
        bazi_context = f"""
=== User's Bazi (Birth Chart) - FOR YOUR REFERENCE ONLY ===
{bazi_text}

IMPORTANT: Use this Bazi information as BACKGROUND CONTEXT to inform your advice, but:
- DO NOT mention specific Bazi terms like "己亥", "甲木", "大运" etc. in your response
- DO NOT say "based on your Bazi" or "your birth chart shows"
- Instead, say things like "based on your natural tendencies" or "given your strengths"
- Weave the insights naturally without revealing the source
===
"""

    # === V4 新增：文化上下文（如果有） ===
    cultural_context = get_cultural_context(user_state)

    # 对话历史（如果有）
    history_text = ""
    if conversation_history:
        recent_history = conversation_history[-20:]  # 最近10轮
        history_text = "\nPrevious conversation:\n"
        for msg in recent_history:
            role_label = "User" if msg['role'] == 'user' else "You"
            history_text += f"{role_label}: {msg['content']}\n"
    
    # 当前问题
    current_question = f"""
User question: "{user_query}"

Give your direct answer now (under 80 words). Be natural and conversational:"""
    
    # 组合完整 prompt
    full_prompt = system_role + bazi_context + cultural_context + history_text + current_question
    
    return full_prompt

def generate_decision_header(user_query, l4_info):
    """
    生成决策头部：信号灯 + 能量类型 + 核心指令
    使用快速 LLM 调用（非流式）
    """
    if LLM_PROVIDER == 'silicon_flow' and not SILICON_FLOW_API_KEY:
        return None
    
    prompt = f"""Based on this question: "{user_query}"
Topic: {l4_info['l4_name']}

Generate a quick decision header in JSON format:
{{
  "signal": "🟢" or "🟡" or "🔴",
  "vibe": "one of: Growth Energy / Passion Energy / Grounding Energy / Clarity Energy / Flow Energy",
  "instruction": "one short imperative sentence (5-8 words)"
}}

Rules:
- 🟢 Green = Go for it, confident move
- 🟡 Yellow = Proceed with caution
- 🔴 Red = Stop, reconsider
- Choose the energy that fits best
- Instruction must be direct and actionable

Respond ONLY with valid JSON, no explanation."""

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.5
    }
    
    try:
        response = requests.post(LLM_API_URL, headers=headers, 
                                data=json.dumps(payload), timeout=30)
        result = response.json()
        content = result['choices'][0]['message']['content'].strip() if 'choices' in result else result.get('message', {}).get('content', '').strip()
        
        # 尝试解析 JSON
        import re
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            return decision
        
        # 如果解析失败，返回默认值
        return {
            "signal": "🟢",
            "vibe": "Clarity Energy",
            "instruction": "Trust your instinct and move forward"
        }
    except Exception as e:
        print(f"[ERROR] 生成决策头部失败: {e}")
        return None

def call_llm_stream(prompt: str):
    """
    Call LLM API with streaming enabled.
    Yields chunks of text as they arrive.
    """
    if LLM_PROVIDER == 'silicon_flow' and not SILICON_FLOW_API_KEY:
        yield "data: Error: API key not configured\n\n"
        return

    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True
    }
    
    # Silicon Flow格式需要max_tokens
    if LLM_PROVIDER == 'silicon_flow':
        payload["max_tokens"] = 2048
        payload["temperature"] = 0.7

    try:
        response = requests.post(
            LLM_API_URL, 
            headers=headers, 
            data=json.dumps(payload), 
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                
                # Silicon Flow格式
                if line_text.startswith('data: '):
                    line_text = line_text[6:]
                    if line_text.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(line_text)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue
                # Ollama格式（直接返回JSON）
                else:
                    try:
                        data = json.loads(line_text)
                        if 'message' in data:
                            content = data['message'].get('content', '')
                            if content:
                                yield f"data: {json.dumps({'content': content})}\n\n"
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


def find_best_l4_match(user_query):
    """Find the best matching L4 intention for the user query with hierarchical search"""
    conn = None
    try:
        print(f"[MATCH] 开始匹配流程，用户问题: '{user_query}'")
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Step 1: Find best matching L1 Domain
        print("[MATCH] 步骤 1/4: 查询所有 L1 领域...")
        cursor.execute("SELECT id, name, description_en FROM knowledge_base WHERE level = 1")
        l1_candidates = cursor.fetchall()
        
        print(f"[MATCH] 找到 {len(l1_candidates)} 个 L1 领域")
        
        if not l1_candidates:
            print("[ERROR] 数据库中没有 L1 数据！")
            return None
        
        # Use LLM to select best L1
        l1_list = "\n".join([f"ID {c[0]}: {c[1]} - {c[2][:100] if c[2] else ''}" for c in l1_candidates])
        l1_prompt = f"""User Query: "{user_query}"

Available Life Domains (L1):
{l1_list}

Task: Select the single most relevant Life Domain ID that best matches the user's question.
Return ONLY the ID number."""
        
        print("[MATCH] 调用 LLM 选择 L1...")
        best_l1_id = call_llm_for_selection(l1_prompt)
        if not best_l1_id:
            print("[ERROR] L1 匹配失败，LLM 未返回有效 ID")
            return None
        
        print(f"[Match] L1 Domain ID: {best_l1_id}")
        
        # Step 2: Find best matching L2 Scenario under the selected L1
        cursor.execute("""
            SELECT id, name, description_en 
            FROM knowledge_base 
            WHERE level = 2 AND parent_id = %s
        """, (best_l1_id,))
        l2_candidates = cursor.fetchall()
        
        if not l2_candidates:
            return None
        
        l2_list = "\n".join([f"ID {c[0]}: {c[1]} - {c[2][:100] if c[2] else ''}" for c in l2_candidates])
        l2_prompt = f"""User Query: "{user_query}"

Available Scenarios (L2):
{l2_list}

Task: Select the single most relevant Scenario ID that best matches the user's specific situation.
Return ONLY the ID number."""
        
        best_l2_id = call_llm_for_selection(l2_prompt)
        if not best_l2_id:
            return None
        
        print(f"[Match] L2 Scenario ID: {best_l2_id}")
        
        # Step 3: Find best matching L3 Sub-scenario under the selected L2
        cursor.execute("""
            SELECT id, name, description_en 
            FROM knowledge_base 
            WHERE level = 3 AND parent_id = %s
        """, (best_l2_id,))
        l3_candidates = cursor.fetchall()
        
        if not l3_candidates:
            return None
        
        l3_list = "\n".join([f"ID {c[0]}: {c[1]} - {c[2][:80] if c[2] else ''}" for c in l3_candidates])
        l3_prompt = f"""User Query: "{user_query}"

Available Sub-scenarios (L3):
{l3_list}

Task: Select the single most relevant Sub-scenario ID.
Return ONLY the ID number."""
        
        best_l3_id = call_llm_for_selection(l3_prompt)
        if not best_l3_id:
            return None
        
        print(f"[Match] L3 Sub-scenario ID: {best_l3_id}")
        
        # Step 4: Find best matching L4 Intention under the selected L3
        cursor.execute("""
            SELECT kb.id, kb.name, kb.description_en 
            FROM knowledge_base kb
            JOIN l4_content c ON kb.id = c.l4_id
            WHERE kb.level = 4 AND kb.parent_id = %s
        """, (best_l3_id,))
        l4_candidates = cursor.fetchall()
        
        if not l4_candidates:
            # Fallback: try to find any L4 with content under this L3
            cursor.execute("""
                SELECT kb.id, kb.name, kb.description_en 
                FROM knowledge_base kb
                WHERE kb.level = 4 AND kb.parent_id = %s
                LIMIT 1
            """, (best_l3_id,))
            fallback = cursor.fetchone()
            if fallback:
                print(f"[Match] L4 Intention ID (fallback): {fallback[0]}")
                return fallback[0]
            return None
        
        l4_list = "\n".join([f"ID {c[0]}: {c[1]}" for c in l4_candidates])
        l4_prompt = f"""User Query: "{user_query}"

Available User Intentions (L4):
{l4_list}

Task: Select the single most relevant Intention ID that exactly matches what the user wants to know.
Return ONLY the ID number."""
        
        best_l4_id = call_llm_for_selection(l4_prompt)
        print(f"[Match] L4 Intention ID: {best_l4_id}")
        
        return best_l4_id
        
    except Exception as e:
        print(f"Error in find_best_l4_match: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def call_llm_for_selection(prompt):
    """Helper function to call LLM and extract ID from response"""
    if LLM_PROVIDER == 'silicon_flow' and not SILICON_FLOW_API_KEY:
        print("[ERROR] API Key 未配置！")
        return None
    
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    
    if LLM_PROVIDER == 'silicon_flow':
        payload["max_tokens"] = 50
        payload["temperature"] = 0.3
    
    try:
        print(f"[LLM] 调用模型: {LLM_MODEL} (Provider: {LLM_PROVIDER})")
        print(f"[LLM] Prompt 长度: {len(prompt)} 字符")
        
        response = requests.post(LLM_API_URL, headers=headers, 
                                data=json.dumps(payload), timeout=60)
        
        print(f"[LLM] 响应状态码: {response.status_code}")
        
        result = response.json()
        
        if response.status_code != 200:
            print(f"[ERROR] API 返回错误: {result}")
            return None
        
        # 兼容不同格式的响应
        if 'choices' in result:
            content = result['choices'][0]['message']['content'].strip()
        elif 'message' in result:
            content = result['message']['content'].strip()
        else:
            print(f"[ERROR] 无法解析响应格式: {result}")
            return None
        
        print(f"[LLM] 返回内容: '{content}'")
        
        import re
        match = re.search(r'\d+', content)
        if match:
            selected_id = int(match.group())
            print(f"[LLM] 提取的 ID: {selected_id}")
            return selected_id
        else:
            print(f"[ERROR] 无法从返回内容中提取数字 ID")
            return None
            
    except Exception as e:
        print(f"[ERROR] LLM 调用异常: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def get_l4_info(l4_id):
    """Retrieve basic info for a specific L4 ID from knowledge_base"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT l4.name, l3.name, l2.name, l1.name
            FROM knowledge_base l4
            JOIN knowledge_base l3 ON l4.parent_id = l3.id
            JOIN knowledge_base l2 ON l3.parent_id = l2.id
            JOIN knowledge_base l1 ON l2.parent_id = l1.id
            WHERE l4.id = %s AND l4.level = 4
        """, (l4_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'l4_name': result[0],
                'l3_name': result[1],
                'l2_name': result[2],
                'l1_name': result[3]
            }
        return None
        
    except Exception as e:
        print(f"Error in get_l4_info: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def generate_stream_response(user_query, session_id='default', bazi_data=None, user_state=None):
    """Generate streaming response with L4 knowledge boundary and conversation context"""
    
    import sys
    print(f"\n{'='*60}", flush=True)
    print(f"[STREAM] 开始生成流式响应", flush=True)
    print(f"[STREAM] Session ID: '{session_id}'", flush=True)
    print(f"[STREAM] 用户问题: '{user_query}'", flush=True)
    print(f"[STREAM] 八字数据: {bazi_data}", flush=True)
    print(f"[STREAM] 用户所在州: {user_state if user_state else '未指定'}", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()
    
    # 获取会话
    session = get_or_create_session(session_id)
    
    # === V2 新增：调用 MCP 获取排盘结果（优化：会话中已有则复用，不重复调用） ===
    bazi_result = None
    bazi_text = session.get('bazi_text')  # 先尝试从会话中获取
    
    # 只有当会话中没有八字信息，且前端传了新的八字数据时，才调用MCP
    if not bazi_text and bazi_data:
        from .bazi_mcp_client import call_bazi_mcp, format_bazi_for_llm
        
        yield f"data: {json.dumps({'status': 'Getting Bazi chart...'})}\n\n"
        
        print("[MCP] 会话中无八字信息，开始调用 bazi-mcp 工具...", flush=True)
        sys.stdout.flush()
        
        bazi_result = call_bazi_mcp(
            solar_datetime=bazi_data.get('solar_datetime'),
            gender=bazi_data.get('gender', 1)
        )
        
        if bazi_result:
            print("[MCP] ✅ 成功获取八字排盘结果，已保存到会话", flush=True)
            sys.stdout.flush()
            bazi_text = format_bazi_for_llm(bazi_result)
            # 保存到会话中，后续对话可以复用
            session['bazi_result'] = bazi_result
            session['bazi_text'] = bazi_text
        else:
            print("[MCP] ❌ 获取八字排盘失败", flush=True)
            sys.stdout.flush()
    elif bazi_text:
        print("[MCP] ✅ 复用会话中已保存的八字信息，跳过MCP调用", flush=True)
        sys.stdout.flush()
    
    # Send initial status
    yield f"data: {json.dumps({'status': 'Analyzing your question...'})}\n\n"
    
    # 每轮对话都重新匹配 L4，确保精准响应
    print("[STREAM] 调用 find_best_l4_match...", flush=True)
    sys.stdout.flush()
    
    l4_id = find_best_l4_match(user_query)
    
    print(f"[STREAM] 返回的 L4 ID: {l4_id}", flush=True)
    sys.stdout.flush()
    
    # 添加用户消息到历史
    add_to_history(session_id, 'user', user_query)
    
    # === 兜底逻辑：如果没有匹配到 L4，直接用通用 prompt ===
    if not l4_id:
        print("[STREAM] L4 匹配失败，使用通用模式回答", flush=True)
        sys.stdout.flush()
        
        # 发送状态提示
        yield f"data: {json.dumps({'status': 'Answering your question...'})}\n\n"
        
        # 构建通用 prompt（不依赖知识库）
        prompt = build_general_prompt(user_query, session['history'][:-1], bazi_text, user_state)
        
        print(f"[STREAM] 使用通用 Prompt，长度: {len(prompt)} 字符", flush=True)
        if bazi_text:
            print(f"[STREAM] 已整合八字信息到 Prompt", flush=True)
        
        # 调用 LLM 流式生成
        assistant_response = ""
        for chunk in call_llm_stream(prompt):
            if chunk.startswith("data:"):
                yield chunk
                try:
                    data = json.loads(chunk[6:])
                    if 'content' in data:
                        assistant_response += data['content']
                except:
                    pass
        
        # 添加助手回复到历史
        if assistant_response:
            add_to_history(session_id, 'assistant', assistant_response)
        
        # 发送完成信号
        yield "data: [DONE]\n\n"
        print("[STREAM] 流式响应完成（通用模式）", flush=True)
        sys.stdout.flush()
        return
    
    # === 正常流程：匹配到了 L4 ===
    # Get L4 basic info as semantic boundary
    l4_info = get_l4_info(l4_id)
    
    if not l4_info:
        print("[STREAM] L4信息获取失败，使用通用模式回答", flush=True)
        sys.stdout.flush()
        
        # 发送状态提示
        yield f"data: {json.dumps({'status': 'Answering your question...'})}\n\n"
        
        # 构建通用 prompt
        prompt = build_general_prompt(user_query, session['history'][:-1], bazi_text, user_state)
        
        print(f"[STREAM] 使用通用 Prompt，长度: {len(prompt)} 字符", flush=True)
        if bazi_text:
            print(f"[STREAM] 已整合八字信息到 Prompt", flush=True)
        
        # 调用 LLM 流式生成
        assistant_response = ""
        for chunk in call_llm_stream(prompt):
            if chunk.startswith("data:"):
                yield chunk
                try:
                    data = json.loads(chunk[6:])
                    if 'content' in data:
                        assistant_response += data['content']
                except:
                    pass
        
        # 添加助手回复到历史
        if assistant_response:
            add_to_history(session_id, 'assistant', assistant_response)
        
        # 发送完成信号
        yield "data: [DONE]\n\n"
        print("[STREAM] 流式响应完成（通用模式 - L4信息缺失）", flush=True)
        sys.stdout.flush()
        return
    
    # 更新会话中的 L4 信息
    session['l4_id'] = l4_id
    session['l4_info'] = l4_info
    
    # Send matched topic
    topic_name = l4_info['l4_name']
    matched_msg = {'status': f'Topic: {topic_name}', 'section': 'header'}
    yield f"data: {json.dumps(matched_msg)}\n\n"
    
    # 构建 prompt（简洁版）
    prompt = build_contextualized_prompt(user_query, l4_info, session['history'][:-1], bazi_text, user_state)  # 历史不包含当前问题
    
    print(f"[STREAM] 构建知识库增强 Prompt，长度: {len(prompt)} 字符", flush=True)
    if bazi_text:
        print(f"[STREAM] 已整合八字信息到 Prompt", flush=True)
    
    # 调用 LLM 流式生成
    assistant_response = ""
    for chunk in call_llm_stream(prompt):
        if chunk.startswith("data:"):
            yield chunk
            # 提取内容累积（用于保存到历史）
            try:
                data = json.loads(chunk[6:])
                if 'content' in data:
                    assistant_response += data['content']
            except:
                pass
    
    # 添加助手回复到历史
    if assistant_response:
        add_to_history(session_id, 'assistant', assistant_response)
    
    # Send completion
    yield "data: [DONE]\n\n"
    print(f"[STREAM] 流式响应完成", flush=True)
    sys.stdout.flush()


def ask_advisor(request):
    """Handle streaming responses for user questions"""
    if request.method == 'POST':
        user_query = request.POST.get('query', '').strip()
        # 从请求中获取或生成 session_id
        session_id = request.POST.get('session_id', '').strip()
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            print(f"[SESSION] 生成新会话ID: {session_id}")
        else:
            print(f"[SESSION] 使用现有会话ID: {session_id}")
        
        # === V2 新增：获取八字数据 ===
        bazi_data_str = request.POST.get('bazi_data', '').strip()
        bazi_data = None
        if bazi_data_str:
            try:
                bazi_data = json.loads(bazi_data_str)
                print(f"[BAZI] 收到命理数据: {bazi_data}")
            except json.JSONDecodeError:
                print(f"[BAZI] 解析命理数据失败: {bazi_data_str}")
        
        # === V4 新增：获取用户所在州（文化适配） ===
        user_state = request.POST.get('user_state', '').strip()
        if user_state:
            print(f"[CULTURAL] 用户所在州: {user_state}")
        
        # 添加调试日志
        print(f"\n{'='*60}")
        print(f"[REQUEST] 收到用户问题: '{user_query}'")
        print(f"[REQUEST] 会话ID: {session_id}")
        print(f"[REQUEST] 八字数据: {'有' if bazi_data else '无'}")
        print(f"[REQUEST] 用户所在州: {user_state if user_state else '未指定'}")
        print(f"[REQUEST] API Key存在: {bool(SILICON_FLOW_API_KEY)}")
        print(f"[REQUEST] 使用模型: {LLM_MODEL}")
        print(f"{'='*60}\n")
        
        if not user_query:
            print("[ERROR] 用户问题为空")
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'error': 'Please enter a question'})}\n\n"]),
                content_type='text/event-stream'
            )
        
        response = StreamingHttpResponse(
            generate_stream_response(user_query, session_id, bazi_data, user_state),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Session-ID'] = session_id  # 通过响应头返回 session_id
        response['X-Accel-Buffering'] = 'no'
        return response
    
    return render(request, 'advisor/index.html')

