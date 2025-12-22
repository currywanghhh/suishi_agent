"""
Flask Web 应用 - 八字算命机
提供 Web 界面进行八字排盘和分析
"""
from flask import Flask, render_template, request, jsonify
from mcp_client import call_bazi_mcp, parse_datetime_input
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)

# 配置大模型 API（Silicon Flow）
SILICON_FLOW_API_KEY = os.getenv('SILICON_FLOW_API_KEY', 'sk-bqvwghqjntyjcfstntiekzlmldhabgbzvalkdkoedpgcrmdf')
SILICON_FLOW_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class BaziAnalyzer:
    """八字分析逻辑"""
    
    @staticmethod
    def analyze(birth_date, birth_time, gender, timezone="+08:00"):
        """执行八字分析"""
        iso_datetime = parse_datetime_input(birth_date, birth_time, timezone)
        bazi_result = call_bazi_mcp(solar_datetime=iso_datetime, gender=gender)
        
        if not bazi_result:
            return None
        
        # 统计五行
        wuxing_count = BaziAnalyzer.count_wuxing(bazi_result)
        
        # 格式化大运
        dayun_formatted = BaziAnalyzer.format_dayun(bazi_result)
        
        # 格式化神煞
        shensha_formatted = BaziAnalyzer.format_shensha(bazi_result)
        
        return {
            'raw': bazi_result,
            'wuxing': wuxing_count,
            'dayun': dayun_formatted,
            'shensha': shensha_formatted
        }
    
    @staticmethod
    def count_wuxing(bazi_result):
        """统计五行数量"""
        wuxing_count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        for pillar_name in pillars:
            pillar = bazi_result.get(pillar_name, {})
            if pillar:
                tg_wx = pillar.get('天干', {}).get('五行', '')
                dz_wx = pillar.get('地支', {}).get('五行', '')
                if tg_wx in wuxing_count:
                    wuxing_count[tg_wx] += 1
                if dz_wx in wuxing_count:
                    wuxing_count[dz_wx] += 1
        
        return wuxing_count
    
    @staticmethod
    def format_dayun(bazi_result):
        """格式化大运数据"""
        dayun_data = bazi_result.get('大运', {})
        if not dayun_data or '大运' not in dayun_data:
            return []
        
        dayun_list = dayun_data.get('大运', [])
        current_year = datetime.now().year
        
        formatted = []
        for yun in dayun_list[:6]:
            start_year = yun.get('开始年份', '')
            end_year = yun.get('结束', '')
            is_current = start_year <= current_year <= end_year if isinstance(start_year, int) else False
            
            formatted.append({
                'ganzhi': yun.get('干支', ''),
                'period': f"{start_year}-{end_year}年",
                'age': f"{yun.get('开始年龄', '')}-{yun.get('结束年龄', '')}岁",
                'shishen': yun.get('天干十神', ''),
                'is_current': is_current
            })
        
        return formatted
    
    @staticmethod
    def format_shensha(bazi_result):
        """格式化神煞数据"""
        shensha = bazi_result.get('神煞', {})
        if not shensha:
            return {}
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        formatted = {}
        for pillar_name in pillars:
            sha_list = shensha.get(pillar_name, [])
            if sha_list:
                formatted[pillar_name] = sha_list[:8]
        
        return formatted


