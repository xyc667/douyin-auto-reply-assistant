#!/usr/bin/env python3
"""
测试手动发送私信功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('config_ai.env')

from builder.auth import DouyinAuth
from dy_apis.douyin_api import DouyinAPI

# 获取Cookie
cookies_str = os.getenv('DY_COOKIES_MS', '') or os.getenv('DY_COOKIES', '')
web_protect_str = os.getenv('WEB_PROTECT', '')
keys_str = os.getenv('KEYS', '')

print("=" * 60)
print("🧪 测试手动发送私信功能")
print("=" * 60)
print()

# 初始化认证
print("1. 初始化认证...")
auth = DouyinAuth()
auth.perepare_auth(cookies_str, web_protect_str, keys_str)
print("   ✅ 认证成功")
print()

# 测试发送
print("2. 测试发送私信...")
print()

# 获取一个对话ID（用之前的测试对话）
conversation_id = "0:1:105228751401:3616768185600628"
conversation_short_id = 7642920038051185179
ticket = ""
reply_text = "你好呀~我是手动测试"

print(f"发送内容: {reply_text}")
print(f"目标对话: {conversation_id}")
print()

try:
    DouyinAPI.send_msg(
        auth,
        conversation_id,
        conversation_short_id,
        ticket,
        reply_text
    )
    print()
    print("✅ 发送成功！")
    print("请检查对方是否收到消息")
except Exception as e:
    print()
    print(f"❌ 发送失败: {e}")
    import traceback
    traceback.print_exc()
