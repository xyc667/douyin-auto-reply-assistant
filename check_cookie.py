#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

load_dotenv()

cookies_str = os.getenv('DY_COOKIES', '')

print("=" * 60)
print("📋 检查 Cookie...")
print("=" * 60)

if not cookies_str:
    print("❌ Cookie 为空！请在 .env 文件中配置 DY_COOKIES")
else:
    print(f"Cookie 长度: {len(cookies_str)}")
    
    # 检查必要的字段
    fields_to_check = [
        'sessionid',
        's_v_web_id',
        'passport_csrf_token',
        'msToken',
        'odin_tt',
        'ttwid'
    ]
    
    print("\n检查 Cookie 包含的字段:")
    found_fields = {}
    for item in cookies_str.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            found_fields[key] = value
            # 显示前30个字符，太长则截断
            display_value = value[:30]
            if len(value) > 30:
                display_value += '...'
            print("  ✅ " + key + ": " + display_value)
    
    print("\n必要字段检查:")
    for field in fields_to_check:
        if field in found_fields:
            print(f"  ✅ {field}: 存在")
        else:
            print(f"  ❌ {field}: 缺失")
    
    print("\n" + "=" * 60)
    if 'sessionid' in found_fields and 's_v_web_id' in found_fields:
        print("✅ Cookie 看起来是完整的！")
        print("可以尝试运行: python dy_apis/douyin_recv_msg.py")
    else:
        print("❌ Cookie 不完整！")
        print("请重新获取完整的 Cookie！")
        print("\n获取方法:")
        print("  1. 打开 https://www.douyin.com")
        print("  2. 按 F12 打开开发者工具")
        print("  3. 刷新页面")
        print("  4. 在 Network 中找到任意请求")
        print("  5. 复制完整的 Cookie 值")
        print("  6. 配置到 .env 文件中")
    print("=" * 60)

print()