def analyze_with_llm(bazi_result):
    """
    使用大模型分析八字命盘
    
    参数:
        bazi_result: MCP 返回的完整八字数据
    
    返回:
        str: 大模型的分析文本
    """
    if not SILICON_FLOW_API_KEY:
        return "⚠️ 未配置大模型 API Key，请设置 SILICON_FLOW_API_KEY 环境变量"
    
    # 构建分析 prompt
    prompt = f"""你是一位资深的命理分析师，精通八字命理学。请基于以下八字排盘结果，给出专业、详细的命理分析。

【基本信息】
性别：{bazi_result.get('性别', '')}
生肖：{bazi_result.get('生肖', '')}
阳历：{bazi_result.get('阳历', '')}
农历：{bazi_result.get('农历', '')}
八字：{bazi_result.get('八字', '')}
日主：{bazi_result.get('日主', '')}

【四柱详解】
年柱：{bazi_result.get('年柱', {}).get('天干', {}).get('天干', '')}{bazi_result.get('年柱', {}).get('地支', {}).get('地支', '')} - {bazi_result.get('年柱', {}).get('天干', {}).get('十神', '')}
月柱：{bazi_result.get('月柱', {}).get('天干', {}).get('天干', '')}{bazi_result.get('月柱', {}).get('地支', {}).get('地支', '')} - {bazi_result.get('月柱', {}).get('天干', {}).get('十神', '')}
日柱：{bazi_result.get('日柱', {}).get('天干', {}).get('天干', '')}{bazi_result.get('日柱', {}).get('地支', {}).get('地支', '')}
时柱：{bazi_result.get('时柱', {}).get('天干', {}).get('天干', '')}{bazi_result.get('时柱', {}).get('地支', {}).get('地支', '')} - {bazi_result.get('时柱', {}).get('天干', {}).get('十神', '')}

【命宫身宫】
命宫：{bazi_result.get('命宫', '')}
身宫：{bazi_result.get('身宫', '')}

请从以下几个方面进行分析（每个方面100-150字）：

1. **性格特征分析**：基于日主和四柱组合，分析此人的性格特点、优势与不足。

2. **五行格局分析**：分析五行强弱，指出命盘的整体格局和特点。

3. **事业财运倾向**：根据十神关系和五行配置，分析适合的事业方向和财运特点。

4. **人际关系与健康**：从命盘看人际交往模式和需要注意的健康问题。

5. **大运流年建议**：当前阶段的运势特点和生活建议。

注意：
- 语言要专业但易懂，避免过于晦涩的术语
- 分析要客观，既要指出优势，也要提醒需要注意的地方
- 给出实用的建议
- 每个部分用 ### 标题分隔
"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            SILICON_FLOW_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result['choices'][0]['message']['content']
            return analysis
        else:
            return f"⚠️ 大模型调用失败: {response.status_code} - {response.text[:200]}"
            
    except Exception as e:
        return f"⚠️ 大模型分析异常: {str(e)}"


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """分析接口"""
    try:
        data = request.get_json()
        
        birth_date = data.get('birth_date')
        birth_time = data.get('birth_time')
        gender = int(data.get('gender', 1))
        timezone = data.get('timezone', '+08:00')
        use_llm = data.get('use_llm', False)  # 是否使用大模型分析
        
        # 验证输入
        if not birth_date or not birth_time:
            return jsonify({'error': '请输入完整的出生日期和时间'}), 400
        
        # 执行分析
        result = BaziAnalyzer.analyze(birth_date, birth_time, gender, timezone)
        
        if not result:
            return jsonify({'error': 'MCP 工具调用失败，请检查配置'}), 500
        
        # 如果请求大模型分析
        llm_analysis = None
        if use_llm:
            llm_analysis = analyze_with_llm(result['raw'])
        
        return jsonify({
            'success': True, 
            'data': result,
            'llm_analysis': llm_analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/raw/<path:filename>')
def download_raw(filename):
    """下载原始 JSON 数据"""
    # 这里可以实现下载功能
    pass


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔮 八字算命机 Web 服务启动")
    print("="*60)
    print("\n访问地址：http://127.0.0.1:5000")
    
    if SILICON_FLOW_API_KEY:
        print("✅ 大模型 API 已配置")
    else:
        print("⚠️  大模型 API 未配置（可选功能）")
        print("   设置环境变量: set SILICON_FLOW_API_KEY=你的key")
    
    print("\n按 Ctrl+C 停止服务\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
