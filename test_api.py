#!/usr/bin/env python3
"""
测试 MiniMax API 连接
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('config_ai.env')

# MiniMax API配置
api_key = os.getenv('ANTHROPIC_API_KEY', '')
base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://api.minimaxi.com/anthropic')
model = os.getenv('AI_MODEL', 'abab6.5s-chat')

print("=" * 60)
print("🧪 测试 MiniMax API 连接")
print("=" * 60)
print(f"API地址: {base_url}")
print(f"模型: {model}")
print(f"API Key: {api_key[:20]}...")
print()

if not api_key or api_key == '你的API_Key':
    print("❌ API Key未配置！")
    print("请编辑 config_ai.env 设置 ANTHROPIC_API_KEY")
    exit(1)

# 测试不同的API格式
print("尝试不同的API格式...")
print()

# 格式1: MiniMax标准格式
url1 = f"{base_url}/v1/messages"
headers1 = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_key}'
}

data1 = {
    'model': model,
    'messages': [
        {'role': 'user', 'content': '你好'}
    ],
    'max_tokens': 100
}

print("📤 尝试格式1: /v1/messages")
try:
    response = requests.post(url1, headers=headers1, json=data1, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    print()
    
    if response.status_code == 200:
        print("✅ 格式1 成功！")
        result = response.json()
        if 'choices' in result:
            reply = result['choices'][0]['message']['content']
            print(f"回复: {reply}")
        elif 'text' in result:
            print(f"回复: {result['text']}")
        else:
            print(f"完整响应: {json.dumps(result, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 格式1 失败: {e}")
print()

# 格式2: OpenAI兼容格式
url2 = f"{base_url}/chat/completions"
data2 = {
    'model': model,
    'messages': [
        {'role': 'user', 'content': '你好'}
    ],
    'max_tokens': 100
}

print("📤 尝试格式2: /chat/completions")
try:
    response = requests.post(url2, headers=headers1, json=data2, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:500]}")
    print()
    
    if response.status_code == 200:
        print("✅ 格式2 成功！")
except Exception as e:
    print(f"❌ 格式2 失败: {e}")

print()
print("=" * 60)
print("💡 根据返回结果，我来判断使用哪种格式")
print("=" * 60)