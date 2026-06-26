#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试版本 - 打印完整的原始消息
"""

import os
import sys
import json
import threading
import pathlib

# 添加项目根目录到路径
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import websocket
from websocket import WebSocketApp
from dotenv import load_dotenv

# 导入项目模块
from builder.auth import DouyinAuth
from builder.params import Params
from dy_apis.douyin_api import DouyinAPI
from static import Live_pb2, Response_pb2


class DebugRecvMsg:
    def __init__(self, auth: DouyinAuth):
        self.auth = auth
        self.ws = None
        appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
        fpId = '9'
        
        deviceId = DouyinAPI.get_device_id(auth=self.auth)
        accessKey = f'{fpId + appKey + deviceId}f8a69f1719916z'
        import hashlib
        accessKey = hashlib.md5(accessKey.encode(encoding='UTF-8')).hexdigest()
        
        params = Params()
        (params
         .add_param("aid", "6383")
         .add_param("device_platform", "douyin_pc")
         .add_param("fpid", fpId)
         .add_param("device_id", deviceId)
         .add_param("token", self.auth.cookie["sessionid"])
         .add_param("access_key", accessKey)
         )
        self.url = f"wss://frontier-im.douyin.com/ws/v2?{params.toString()}"

    def on_open(self, ws):
        print("✅ WebSocket 连接成功！")
        print("等待接收私信...\n")

    def on_message(self, ws, message):
        print("\n" + "="*80)
        print("📨 收到新消息!")
        print("="*80)
        
        try:
            frame = Live_pb2.PushFrame()
            frame.ParseFromString(message)
            
            print(f"[1] payloadType: {frame.payloadType}")
            
            # 打印完整的 frame
            print(f"\n[2] 完整 Frame 信息:")
            print(str(frame)[:1000])
            
            # 打印 payload 信息
            print(f"\n[3] payload 信息:")
            print(f"    类型: {type(frame.payload)}")
            print(f"    长度: {len(frame.payload) if frame.payload else 0}")
            if frame.payload:
                print(f"    前100字符: {str(frame.payload)[:100]}")
            
            if frame.payloadType == 'pb' and frame.payload:
                print(f"\n[4] 尝试解析 protobuf payload:")
                try:
                    response = Response_pb2.Response()
                    response.ParseFromString(frame.payload)
                    print(f"    解析成功！")
                    print(f"    完整 Response: {str(response)[:1500]}")
                except Exception as e:
                    print(f"    解析失败: {e}")
                    import traceback
                    traceback.print_exc()
            
        except Exception as e:
            print(f"\n[ERROR] 处理消息出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*80 + "\n")

    def on_error(self, ws, error):
        print(f"\n❌ Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"\n🔌 连接关闭, code: {close_status_code}, msg: {close_msg}")

    def start(self):
        print(f"正在连接: {self.url[:100]}...")
        self.ws = WebSocketApp(
            url=self.url,
            header={
                'Pragma': 'no-cache',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
                'Cache-Control': 'no-cache',
                'Sec-WebSocket-Protocol': 'binary, base64, pbbp2',
                'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits'
            },
            cookie=self.auth.cookie_str,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever(origin='https://www.douyin.com')


if __name__ == '__main__':
    print("="*80)
    print("🔍 抖音私信接收 - 调试版本")
    print("="*80)
    
    # 加载 Cookie
    load_dotenv()
    cookies_str = os.getenv('DY_COOKIES', '')
    
    if not cookies_str:
        print("❌ 没有找到 Cookie！请在 .env 文件中配置 DY_COOKIES")
        sys.exit(1)
    
    # 检查是否有 sessionid
    if 'sessionid' not in cookies_str:
        print("❌ Cookie 中没有找到 sessionid！")
        print("请重新获取完整的 Cookie！")
        sys.exit(1)
    
    # 准备 auth
    print("正在初始化...")
    web_protect_str = ''
    keys_str = ''
    
    auth_ = DouyinAuth()
    auth_.perepare_auth(cookies_str, web_protect_str, keys_str)
    
    print("✅ Cookie 验证成功！")
    print("正在启动 WebSocket 连接...\n")
    
    # 启动
    recv = DebugRecvMsg(auth_)
    try:
        recv.start()
    except KeyboardInterrupt:
        print("\n👋 退出程序")

