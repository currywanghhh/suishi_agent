"""
Bazi MCP Client - 独立版本
用于直接调用 MCP 工具并输出完整排盘信息
"""
import subprocess
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
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
        logger.info(f"发送 MCP 请求...")
        
        # 启动 MCP 服务器进程（stdio 模式）
        process = subprocess.Popen(
            ["npx", "bazi-mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='ignore',
            shell=True
        )
        
        # 发送请求并获取响应
        stdout, stderr = process.communicate(input=request_json + "\n", timeout=15)
        
        if stderr:
            logger.debug(f"MCP stderr: {stderr[:200]}")
        
        if not stdout:
            logger.error("MCP 服务器无响应")
            return None
        
        # 解析响应
        lines = stdout.strip().split('\n')
        for line in lines:
            try:
                response = json.loads(line)
                if "result" in response:
                    result_data = response["result"]
                    
                    # MCP 可能返回 content 数组格式
                    if isinstance(result_data, dict) and "content" in result_data:
                        content_list = result_data["content"]
                        if content_list and len(content_list) > 0:
                            text_content = content_list[0].get("text", "")
                            if text_content:
                                bazi_result = json.loads(text_content)
                                logger.info("✅ 成功获取八字排盘")
                                return bazi_result
                    else:
                        bazi_result = result_data
                        if isinstance(bazi_result, str):
                            bazi_result = json.loads(bazi_result)
                        logger.info("✅ 成功获取八字排盘")
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


def parse_datetime_input(date_str, time_str, timezone="+08:00"):
    """
    将用户输入的日期时间转换为 ISO 格式
    
    参数:
        date_str: "1998-07-31" 或 "1998/07/31"
        time_str: "14:10" 或 "14:10:00"
        timezone: "+08:00"
    
    返回:
        str: ISO 格式时间
    """
    # 统一日期格式
    date_str = date_str.replace('/', '-')
    
    # 补充秒数
    if len(time_str.split(':')) == 2:
        time_str += ":00"
    
    return f"{date_str}T{time_str}{timezone}"


if __name__ == "__main__":
    print("=" * 60)
    print("🔮 八字排盘 MCP 工具")
    print("=" * 60)
    
    # 示例：直接调用
    solar_time = "1998-07-31T14:10:00+08:00"
    gender = 1  # 男
    
    print(f"\n📅 计算时间: 1998年7月31日 14:10")
    print(f"👤 性别: {'男' if gender == 1 else '女'}")
    print("\n正在调用 MCP 工具...")
    
    result = call_bazi_mcp(solar_datetime=solar_time, gender=gender)
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 排盘成功！完整结果如下：")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n❌ 排盘失败")
