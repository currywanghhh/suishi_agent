"""
八字算命机 - 基于 MCP 的命理分析工具
输入生辰八字，输出详细的命理分析报告
"""
import json
from mcp_client import call_bazi_mcp, parse_datetime_input
from datetime import datetime


class BaziFortuneTeller:
    """八字分析器"""
    
    def __init__(self):
        self.wuxing_meaning = {
            '木': {'属性': '生长、仁慈', '颜色': '绿色', '方位': '东方', '季节': '春季'},
            '火': {'属性': '热情、礼貌', '颜色': '红色', '方位': '南方', '季节': '夏季'},
            '土': {'属性': '稳重、诚信', '颜色': '黄色', '方位': '中央', '季节': '四季'},
            '金': {'属性': '刚毅、义气', '颜色': '白色', '方位': '西方', '季节': '秋季'},
            '水': {'属性': '智慧、灵活', '颜色': '黑色', '方位': '北方', '季节': '冬季'},
        }
    
    def analyze_bazi(self, birth_date, birth_time, gender, timezone="+08:00"):
        """
        分析八字命盘
        
        参数:
            birth_date: "1998-07-31"
            birth_time: "14:10"
            gender: 1=男, 0=女
            timezone: 时区
        """
        # 转换为 ISO 格式
        iso_datetime = parse_datetime_input(birth_date, birth_time, timezone)
        
        # 调用 MCP 获取排盘
        print("\n🔮 正在计算八字排盘...")
        bazi_result = call_bazi_mcp(solar_datetime=iso_datetime, gender=gender)
        
        if not bazi_result:
            print("❌ 排盘失败，请检查 MCP 工具是否正确安装")
            return None
        
        return bazi_result
    
    def print_basic_info(self, bazi_result):
        """打印基本信息"""
        print("\n" + "="*60)
        print("📋 基本信息")
        print("="*60)
        print(f"性别：{bazi_result.get('性别', '')}")
        print(f"阳历：{bazi_result.get('阳历', '')}")
        print(f"农历：{bazi_result.get('农历', '')}")
        print(f"生肖：{bazi_result.get('生肖', '')} 🐯" if '虎' in str(bazi_result.get('生肖', '')) else f"生肖：{bazi_result.get('生肖', '')}")
        print(f"八字：{bazi_result.get('八字', '')}")
        print(f"日主：{bazi_result.get('日主', '')} (你的核心五行)")
    
    def print_four_pillars(self, bazi_result):
        """打印四柱详情"""
        print("\n" + "="*60)
        print("🏛️  四柱详解（年月日时）")
        print("="*60)
        
        pillars = [
            ('年柱', bazi_result.get('年柱', {})),
            ('月柱', bazi_result.get('月柱', {})),
            ('日柱', bazi_result.get('日柱', {})),
            ('时柱', bazi_result.get('时柱', {}))
        ]
        
        for name, pillar in pillars:
            if not pillar:
                continue
            
            tian_gan = pillar.get('天干', {})
            di_zhi = pillar.get('地支', {})
            
            print(f"\n【{name}】")
            print(f"  天干：{tian_gan.get('天干', '')} ({tian_gan.get('五行', '')}{tian_gan.get('阴阳', '')})", end="")
            if tian_gan.get('十神'):
                print(f" - {tian_gan.get('十神', '')}", end="")
            print()
            
            print(f"  地支：{di_zhi.get('地支', '')} ({di_zhi.get('五行', '')}{di_zhi.get('阴阳', '')})")
            
            # 地支藏干
            cang_gan = di_zhi.get('藏干', {})
            if cang_gan:
                print(f"  藏干：", end="")
                parts = []
                if cang_gan.get('主气'):
                    parts.append(f"{cang_gan['主气'].get('天干', '')}({cang_gan['主气'].get('十神', '')})")
                if cang_gan.get('中气'):
                    parts.append(f"{cang_gan['中气'].get('天干', '')}({cang_gan['中气'].get('十神', '')})")
                if cang_gan.get('余气'):
                    parts.append(f"{cang_gan['余气'].get('天干', '')}({cang_gan['余气'].get('十神', '')})")
                print(" / ".join(parts))
            
            print(f"  纳音：{pillar.get('纳音', '')}")
            print(f"  运势：{pillar.get('星运', '')} (自坐{pillar.get('自坐', '')})")
    
    def print_wuxing_analysis(self, bazi_result):
        """打印五行分析"""
        print("\n" + "="*60)
        print("🌈 五行分析")
        print("="*60)
        
        # 统计五行
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
        
        # 打印统计
        print("\n五行数量统计：")
        for wx, count in wuxing_count.items():
            bar = "█" * count + "░" * (5 - count)
            info = self.wuxing_meaning[wx]
            print(f"  {wx} {bar} {count}个 ({info['属性']}) - {info['颜色']}/{info['方位']}")
        
        # 分析强弱
        max_wx = max(wuxing_count, key=wuxing_count.get)
        min_wx = min(wuxing_count, key=wuxing_count.get)
        
        print(f"\n✨ 五行特征：")
        print(f"  最旺：{max_wx} ({wuxing_count[max_wx]}个) - {self.wuxing_meaning[max_wx]['属性']}")
        if wuxing_count[min_wx] == 0:
            print(f"  缺失：{min_wx} - 建议补充{self.wuxing_meaning[min_wx]['颜色']}系")
        else:
            print(f"  最弱：{min_wx} ({wuxing_count[min_wx]}个)")
    
    def print_dayun(self, bazi_result):
        """打印大运"""
        dayun_data = bazi_result.get('大运', {})
        if not dayun_data or '大运' not in dayun_data:
            return
        
        print("\n" + "="*60)
        print("🔮 大运分析（人生阶段运势）")
        print("="*60)
        
        print(f"\n起运年龄：{dayun_data.get('起运年龄', '')}岁")
        print(f"起运日期：{dayun_data.get('起运日期', '')}")
        
        dayun_list = dayun_data.get('大运', [])
        current_year = datetime.now().year
        
        print("\n运势列表：")
        for i, yun in enumerate(dayun_list[:6], 1):  # 显示前6个大运
            gan_zhi = yun.get('干支', '')
            start_year = yun.get('开始年份', '')
            end_year = yun.get('结束', '')
            start_age = yun.get('开始年龄', '')
            end_age = yun.get('结束年龄', '')
            tian_gan_shishen = yun.get('天干十神', '')
            
            # 判断是否当前大运
            is_current = start_year <= current_year <= end_year if isinstance(start_year, int) else False
            marker = "👉 " if is_current else "   "
            
            print(f"{marker}{i}. {gan_zhi} ({start_year}-{end_year}年, {start_age}-{end_age}岁) - {tian_gan_shishen}")
    
    def print_shensha(self, bazi_result):
        """打印神煞"""
        shensha = bazi_result.get('神煞', {})
        if not shensha:
            return
        
        print("\n" + "="*60)
        print("⭐ 神煞分析")
        print("="*60)
        
        pillars = ['年柱', '月柱', '日柱', '时柱']
        for pillar_name in pillars:
            sha_list = shensha.get(pillar_name, [])
            if sha_list:
                print(f"\n{pillar_name}：{', '.join(sha_list[:8])}")  # 只显示前8个
    
    def print_fortune_summary(self, bazi_result):
        """打印运势总结"""
        print("\n" + "="*60)
        print("💡 简要总结")
        print("="*60)
        
        ri_zhu = bazi_result.get('日主', '')
        bazi_str = bazi_result.get('八字', '')
        
        print(f"\n你的日主是【{ri_zhu}】，八字为【{bazi_str}】")
        print("\n这份命盘的特点：")
        print("• 天干地支组合形成独特的五行格局")
        print("• 大运流转影响人生不同阶段的运势")
        print("• 神煞显示特殊的命理特征")
        print("\n💡 提示：命理仅供参考，人生还需自己把握！")
    
    def generate_full_report(self, birth_date, birth_time, gender, timezone="+08:00"):
        """生成完整报告"""
        print("\n" + "🌟"*30)
        print("           八字命理分析报告")
        print("🌟"*30)
        
        # 获取排盘结果
        bazi_result = self.analyze_bazi(birth_date, birth_time, gender, timezone)
        
        if not bazi_result:
            return
        
        # 打印各部分
        self.print_basic_info(bazi_result)
        self.print_four_pillars(bazi_result)
        self.print_wuxing_analysis(bazi_result)
        self.print_dayun(bazi_result)
        self.print_shensha(bazi_result)
        self.print_fortune_summary(bazi_result)
        
        # 保存原始数据
        print("\n" + "="*60)
        print("💾 完整数据已保存")
        print("="*60)
        
        filename = f"bazi_result_{birth_date.replace('-', '')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(bazi_result, f, ensure_ascii=False, indent=2)
        
        print(f"文件路径：{filename}")
        print("\n✅ 分析完成！")


def main():
    """主函数：交互式输入"""
    teller = BaziFortuneTeller()
    
    print("\n" + "="*60)
    print("🔮 欢迎使用八字算命机")
    print("="*60)
    
    # 获取用户输入
    print("\n请输入生辰信息：")
    birth_date = input("📅 出生日期（格式：1998-07-31）：").strip()
    birth_time = input("⏰ 出生时间（格式：14:10）：").strip()
    gender_input = input("👤 性别（男/女）：").strip()
    
    gender = 1 if gender_input in ['男', 'M', 'm', '1'] else 0
    
    # 生成报告
    teller.generate_full_report(birth_date, birth_time, gender)


if __name__ == "__main__":
    # 两种使用方式：
    
    # 方式1：交互式输入（取消注释使用）
    # main()
    
    # 方式2：直接调用（示例）
    teller = BaziFortuneTeller()
    teller.generate_full_report(
        birth_date="1998-07-31",
        birth_time="14:10",
        gender=1
    )
