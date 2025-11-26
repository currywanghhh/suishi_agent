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
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}
LLM_MODEL = "deepseek-ai/DeepSeek-R1"


def index(request):
    """Render the main advisor interface"""
    return render(request, 'advisor/index.html')


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
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Step 1: Find best matching L1 Domain
        cursor.execute("SELECT id, name, description_en FROM knowledge_base WHERE level = 1")
        l1_candidates = cursor.fetchall()
        
        if not l1_candidates:
            return None
        
        # Use LLM to select best L1
        l1_list = "\n".join([f"ID {c[0]}: {c[1]} - {c[2][:100] if c[2] else ''}" for c in l1_candidates])
        l1_prompt = f"""User Query: "{user_query}"

Available Life Domains (L1):
{l1_list}

Task: Select the single most relevant Life Domain ID that best matches the user's question.
Return ONLY the ID number."""
        
        best_l1_id = call_llm_for_selection(l1_prompt)
        if not best_l1_id:
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
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, 
                                data=json.dumps(payload), timeout=60)
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        import re
        match = re.search(r'\d+', content)
        if match:
            return int(match.group())
    except Exception as e:
        print(f"Error in call_llm_for_selection: {e}")
    
    return None


def get_l4_content(l4_id):
    """Retrieve content for a specific L4 ID"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT kb.name, c.five_elements_insight, c.action_guide, 
                   c.communication_scripts, c.energy_harmonization
            FROM l4_content c
            JOIN knowledge_base kb ON c.l4_id = kb.id
            WHERE c.l4_id = %s
        """, (l4_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'intention_name': result[0],
                'five_elements_insight': result[1],
                'action_guide': result[2],
                'communication_scripts': result[3],
                'energy_harmonization': result[4]
            }
        return None
        
    except Exception as e:
        print(f"Error in get_l4_content: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def generate_stream_response(user_query):
    """Generate streaming response for user query"""
    
    # Send initial status
    yield f"data: {json.dumps({'status': 'Analyzing your question...'})}\n\n"
    time.sleep(0.5)
    
    # Find matching L4
    l4_id = find_best_l4_match(user_query)
    
    if not l4_id:
        yield f"data: {json.dumps({'error': 'Could not find a relevant topic in our knowledge base.'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # Get content
    content = get_l4_content(l4_id)
    
    if not content:
        yield f"data: {json.dumps({'error': 'Content not available for this topic.'})}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # Send matched intention
    intention_name = content['intention_name']
    matched_msg = {'status': f'Matched: {intention_name}', 'section': 'header'}
    yield f"data: {json.dumps(matched_msg)}\n\n"
    time.sleep(0.3)
    
    # Stream Five Elements Insight
    insight_title = {'section': 'insight_title', 'content': '\n🔮 Five Elements Insight\n'}
    yield f"data: {json.dumps(insight_title)}\n\n"
    time.sleep(0.2)
    
    insight_text = content['five_elements_insight']
    for i in range(0, len(insight_text), 3):
        chunk = insight_text[i:i+3]
        yield f"data: {json.dumps({'section': 'insight', 'content': chunk})}\n\n"
        time.sleep(0.01)
    
    # Stream Action Guide
    action_title = {'section': 'action_title', 'content': '\n\n✅ Action Guide\n'}
    yield f"data: {json.dumps(action_title)}\n\n"
    time.sleep(0.2)
    
    action_text = content['action_guide']
    for i in range(0, len(action_text), 3):
        chunk = action_text[i:i+3]
        yield f"data: {json.dumps({'section': 'action', 'content': chunk})}\n\n"
        time.sleep(0.01)
    
    # Stream Communication Scripts
    scripts_title = {'section': 'scripts_title', 'content': '\n\n💬 Communication Scripts\n'}
    yield f"data: {json.dumps(scripts_title)}\n\n"
    time.sleep(0.2)
    
    scripts_text = content['communication_scripts']
    for i in range(0, len(scripts_text), 3):
        chunk = scripts_text[i:i+3]
        yield f"data: {json.dumps({'section': 'scripts', 'content': chunk})}\n\n"
        time.sleep(0.01)
    
    # Stream Energy Harmonization
    energy_title = {'section': 'energy_title', 'content': '\n\n🌟 Energy Harmonization\n'}
    yield f"data: {json.dumps(energy_title)}\n\n"
    time.sleep(0.2)
    
    energy_text = content['energy_harmonization']
    for i in range(0, len(energy_text), 3):
        chunk = energy_text[i:i+3]
        yield f"data: {json.dumps({'section': 'energy', 'content': chunk})}\n\n"
        time.sleep(0.01)
    
    # Send completion
    yield "data: [DONE]\n\n"


def ask_advisor(request):
    """Handle streaming responses for user questions"""
    if request.method == 'POST':
        user_query = request.POST.get('query', '').strip()
        
        if not user_query:
            return StreamingHttpResponse(
                iter([f"data: {json.dumps({'error': 'Please enter a question'})}\n\n"]),
                content_type='text/event-stream'
            )
        
        response = StreamingHttpResponse(
            generate_stream_response(user_query),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
    
    return render(request, 'advisor/index.html')

