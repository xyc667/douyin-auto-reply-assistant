#!/usr/bin/env python
# 测试 get_device_id API

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()

from dy_apis.douyin_api import DouyinAPI
from builder.auth import DouyinAuth

# 获取 Cookie 和 web_protect
cookies_str = os.getenv('DY_COOKIES', '')
web_protect_str = os.getenv('WEB_PROTECT', '')
keys_str = os.getenv('KEYS', '')

print("正在初始化认证...")
auth = DouyinAuth()
auth.perepare_auth(cookies_str, web_protect_str, keys_str)

print("✅ 认证初始化成功！")
print(f"Cookie 包含 {len(auth.cookie)} 个字段")
print(f"web_protect ticket: {auth.ticket[:50] if auth.ticket else '未设置'}...")
print()

print("正在测试 get_device_id...")
try:
    device_id = DouyinAPI.get_device_id(auth=auth)
    print(f"✅ 成功获取 device_id: {device_id}")
except Exception as e:
    print(f"❌ get_device_id 失败: {e}")
    print()
    print("💡 可能的原因：")
    print("   1. Cookie 可能不完整或已过期")
    print("   2. API 返回了错误响应")
    print("   3. 需要重新获取 Cookie")