"""
Bazi MCP Client - 通过 MCP stdio 协议调用 bazi-mcp 工具
"""
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


def call_bazi_mcp(solar_datetime=None, lunar_datetime=None, gender=1, provider_sect=2):
    """
    通过 MCP stdio 协议调用 bazi-mcp 工具获取八字排盘结果
    
    参数:
        solar_datetime (str): 公历时间，ISO格式，例如 "2000-05-15T12:00:00+08:00"
        lunar_datetime (str): 农历时间，例如 "2000-05-15 12:00:00"
        gender (int): 性别，0-女，1-男，默认1
        provider_sect (int): 早晚子时配置，1或2，默认2
    
    返回:
        dict: 八字排盘结果
        None: 调用失败时返回None
    """
    try:
        # 构建工具参数
        tool_args = {
            "gender": gender,
            "eightCharProviderSect": provider_sect
        }
        
        if solar_datetime:
            tool_args["solarDatetime"] = solar_datetime
        elif lunar_datetime:
            tool_args["lunarDatetime"] = lunar_datetime
        else:
            logger.error("必须提供 solar_datetime 或 lunar_datetime 之一")
            return None
        
        # 构建 MCP 请求（JSON-RPC 格式）
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "getBaziDetail",
                "arguments": tool_args
            }
        }
        
        request_json = json.dumps(mcp_request)
        print(f"[MCP] 发送请求: {request_json}")
        
        # 启动 MCP 服务器进程（stdio 模式）
        process = subprocess.Popen(
            ["npx", "bazi-mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',  # 强制使用 UTF-8 编码
            errors='ignore',   # 忽略无法解码的字符
            shell=True  # Windows 需要
        )
        
        # 发送请求并获取响应
        stdout, stderr = process.communicate(input=request_json + "\n", timeout=10)
        
        if stderr:
            print(f"[MCP] 错误输出: {stderr}")
        
        if not stdout:
            logger.error("MCP 服务器无响应")
            return None
        
        print(f"[MCP] 原始响应: {stdout[:500]}...")  # 打印前500字符
        
        # 解析响应（可能有多行，找到包含 result 的那一行）
        lines = stdout.strip().split('\n')
        for line in lines:
            try:
                response = json.loads(line)
                if "result" in response:
                    # MCP 响应格式: {"jsonrpc": "2.0", "id": 1, "result": {...}}
                    result_data = response["result"]
                    
                    # MCP 可能返回 content 数组格式
                    if isinstance(result_data, dict) and "content" in result_data:
                        # 格式: {"content": [{"type": "text", "text": "..."}]}
                        content_list = result_data["content"]
                        if content_list and len(content_list) > 0:
                            text_content = content_list[0].get("text", "")
                            if text_content:
                                bazi_result = json.loads(text_content)
                                print(f"[MCP] 成功获取八字排盘")
                                return bazi_result
                    else:
                        # 直接返回格式
                        bazi_result = result_data
                        if isinstance(bazi_result, str):
                            bazi_result = json.loads(bazi_result)
                        print(f"[MCP] 成功获取八字排盘")
                        return bazi_result
                        
                elif "error" in response:
                    logger.error(f"MCP 返回错误: {response['error']}")
                    return None
            except json.JSONDecodeError:
                continue
        
        logger.error("无法解析 MCP 响应")
        return None
        
    except subprocess.TimeoutExpired:
        logger.error("MCP 调用超时")
        process.kill()
        return None
    except Exception as e:
        logger.error(f"调用 MCP 发生异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_bazi_for_llm(bazi_result):
    """
    将八字排盘结果格式化为适合 LLM 理解的文本
    
    参数:
        bazi_result (dict): call_bazi_mcp 返回的排盘结果
    
    返回:
        str: 格式化后的文本描述
    """
    if not bazi_result:
        return ""
    
    try:
        # 提取核心信息
        text_parts = []
        
        # 基本信息
        text_parts.append(f"性别：{bazi_result.get('性别', '')}")
        text_parts.append(f"阳历：{bazi_result.get('阳历', '')}")
        text_parts.append(f"农历：{bazi_result.get('农历', '')}")
        text_parts.append(f"八字：{bazi_result.get('八字', '')}")
        text_parts.append(f"生肖：{bazi_result.get('生肖', '')}")
        text_parts.append(f"日主：{bazi_result.get('日主', '')}")
        
        # 四柱信息（年月日时）
        pillars = ['年柱', '月柱', '日柱', '时柱']
        for pillar_name in pillars:
            pillar = bazi_result.get(pillar_name, {})
            if pillar:
                tian_gan = pillar.get('天干', {})
                di_zhi = pillar.get('地支', {})
                text_parts.append(f"\n{pillar_name}：")
                text_parts.append(f"  天干：{tian_gan.get('天干', '')} ({tian_gan.get('五行', '')}{tian_gan.get('阴阳', '')})")
                if pillar_name != '日柱':  # 日柱天干没有十神
                    text_parts.append(f"  十神：{tian_gan.get('十神', '')}")
                text_parts.append(f"  地支：{di_zhi.get('地支', '')} ({di_zhi.get('五行', '')}{di_zhi.get('阴阳', '')})")
                text_parts.append(f"  纳音：{pillar.get('纳音', '')}")
                text_parts.append(f"  运势：{pillar.get('星运', '')}")
        
        # 命宫、身宫
        text_parts.append(f"\n命宫：{bazi_result.get('命宫', '')}")
        text_parts.append(f"身宫：{bazi_result.get('身宫', '')}")
        
        # 神煞（精简显示）
        shen_sha = bazi_result.get('神煞', {})
        if shen_sha:
            text_parts.append("\n神煞（重要）：")
            for pillar_name in pillars:
                sha_list = shen_sha.get(pillar_name, [])
                if sha_list:
                    text_parts.append(f"  {pillar_name}：{', '.join(sha_list[:5])}")  # 只显示前5个
        
        # 大运（只显示当前和未来2个）
        da_yun = bazi_result.get('大运', {})
        if da_yun and '大运' in da_yun:
            text_parts.append(f"\n起运年龄：{da_yun.get('起运年龄', '')}岁")
            yun_list = da_yun['大运'][:3]  # 只取前3个大运
            text_parts.append("大运（近期）：")
            for yun in yun_list:
                text_parts.append(
                    f"  {yun.get('干支', '')} ({yun.get('开始年份', '')}-{yun.get('结束', '')}年, "
                    f"{yun.get('开始年龄', '')}-{yun.get('结束年龄', '')}岁) - "
                    f"天干：{yun.get('天干十神', '')}"
                )
        
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.error(f"格式化八字结果失败: {e}")
        return ""


# 测试代码
if __name__ == "__main__":
    # 测试：1998年7月31日14:10生人
    solar_time = "1998-07-31T14:10:00+08:00"
    
    print("测试调用 bazi-mcp...")
    result = call_bazi_mcp(solar_datetime=solar_time, gender=1)
    
    if result:
        print("\n✅ 成功获取排盘结果！")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n" + "="*50)
        print("格式化后的文本：")
        print("="*50)
        formatted = format_bazi_for_llm(result)
        print(formatted)
    else:
        print("\n❌ 调用失败")
