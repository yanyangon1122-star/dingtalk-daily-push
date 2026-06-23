#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日推送脚本：黄历 + 运势 + 每日一句四语"""

import json
import os
import urllib.request
import ssl
from datetime import datetime, timedelta

WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK')
BAZI = os.environ.get('USER_BAZI', '甲戌年 乙亥月 壬子日 甲辰时')

# 天干地支
TIAN_GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DI_ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
    '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
    '戌': '土', '亥': '水'
}

# 月建（节气月）- 以立春为岁首
MONTH_ZHI = {1: '丑', 2: '寅', 3: '卯', 4: '辰', 5: '巳', 6: '午',
             7: '未', 8: '申', 9: '酉', 10: '戌', 11: '亥', 12: '子'}
# 简化：按月份近似（实际应按节气，这里近似处理）

def get_year_gz(year):
    """计算年干支 - 参考：2024=甲辰"""
    gan_idx = (year - 4) % 10
    zhi_idx = (year - 4) % 12
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_month_gz(year, month):
    """计算月干支"""
    year_gan_idx = (year - 4) % 10
    # 月支映射：阳历月→地支索引
    # 1月丑(1), 2月寅(2), 3月卯(3), 4月辰(4), 5月巳(5), 6月午(6), 7月未(7)
    # 8月申(8), 9月酉(9), 10月戌(10), 11月亥(11), 12月子(0)
    # 注意：这里近似将阳历月直接对应，实际应按节气
    month_zhi_map = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0]
    zhi_idx = month_zhi_map[month - 1]
    # 五虎遁：甲己丙首(2), 乙庚戊头(4), 丙辛庚起(6), 丁壬壬位(8), 戊癸甲寅(0)
    month_gan_start = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]
    # 正月(zhi=2, 2月)对应month_gan_start
    gan_idx = (month_gan_start[year_gan_idx] + zhi_idx - 2) % 10
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_day_gz(year, month, day):
    """计算日干支 - 参考：2024-01-01=壬子"""
    ref_date = datetime(2024, 1, 1)
    target_date = datetime(year, month, day)
    diff = (target_date - ref_date).days
    gan_idx = (8 + diff) % 10  # 壬=8
    zhi_idx = (0 + diff) % 12  # 子=0
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_lunar_info():
    """获取干支信息（本地计算，不依赖外部API）"""
    try:
        today = datetime.now()
        year, month, day = today.year, today.month, today.day
        gz_year = get_year_gz(year)
        gz_month = get_month_gz(year, month)
        gz_day = get_day_gz(year, month, day)
        return {
            'gz_year': gz_year,
            'gz_month': gz_month,
            'gz_day': gz_day,
        }
    except Exception as e:
        print(f"干支计算失败: {e}")
    return None

# 十神详细解读
SHISHEN_INFO = {
    '正印': {
        'label': '正印当值',
        'tips': ['学习运强，适合吸收新知识、阅读充电', '贵人运佳，长辈或上司愿意提供帮助', '心态平和，适合做长远规划']
    },
    '偏印': {
        'label': '偏印当值',
        'tips': ['灵感突现，适合思考非传统方案', '直觉敏锐，可关注一闪而过的想法', '注意不要过度钻牛角尖']
    },
    '正官': {
        'label': '正官当值',
        'tips': ['规则意识强，适合处理制度流程相关事务', '注意言行举止，谨言慎行', '适合向上级汇报、争取认可']
    },
    '七杀': {
        'label': '七杀当值',
        'tips': ['压力较大，但也是突破瓶颈的机会', '注意情绪管理，避免冲动决策', '适合处理紧急或挑战性任务']
    },
    '正财': {
        'label': '正财当值',
        'tips': ['正财运佳，工资奖金相关事宜顺利', '适合推进商务谈判、签署合同', '稳扎稳打，不宜冒险投机']
    },
    '偏财': {
        'label': '偏财当值',
        'tips': ['偏财运不错，可能有意外收获', '适合开拓新业务、接触新客户', '注意把握机会但保持理性']
    },
    '食神': {
        'label': '食神当值',
        'tips': ['创造力强，适合推进新项目、头脑风暴', '表达能力佳，沟通顺畅', '心情愉悦，人际关系和谐']
    },
    '伤官': {
        'label': '伤官当值',
        'tips': ['思维活跃，适合创新策划、提出新方案', '表达欲强，注意言辞不要太直接', '适合做汇报、演讲等展示类工作']
    },
    '劫财': {
        'label': '劫财当值',
        'tips': ['竞争激烈，注意保护自身利益', '合作中明确分工和利益分配', '不宜大额支出或借贷']
    },
    '日主': {
        'label': '日主当值',
        'tips': ['自身能量最强，适合独立决策、主导事务', '意志坚定，执行力强', '适合推进个人重要事项']
    }
}

