#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单版本的抖音私信接收程序
先测试能否正常连接和接收消息
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


class SimpleRecvMsg:
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
        print("等待接收私信...")

    def on_message(self, ws, message):
        print("\n" + "="*60)
        print("📨 收到新消息!")
        
        try:
            frame = Live_pb2.PushFrame()
            frame.ParseFromString(message)
            
            print(f"payloadType: {frame.payloadType}")
            
            # 打印完整的 frame 信息用于调试
            print("\n🔍 完整 Frame:")
            print(str(frame)[:800])
            
            # 检查是否有其他字段
            print(f"\nframe.payload: {type(frame.payload)}, length: {len(frame.payload) if frame.payload else 0}")
            
            # 尝试直接解析原始消息不通过 protobuf
            if frame.payload:
                print(f"\npayload 原始数据 (前200): {frame.payload[:200]}")
            
            if frame.payloadType == 'text/json':
                # 处理 JSON 类型的消息
                print("\n📄 JSON 消息内容:")
                try:
                    # frame.payload 可能是 bytes 或 string
                    payload = frame.payload
                    if isinstance(payload, bytes):
                        payload = payload.decode('utf-8')
                    
                    if payload:
                        # 格式化打印 JSON
                        import json
                        json_data = json.loads(payload)
                        print(json.dumps(json_data, ensure_ascii=False, indent=2))
                    else:
                        print("(payload 为空)")
                except Exception as e:
                    print(f"解析 JSON 失败: {e}")
                    print(f"原始内容: {frame.payload}")
                    
            elif frame.payloadType == 'pb':
                try:
                    response = Response_pb2.Response()
                    response.ParseFromString(frame.payload)
                    
                    # 打印原始数据用于调试
                    print("\n原始消息:")
                    print(str(response)[:500])
                    
                    # 尝试提取消息内容
                    try:
                        notify = response.body.new_message_notify
                        if notify and notify.message:
                            msg = notify.message
                            print(f"\n发件人: {msg.sender}")
                            print(f"消息类型: {msg.message_type}")
                            print(f"内容: {msg.content}")
                    except Exception as e:
                        print(f"解析消息内容失败: {e}")
                except Exception as e:
                    print(f"解析 protobuf 失败: {e}")
            else:
                print(f"\n未知的 payloadType: {frame.payloadType}")
                if frame.payload:
                    print(f"payload: {frame.payload[:100]}")
                    
        except Exception as e:
            print(f"处理消息出错: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*60)

    def on_error(self, ws, error):
        print(f"\n❌ Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"\n🔌 连接关闭, code: {close_status_code}, msg: {close_msg}")

    def start(self):
        print(f"正在连接: {self.url[:100]}...")
        self.ws = WebSocketApp(
            url=self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever(origin='https://www.douyin.com')


if __name__ == '__main__':
    print("="*60)
    print("💬 抖音私信接收 - 简化版")
    print("="*60)
    
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
    recv = SimpleRecvMsg(auth_)
    try:
        recv.start()
    except KeyboardInterrupt:
        print("\n👋 退出程序")

