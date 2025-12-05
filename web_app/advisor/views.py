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
SILICON_FLOW_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'
SILICON_FLOW_API_KEY = os.getenv('SILICON_FLOW_API_KEY')

# 去掉环境变量中可能的引号
if SILICON_FLOW_API_KEY:
    SILICON_FLOW_API_KEY = SILICON_FLOW_API_KEY.strip('"').strip("'")

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

# 使用快速模型进行简单的 ID 选择任务
LLM_MODEL = "Qwen/Qwen3-32B"  # 修正模型名称
# 常见的可用模型：
# - "Qwen/Qwen2.5-7B-Instruct"
# - "deepseek-ai/DeepSeek-V2.5"
# - "01-ai/Yi-1.5-9B-Chat"

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


# 场景人格映射表
PERSONA_MAPPING = {
    # 情感与人际关系
    'dating': 'a bold Fashion Editor meets Energy Healer',
    'relationship': 'a straight-talking Relationship Coach with cosmic insights',
    'breakup': 'a compassionate yet brutally honest Therapist',
    'friendship': 'a wise Life Coach who keeps it real',
    
    # 职场与事业
    'workplace': 'a sharp Corporate Strategist with Zen wisdom',
    'career': 'a visionary Career Mentor who sees the bigger picture',
    'conflict': 'a tough-love Mediator with clarity',
    'leadership': 'a confident Executive Coach',
    
    # 个人成长
    'decision': 'a decisive Life Strategist',
    'habit': 'a no-nonsense Performance Coach',
    'confidence': 'a fierce Empowerment Coach',
    
    # 默认
    'default': 'a bold, intuitive Energy Strategist'
}

# 五行能量映射（北美化表达）
ENERGY_ELEMENTS = {
    'wood': 'Growth Energy - bold, expansive, forward-moving',
    'fire': 'Passion Energy - magnetic, expressive, confident',
    'earth': 'Grounding Energy - stable, centering, reliable',
    'metal': 'Clarity Energy - sharp, decisive, structured',
    'water': 'Flow Energy - adaptive, intuitive, resilient'
}

def get_persona_for_l4(l4_name):
    """根据 L4 场景动态选择 AI 人格"""
    l4_lower = l4_name.lower()
    
    # 匹配关键词
    for keyword, persona in PERSONA_MAPPING.items():
        if keyword in l4_lower:
            return persona
    
    return PERSONA_MAPPING['default']

def build_contextualized_prompt(user_query, l4_info, conversation_history):
    """构建包含 L4 语义边界和对话历史的 prompt"""
    
    # 动态选择人格
    persona = get_persona_for_l4(l4_info['l4_name'])
    
    # 系统角色定义 - V2 犀利版
    system_role = f"""You are {persona}.

Your Style:
- Be DIRECT and CONFIDENT. No "you could try" or "it might be good to" - say "Do this" or "Don't do that".
- Give ONE clear instruction, not 10 vague suggestions.
- Be the friend who tells the truth, not the one who says "both options are fine".
- Use natural, conversational English with personality.

Output Structure (MANDATORY):
1. **The Move:** (1-2 sentences, imperative mood) - What to do RIGHT NOW
2. **Why It Works:** (2-3 sentences max) - The energy/logic behind it
3. **Your Mantra:** (1 power phrase) - A quote to own this decision

Example:
**The Move:** Wear the beige trench coat with gold accessories.
**Why It Works:** You're carrying too much emotional water today—beige grounds that energy like earth absorbing a flood. Gold adds a boundary, a signal that says "I'm here, but I'm not scattered."
**Your Mantra:** "I am not asking for space. I am claiming it."

Rules:
- Stay within the topic scope
- Keep total response under 100 words
- Reference energy qualities naturally (Growth, Passion, Grounding, Clarity, Flow) - never say "Wood/Fire/Earth/Metal/Water"
- Be bold but not rude. Think: confident best friend."""
    
    # 知识边界（L4 主题作为语义边界）
    knowledge_boundary = f"""

📍 Topic Focus: {l4_info['l4_name']}
   (Context: {l4_info['l1_name']} → {l4_info['l2_name']} → {l4_info['l3_name']})

⚡ Energy Toolbox (use naturally, don't explain):
   • Growth Energy - bold, expansive, forward-moving
   • Passion Energy - magnetic, expressive, confident  
   • Grounding Energy - stable, centering, reliable
   • Clarity Energy - sharp, decisive, structured
   • Flow Energy - adaptive, intuitive, resilient
"""

    # 对话历史（最近10轮）
    history_text = ""
    if conversation_history:
        recent_history = conversation_history[-20:]  # 最近10轮（每轮2条消息）
        history_text = "\n\nConversation Context:\n"
        for msg in recent_history:
            role_label = "User" if msg['role'] == 'user' else "You"
            history_text += f"{role_label}: {msg['content']}\n"
    
    # 当前问题
    current_question = f"""\n\n💬 User Question: "{user_query}"

🎯 Now respond following the 3-part structure:
   **The Move:** [Direct instruction]
   **Why It Works:** [Brief energy/logic explanation]
   **Your Mantra:** [Power quote]

Keep it under 100 words total. Be direct, be confident, be actionable."""
    
    # 组合完整 prompt
    full_prompt = system_role + knowledge_boundary + history_text + current_question
    
    return full_prompt

