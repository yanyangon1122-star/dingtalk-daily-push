#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日推送脚本：黄历 + 运势 + 每日一句"""

import json
import os
import urllib.request
import ssl
from datetime import datetime

WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK')
BAZI = os.environ.get('USER_BAZI', '甲戌年 乙亥月 壬子日 甲辰时')

WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土',
    '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金',
    '戌': '土', '亥': '水'
}

SHISHEN = {
    '壬': '日主', '癸': '劫财', '甲': '食神', '乙': '伤官',
    '丙': '偏财', '丁': '正财', '戊': '七杀', '己': '正官',
    '庚': '偏印', '辛': '正印'
}

def get_lunar_info():
    today = datetime.now()
    year, month, day = today.year, today.month, today.day
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        url = f"https://api.oick.cn/api/lunar?date={year}-{month:02d}-{day:02d}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('code') == 200:
                result = data.get('data', {})
                return {
                    'lunar_date': result.get('lunar', ''),
                    'gz_year': result.get('gzYear', ''),
                    'gz_month': result.get('gzMonth', ''),
                    'gz_day': result.get('gzDay', ''),
                    'yi': result.get('yi', ''),
                    'ji': result.get('ji', ''),
                }
    except Exception as e:
        print(f"农历API调用失败: {e}")
    return None

def analyze_fortune(day_gz):
    if not day_gz:
        return "今日运势：信息获取中"
    day_tian = day_gz[0] if day_gz else ''
    day_di = day_gz[1] if len(day_gz) > 1 else ''
    shishen = SHISHEN.get(day_tian, '')
    tian_wuxing = WUXING.get(day_tian, '')
    fortune = []
    if shishen in ('正印', '偏印'):
        fortune.append("印星当值，适合学习充电、思考规划")
        fortune.append("贵人运佳，可寻求长辈或上司指导")
    elif shishen in ('正官', '七杀'):
        fortune.append("官杀当值，工作压力较大")
        fortune.append("注意言行举止，谨慎处理人际关系")
    elif shishen in ('正财', '偏财'):
        fortune.append("财星当值，财运不错")
        fortune.append("适合推进商务谈判或处理财务事项")
    elif shishen in ('食神', '伤官'):
        fortune.append("食伤当值，创造力强")
        fortune.append("适合表达观点、推进新项目")
    elif shishen == '劫财':
        fortune.append("比劫当值，竞争激烈")
        fortune.append("注意合作中的利益分配")
    else:
        fortune.append("日主当值，自身能量强")
        fortune.append("适合独立决策、主导事务")
    if tian_wuxing == '水':
        fortune.append("水旺之日，思维敏捷，但注意情绪波动")
    elif tian_wuxing == '火':
        fortune.append("火旺之日，行动力强，注意避免急躁")
    elif tian_wuxing == '木':
        fortune.append("木旺之日，生机勃勃，适合开拓创新")
    elif tian_wuxing == '金':
        fortune.append("金旺之日，决断力强，注意过于刚硬")
    elif tian_wuxing == '土':
        fortune.append("土旺之日，稳重踏实，适合巩固既有成果")
    return fortune

def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "早上好"
    elif hour < 18:
        return "下午好"
    else:
        return "晚上好"

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
        lines.append(f"**农历**: {lunar['lunar_date']}")
        lines.append(f"**干支**: {lunar['gz_year']}年 {lunar['gz_month']}月 {lunar['gz_day']}日")
        if lunar.get('yi'):
            lines.append(f"**宜**: {lunar['yi']}")
        if lunar.get('ji'):
            lines.append(f"**忌**: {lunar['ji']}")
    else:
        lines.append("今日黄历信息获取中...")

    lines.append("")
    lines.append("**今日运势**")
    lines.append("")
    lines.append(f"**八字**: {BAZI}")
    lines.append(f"**日主**: 壬水")
    lines.append("")

    if day_gz:
        fortune = analyze_fortune(day_gz)
        for item in fortune:
            lines.append(f"• {item}")
    else:
        lines.append("运势分析信息获取中...")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**每日一句**")
    lines.append("")
    lines.append("🇨🇳 你好，我叫小杨。")
    lines.append("🇬 Hello, my name is Yang.")
    lines.append("🇪 Hola, me llamo Yang.")
    lines.append("🇰🇷 안녕하세요, 제 이름은 양입니다.")

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
