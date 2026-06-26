#!/usr/bin/env python
print("测试1: Python 运行正常")

import sys
import pathlib
print("测试2: pathlib 导入成功")

sys.path.insert(0, str(pathlib.Path(__file__).parent))
print("测试3: sys.path 设置成功")

import os
from dotenv import load_dotenv
print("测试4: 导入 os 和 dotenv 成功")

load_dotenv()
print("测试5: load_dotenv() 执行成功")

cookies_str = os.getenv('DY_COOKIES', '')
web_protect_str = os.getenv('WEB_PROTECT', '')
keys_str = os.getenv('KEYS', '')

print(f"测试6: Cookie 长度 = {len(cookies_str)}")
print(f"测试7: web_protect 存在 = {bool(web_protect_str)}")
print(f"测试8: keys 存在 = {bool(keys_str)}")

from builder.auth import DouyinAuth
print("测试9: DouyinAuth 导入成功")

auth = DouyinAuth()
print("测试10: DouyinAuth 实例创建成功")

print("测试11: 正在调用 perepare_auth...")
auth.perepare_auth(cookies_str, web_protect_str, keys_str)
print("测试12: perepare_auth() 执行成功")

print("测试13: 正在导入 DouyinRecvMsg...")
from dy_apis.douyin_recv_msg import DouyinRecvMsg
print("测试14: DouyinRecvMsg 导入成功")

print("测试15: 正在创建 DouyinRecvMsg 实例...")
douyinMsg = DouyinRecvMsg(auth)
print("测试16: DouyinRecvMsg 实例创建成功！")

print(f"\n✅ 所有测试通过！")
print(f"WebSocket URL: {douyinMsg.url[:100]}...")