def generate_decision_header(user_query, l4_info):
    """
    生成决策头部：信号灯 + 能量类型 + 核心指令
    使用快速 LLM 调用（非流式）
    """
    if not SILICON_FLOW_API_KEY:
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

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.5
    }
    
    try:
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, 
                                data=json.dumps(payload), timeout=30)
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
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
    if not SILICON_FLOW_API_KEY:
        yield "data: Error: API key not configured\n\n"
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.7,
        "stream": True  # Enable streaming
    }

    try:
        response = requests.post(
            SILICON_FLOW_API_URL, 
            headers=headers, 
            data=json.dumps(payload), 
            stream=True,
            timeout=120
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    line_text = line_text[6:]  # Remove 'data: ' prefix
                    
                    if line_text.strip() == '[DONE]':
                        break
                        
                    try:
                        data = json.loads(line_text)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                # Send as SSE format
                                yield f"data: {json.dumps({'content': content})}\n\n"
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
    if not SILICON_FLOW_API_KEY:
        print("[ERROR] API Key 未配置！")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50,
        "temperature": 0.3
    }
    
    try:
        print(f"[LLM] 调用模型: {LLM_MODEL}")
        print(f"[LLM] Prompt 长度: {len(prompt)} 字符")
        
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, 
                                data=json.dumps(payload), timeout=60)
        
        print(f"[LLM] 响应状态码: {response.status_code}")
        
        result = response.json()
        
        # 如果是错误响应，打印详细错误信息
        if response.status_code != 200:
            print(f"[ERROR] API 返回错误: {result}")
            return None
        
        content = result['choices'][0]['message']['content'].strip()
        
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


def generate_stream_response(user_query, session_id='default'):
    """Generate streaming response with L4 knowledge boundary and conversation context"""
    
    import sys
    print(f"\n{'='*60}", flush=True)
    print(f"[STREAM] 开始生成流式响应", flush=True)
    print(f"[STREAM] Session ID: '{session_id}'", flush=True)
    print(f"[STREAM] 用户问题: '{user_query}'", flush=True)
    print(f"{'='*60}\n", flush=True)
    sys.stdout.flush()
    
    # 获取会话
    session = get_or_create_session(session_id)
    
    # Send initial status
    yield f"data: {json.dumps({'status': 'Analyzing your question...'})}\n\n"
    
    # 每轮对话都重新匹配 L4，确保精准响应
    print("[STREAM] 调用 find_best_l4_match...", flush=True)
    sys.stdout.flush()
    
    l4_id = find_best_l4_match(user_query)
    
    print(f"[STREAM] 返回的 L4 ID: {l4_id}", flush=True)
    sys.stdout.flush()
    
    if not l4_id:
        print("[STREAM] L4 ID 为 None，返回错误", flush=True)
        sys.stdout.flush()
        yield f"data: {json.dumps({'error': 'Could not find a relevant topic in our knowledge base.'})}\n\n"
        yield "data: [DONE]\n\n"
        print("[STREAM] 流式响应完成（错误退出）", flush=True)
        return
    
    # Get L4 basic info as semantic boundary
    l4_info = get_l4_info(l4_id)
    
    if not l4_info:
        yield f"data: {json.dumps({'error': 'Topic not found in knowledge base.'})}\n\n"
        yield "data: [DONE]\n\n"
        print("[STREAM] 流式响应完成（L4信息未找到）", flush=True)
        return
    
    # 更新会话中的 L4 信息
    session['l4_id'] = l4_id
    session['l4_info'] = l4_info
    
    # 添加用户消息到历史
    add_to_history(session_id, 'user', user_query)
    
    # Send matched topic
    topic_name = l4_info['l4_name']
    matched_msg = {'status': f'Topic: {topic_name}', 'section': 'header'}
    yield f"data: {json.dumps(matched_msg)}\n\n"
    
    # === V2 新增：生成决策头部（红绿灯系统） ===
    print("[STREAM] 生成决策头部...", flush=True)
    decision_header = generate_decision_header(user_query, l4_info)
    if decision_header:
        yield f"data: {json.dumps({'decision_header': decision_header})}\n\n"
        print(f"[STREAM] 决策头部: {decision_header}", flush=True)
    
    # 构建 prompt（包含 L4 语义边界 + 对话历史）
    prompt = build_contextualized_prompt(user_query, l4_info, session['history'][:-1])  # 历史不包含当前问题
    
    print(f"[STREAM] 构建的 Prompt 长度: {len(prompt)} 字符", flush=True)
    
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
        
        # 添加调试日志
        print(f"\n{'='*60}")
        print(f"[REQUEST] 收到用户问题: '{user_query}'")
        print(f"[REQUEST] 会话ID: {session_id}")
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
            generate_stream_response(user_query, session_id),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Session-ID'] = session_id  # 通过响应头返回 session_id
        response['X-Accel-Buffering'] = 'no'
        return response
    
    return render(request, 'advisor/index.html')