WUXING_INFO = {
    '水': {
        'traits': '思维敏捷、灵活变通',
        'warning': '注意情绪波动，避免思虑过度'
    },
    '火': {
        'traits': '行动力强、热情积极',
        'warning': '注意避免急躁冲动，三思后行'
    },
    '木': {
        'traits': '生机勃勃、善于开拓',
        'warning': '注意不要急于求成，稳扎稳打'
    },
    '金': {
        'traits': '决断力强、条理清晰',
        'warning': '注意不要过于刚硬，适当灵活变通'
    },
    '土': {
        'traits': '稳重踏实、可靠值得信赖',
        'warning': '适合巩固既有成果，不宜冒险'
    }
}

# 壬日主的十神映射
RIZHU_SHISHEN = {
    '壬': '日主', '癸': '劫财', '甲': '食神', '乙': '伤官',
    '丙': '偏财', '丁': '正财', '戊': '七杀', '己': '正官',
    '庚': '偏印', '辛': '正印'
}

def analyze_fortune(day_gz):
    if not day_gz or len(day_gz) < 2:
        return []
    day_tian = day_gz[0]
    day_di = day_gz[1]
    # 先根据日主(壬)映射到天干对应的十神名称
    shishen_name = RIZHU_SHISHEN.get(day_tian, '')
    shishen = SHISHEN_INFO.get(shishen_name, None)
    tian_wuxing = WUXING.get(day_tian, '')
    fortune = []
    if shishen:
        fortune.append(f"**{shishen['label']}**")
        for tip in shishen['tips']:
            fortune.append(f"• {tip}")
    elif shishen_name:
        fortune.append(f"**{shishen_name}当值**")
        fortune.append("• 今日运势信息获取中")
    else:
        fortune.append(f"**{day_tian}当值**")
        fortune.append("• 今日运势信息获取中")
    if tian_wuxing and tian_wuxing in WUXING_INFO:
        info = WUXING_INFO[tian_wuxing]
        fortune.append(f"**五行特点**：{info['traits']}；{info['warning']}")
    return fortune

def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "早上好"
    elif hour < 18:
        return "下午好"
    else:
        return "晚上好"

DAILY_QUOTES = [
    {"zh": "今天天气真好。", "en": "The weather is really nice today.", "es": "Hoy hace muy buen tiempo.", "ko": "오늘 날씨가 정말 좋네요."},
    {"zh": "你吃了吗？", "en": "Have you eaten yet?", "es": "¿Ya has comido?", "ko": "밥 먹었어요?"},
    {"zh": "路上小心。", "en": "Be careful on your way.", "es": "Ten cuidado en el camino.", "ko": "길 조심하세요."},
    {"zh": "早点休息。", "en": "Rest early tonight.", "es": "Descansa temprano esta noche.", "ko": "일찍 쉬세요."},
    {"zh": "加油，你可以的！", "en": "You can do it!", "es": "¡Tú puedes hacerlo!", "ko": "힘내요, 할 수 있어요!"},
    {"zh": "慢慢来，不着急。", "en": "Take your time, no rush.", "es": "Tómate tu tiempo, sin prisa.", "ko": "천천히 해요, 급하지 않아요."},
    {"zh": "辛苦了，谢谢你。", "en": "Thank you for your hard work.", "es": "Gracias por tu arduo trabajo.", "ko": "수고하셨어요, 감사합니다."},
]

def get_daily_quote():
    day_of_year = datetime.now().timetuple().tm_yday
    return DAILY_QUOTES[day_of_year % len(DAILY_QUOTES)]

def build_message():
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]
    greeting = get_greeting()
    lunar = get_lunar_info()
    day_gz = lunar['gz_day'] if lunar else ''

    lines = [
        f"### {greeting} | {today_str} {weekday}",
        "",
    ]

    if lunar:
        lines.append(f"**干支**: {lunar['gz_year']}年 {lunar['gz_month']}月 {lunar['gz_day']}日")
    else:
        lines.append("今日干支信息获取中...")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**今日运势**")
    lines.append("")
    lines.append(f"**八字**: {BAZI}")
    lines.append(f"**日主**: 壬水")
    if day_gz:
        lines.append(f"**今日干支**: {lunar['gz_day']}")
    lines.append("")

    if day_gz:
        fortune = analyze_fortune(day_gz)
        for item in fortune:
            lines.append(item)
    else:
        lines.append("运势分析信息获取中...")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**每日一句**")
    lines.append("")
    quote = get_daily_quote()
    lines.append(f"CN {quote['zh']}")
    lines.append(f"EN {quote['en']}")
    lines.append(f"ES {quote['es']}")
    lines.append(f"KO {quote['ko']}")

    return "\n".join(lines)

def send_to_dingtalk(text):
    if not WEBHOOK_URL:
        print("错误：未设置DINGTALK_WEBHOOK环境变量")
        return False
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "每日推送",
            "text": text
        }
    }
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result.get('errcode') == 0:
                print("推送成功！")
                return True
            else:
                print(f"推送失败: {result}")
                return False
    except Exception as e:
        print(f"发送异常: {e}")
        return False

if __name__ == '__main__':
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    message = build_message()
    print(f"消息内容:\n{message}")
    print("-" * 40)
    send_to_dingtalk(message)
