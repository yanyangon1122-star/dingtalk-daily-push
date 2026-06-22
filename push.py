#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日推送脚本：获取黄历信息并发送到钉钉群"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime
import calendar

WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK')

def get_lunar_info():
    """调用农历API获取今日黄历信息"""
    today = datetime.now()
    year, month, day = today.year, today.month, today.day

    # 使用免费农历API
    try:
        url = f"https://api.oick.cn/api/lunar?date={year}-{month:02d}-{day:02d}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
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

    # 备用方案：使用另一个API
    try:
        url = f"https://timor.tech/api/huangli/day/{year}{month:02d}{day:02d}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('code') == 0:
                result = data.get('data', {})
                return {
                    'lunar_date': result.get('lunar', ''),
                    'gz_year': result.get('year_gan支', ''),
                    'gz_month': result.get('month_gan支', ''),
                    'gz_day': result.get('day_gan支', ''),
                    'yi': result.get('yi', ''),
                    'ji': result.get('ji', ''),
                }
    except Exception as e:
        print(f"备用API调用失败: {e}")

    return None

def get_greeting():
    """根据时间生成问候语"""
    hour = datetime.now().hour
    if hour < 12:
        return "早上好"
    elif hour < 18:
        return "下午好"
    else:
        return "晚上好"

def build_message():
    """构建推送消息"""
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    weekday = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]
    greeting = get_greeting()

    lunar = get_lunar_info()

    # 构建消息内容
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
    lines.append("---")
    lines.append("")
    lines.append("**每日一句**")
    lines.append("")
    lines.append("🇨🇳 你好，我叫小杨。")
    lines.append("🇧 Hello, my name is Yang.")
    lines.append("🇪🇸 Hola, me llamo Yang.")
    lines.append("🇰🇷 안녕하세요, 제 이름은 양입니다.")

    return "\n".join(lines)

def send_to_dingtalk(text):
    """发送到钉钉"""
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
