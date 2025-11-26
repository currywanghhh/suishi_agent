"""
Wu Xing Advisor - V2 多轮对话版本
优化策略：通过多轮引导式对话减少响应时间
"""
import os
import json
import time
import mysql.connector
import requests
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
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

# 会话存储（生产环境应使用Redis或数据库）
SESSIONS = {}


def index_v2(request):
    """V2版本的主界面"""
    return render(request, 'advisor/index_v2.html')


def call_llm_fast(prompt: str, max_tokens=100, temperature=0.3):
    """
    快速LLM调用，用于分类和选择任务
    不使用流式传输，直接返回结果
    """
    if not SILICON_FLOW_API_KEY:
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }

    try:
        response = requests.post(
            SILICON_FLOW_API_URL, 
            headers=headers, 
            data=json.dumps(payload), 
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error in call_llm_fast: {e}")
        return None


def get_all_l1_domains():
    """获取所有L1领域"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description_en 
            FROM knowledge_base 
            WHERE level = 1 
            ORDER BY id
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_all_l1_domains: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_l2_scenarios(l1_id):
    """获取指定L1下的所有L2场景"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description_en 
            FROM knowledge_base 
            WHERE level = 2 AND parent_id = %s
            ORDER BY id
        """, (l1_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_l2_scenarios: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_l3_subscenarios(l2_id):
    """获取指定L2下的所有L3子场景"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description_en 
            FROM knowledge_base 
            WHERE level = 3 AND parent_id = %s
            ORDER BY id
        """, (l2_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_l3_subscenarios: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_l4_intentions(l3_id):
    """获取指定L3下的所有L4意图"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT kb.id, kb.name, kb.description_en 
            FROM knowledge_base kb
            WHERE kb.level = 4 AND kb.parent_id = %s
            ORDER BY kb.id
        """, (l3_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error in get_l4_intentions: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_l4_full_content(l4_id):
    """获取L4的完整内容"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT kb.name, kb.description_en, 
                   c.five_elements_insight, c.action_guide, 
                   c.communication_scripts, c.energy_harmonization
            FROM knowledge_base kb
            LEFT JOIN l4_content c ON kb.id = c.l4_id
            WHERE kb.id = %s
        """, (l4_id,))
        result = cursor.fetchone()
        if result:
            return {
                'name': result[0],
                'description': result[1],
                'five_elements_insight': result[2],
                'action_guide': result[3],
                'communication_scripts': result[4],
                'energy_harmonization': result[5]
            }
        return None
    except Exception as e:
        print(f"Error in get_l4_full_content: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@require_http_methods(["POST"])
def start_conversation(request):
    """
    开始新对话 - Step 1: 分析用户问题并返回L1/L2选项
    策略：只做一次LLM调用快速分类到L1，然后返回该L1下的所有L2选项
    """
    try:
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        # 生成会话ID
        session_id = f"session_{int(time.time() * 1000)}"
        
        # 获取所有L1领域
        l1_domains = get_all_l1_domains()
        if not l1_domains:
            return JsonResponse({'error': 'No domains found in knowledge base'}, status=500)
        
        # 使用LLM快速分类到L1
        l1_list = "\n".join([f"{d[0]}. {d[1]}: {d[2][:80] if d[2] else ''}" for d in l1_domains])
        
        classification_prompt = f"""User Question: "{user_query}"

Available Life Domains:
{l1_list}

Task: Identify the SINGLE most relevant domain ID that best matches this question.
Think step by step, then output ONLY the domain ID number.

Output format: Just the number (e.g., "3")"""

        llm_response = call_llm_fast(classification_prompt, max_tokens=50, temperature=0.2)
        
        # 提取L1 ID
        import re
        match = re.search(r'\d+', llm_response or '')
        if not match:
            # 如果分类失败，返回所有L1供用户选择
            return JsonResponse({
                'session_id': session_id,
                'step': 'select_domain',
                'message': 'Please select the life area related to your question:',
                'options': [{'id': d[0], 'name': d[1], 'description': d[2][:100] if d[2] else ''} 
                           for d in l1_domains[:6]],  # 只显示前6个
                'user_query': user_query
            })
        
        best_l1_id = int(match.group())
        
        # 获取该L1下的所有L2场景
        l2_scenarios = get_l2_scenarios(best_l1_id)
        
        if not l2_scenarios:
            return JsonResponse({
                'error': f'No scenarios found for domain ID {best_l1_id}'
            }, status=404)
        
        # 找到对应的L1名称
        l1_name = next((d[1] for d in l1_domains if d[0] == best_l1_id), "Unknown")
        
        # 保存会话状态
        SESSIONS[session_id] = {
            'user_query': user_query,
            'l1_id': best_l1_id,
            'l1_name': l1_name,
            'step': 'l2_selection',
            'created_at': time.time()
        }
        
        return JsonResponse({
            'session_id': session_id,
            'step': 'select_scenario',
            'domain': l1_name,
            'message': f'Great! This seems related to **{l1_name}**. Which specific situation fits best?',
            'options': [{'id': s[0], 'name': s[1], 'description': s[2][:80] if s[2] else ''} 
                       for s in l2_scenarios],
            'user_query': user_query
        })
        
    except Exception as e:
        print(f"Error in start_conversation: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def continue_conversation(request):
    """
    继续对话 - Step 2/3: 用户选择后继续引导
    """
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        selected_id = data.get('selected_id')
        step = data.get('step')  # 'l2_selected', 'l3_selected', 'l4_selected'
        
        if not session_id or session_id not in SESSIONS:
            return JsonResponse({'error': 'Invalid session'}, status=400)
        
        session = SESSIONS[session_id]
        
        # L2被选择 -> 返回L3选项
        if step == 'l2_selected':
            l3_subscenarios = get_l3_subscenarios(selected_id)
            
            if not l3_subscenarios:
                return JsonResponse({
                    'error': 'No sub-scenarios found'
                }, status=404)
            
            # 更新会话
            session['l2_id'] = selected_id
            session['step'] = 'l3_selection'
            
            return JsonResponse({
                'session_id': session_id,
                'step': 'select_subscenario',
                'message': 'Perfect! Let\'s narrow it down. Which specific aspect?',
                'options': [{'id': s[0], 'name': s[1], 'description': s[2][:80] if s[2] else ''} 
                           for s in l3_subscenarios]
            })
        
        # L3被选择 -> 返回L4选项
        elif step == 'l3_selected':
            l4_intentions = get_l4_intentions(selected_id)
            
            if not l4_intentions:
                return JsonResponse({
                    'error': 'No intentions found'
                }, status=404)
            
            # 更新会话
            session['l3_id'] = selected_id
            session['step'] = 'l4_selection'
            
            return JsonResponse({
                'session_id': session_id,
                'step': 'select_intention',
                'message': 'Almost there! What exactly would you like guidance on?',
                'options': [{'id': i[0], 'name': i[1], 'description': i[2][:100] if i[2] else ''} 
                           for i in l4_intentions]
            })
        
        # L4被选择 -> 返回完整内容
        elif step == 'l4_selected':
            content = get_l4_full_content(selected_id)
            
            if not content:
                return JsonResponse({
                    'error': 'Content not found'
                }, status=404)
            
            # 更新会话
            session['l4_id'] = selected_id
            session['step'] = 'completed'
            
            return JsonResponse({
                'session_id': session_id,
                'step': 'final_answer',
                'intention': content['name'],
                'content': {
                    'five_elements_insight': content['five_elements_insight'],
                    'action_guide': content['action_guide'],
                    'communication_scripts': content['communication_scripts'],
                    'energy_harmonization': content['energy_harmonization']
                }
            })
        
        else:
            return JsonResponse({'error': 'Invalid step'}, status=400)
            
    except Exception as e:
        print(f"Error in continue_conversation: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def quick_answer(request):
    """
    快速回答模式 - 直接匹配最佳L4并返回内容（保留V1的快速模式）
    适合用户不想多轮交互时使用
    """
    try:
        data = json.loads(request.body)
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        # 获取所有L1
        l1_domains = get_all_l1_domains()
        if not l1_domains:
            return JsonResponse({'error': 'No domains found'}, status=500)
        
        # 快速匹配L1
        l1_list = "\n".join([f"{d[0]}. {d[1]}" for d in l1_domains])
        l1_prompt = f'Question: "{user_query}"\nDomains:\n{l1_list}\n\nSelect domain ID:'
        llm_result = call_llm_fast(l1_prompt, max_tokens=20)
        
        import re
        match = re.search(r'\d+', llm_result or '')
        if not match:
            return JsonResponse({'error': 'Classification failed'}, status=500)
        
        l1_id = int(match.group())
        
        # 快速匹配L2
        l2_scenarios = get_l2_scenarios(l1_id)
        if not l2_scenarios:
            return JsonResponse({'error': 'No scenarios found'}, status=404)
        
        l2_list = "\n".join([f"{s[0]}. {s[1]}" for s in l2_scenarios])
        l2_prompt = f'Question: "{user_query}"\nScenarios:\n{l2_list}\n\nSelect scenario ID:'
        llm_result = call_llm_fast(l2_prompt, max_tokens=20)
        
        match = re.search(r'\d+', llm_result or '')
        if not match:
            return JsonResponse({'error': 'Scenario selection failed'}, status=500)
        
        l2_id = int(match.group())
        
        # 快速匹配L3
        l3_subscenarios = get_l3_subscenarios(l2_id)
        if not l3_subscenarios:
            return JsonResponse({'error': 'No sub-scenarios found'}, status=404)
        
        l3_list = "\n".join([f"{s[0]}. {s[1]}" for s in l3_subscenarios])
        l3_prompt = f'Question: "{user_query}"\nSub-scenarios:\n{l3_list}\n\nSelect ID:'
        llm_result = call_llm_fast(l3_prompt, max_tokens=20)
        
        match = re.search(r'\d+', llm_result or '')
        if not match:
            return JsonResponse({'error': 'Sub-scenario selection failed'}, status=500)
        
        l3_id = int(match.group())
        
        # 快速匹配L4
        l4_intentions = get_l4_intentions(l3_id)
        if not l4_intentions:
            return JsonResponse({'error': 'No intentions found'}, status=404)
        
        l4_list = "\n".join([f"{i[0]}. {i[1]}" for i in l4_intentions])
        l4_prompt = f'Question: "{user_query}"\nIntentions:\n{l4_list}\n\nSelect ID:'
        llm_result = call_llm_fast(l4_prompt, max_tokens=20)
        
        match = re.search(r'\d+', llm_result or '')
        if not match:
            return JsonResponse({'error': 'Intention selection failed'}, status=500)
        
        l4_id = int(match.group())
        
        # 获取完整内容
        content = get_l4_full_content(l4_id)
        if not content:
            return JsonResponse({'error': 'Content not found'}, status=404)
        
        return JsonResponse({
            'step': 'final_answer',
            'intention': content['name'],
            'content': {
                'five_elements_insight': content['five_elements_insight'],
                'action_guide': content['action_guide'],
                'communication_scripts': content['communication_scripts'],
                'energy_harmonization': content['energy_harmonization']
            }
        })
        
    except Exception as e:
        print(f"Error in quick_answer: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# 定期清理过期会话（可以用定时任务）
def cleanup_old_sessions():
    """清理超过1小时的会话"""
    current_time = time.time()
    expired = [sid for sid, sess in SESSIONS.items() 
               if current_time - sess['created_at'] > 3600]
    for sid in expired:
        del SESSIONS[sid]
    print(f"Cleaned up {len(expired)} expired sessions")
