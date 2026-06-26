#!/usr/bin/env python
# 调试 get_device_id API - 查看完整响应

import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import os
from dotenv import load_dotenv
load_dotenv()

import json
import requests
from dy_apis.douyin_api import DouyinAPI
from builder.auth import DouyinAuth
from builder.params import Params

# 获取 Cookie 和 web_protect
cookies_str = os.getenv('DY_COOKIES', '')
web_protect_str = os.getenv('WEB_PROTECT', '')
keys_str = os.getenv('KEYS', '')

print("正在初始化认证...")
auth = DouyinAuth()
auth.perepare_auth(cookies_str, web_protect_str, keys_str)

print("✅ 认证初始化成功！")
print()

# 手动调用 get_device_id 的 API 并打印完整响应
api = '/passport/tw_c/618a8a0ac4009b1f9/device_id/'
url = f'{DouyinAPI.douyin_url}{api}'

# 使用简单 headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Referer': f'{DouyinAPI.douyin_url}/',
    'Origin': DouyinAPI.douyin_url,
}

params = Params()
params.with_platform()
params.add_param('verifyFp', auth.cookie['s_v_web_id'])
params.add_param('fp', auth.cookie['s_v_web_id'])

print("请求 URL:", url)
print("请求参数:", params.get())
print()

try:
    resp = requests.get(url, params=params.get(), verify=False, headers=headers, cookies=auth.cookie)
    print("响应状态码:", resp.status_code)
    print("响应内容:", resp.text[:1000] if len(resp.text) > 1000 else resp.text)
    print()
    
    try:
        resp_json = json.loads(resp.text)
        print("JSON 解析成功!")
        print("响应 JSON:")
        print(json.dumps(resp_json, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"JSON 解析失败: {e}")
        
except Exception as e:
    print(f"请求失败: {e}")
    import traceback
    traceback.print_exc()