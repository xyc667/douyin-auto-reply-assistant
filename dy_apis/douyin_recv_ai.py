#!/usr/bin/env python3
"""
抖音私信AI自动回复系统
集成私信接收 + AI智能回复 + 自动发送
"""

import os
import sys
import json
import time
import random
import traceback
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入组件
from dotenv import load_dotenv

# 导入AI回复系统
from ai_auto_reply import AutoReplySystem, Message

# 导入私信接收系统
import hashlib
from builder.params import Params
from builder.header import HeaderBuilder
import websocket
from websocket import WebSocketApp
from static import Live_pb2, Response_pb2

class DouyinAISystem:
    """抖音AI自动回复系统"""
    
    def __init__(self):
        # 加载两个配置文件
        load_dotenv('.env')
        load_dotenv('config_ai.env')
        
        # 初始化AI系统
        print("=" * 70)
        print("🚀 初始化抖音AI自动回复系统")
        print("=" * 70)
        
        self.ai_system = AutoReplySystem('config_ai.env')
        
        # 初始化抖音认证
        self._init_douyin_auth()
        
        # 初始化WebSocket
        self._init_websocket()
        
        print("\n✅ 系统初始化完成！")
        print("=" * 70)
    
    def _init_douyin_auth(self):
        """初始化抖音认证"""
        # 优先使用私信专用 Cookie
        cookies_str = os.getenv('DY_COOKIES_MS', '') or os.getenv('DY_COOKIES', '')
        web_protect_str = os.getenv('WEB_PROTECT', '')
        keys_str = os.getenv('KEYS', '')
        
        from builder.auth import DouyinAuth
        self.auth = DouyinAuth()
        self.auth.perepare_auth(cookies_str, web_protect_str, keys_str)
        
        # 获取 device_id
        self._get_device_id()
    
    def _get_device_id(self):
        """获取或生成device_id"""
        try:
            from dy_apis.douyin_api import DouyinAPI
            self.device_id = DouyinAPI.get_device_id(auth=self.auth)
            print(f"✅ 使用真实 device_id: {self.device_id}")
        except:
            # 使用备用方案
            self.device_id = self.auth.cookie.get('a11y_device_id') or '7631877838707'
            print(f"⚠️ 使用备用 device_id: {self.device_id}")
    
    def _init_websocket(self):
        """初始化WebSocket连接"""
        # 生成 access_key
        fpId = '9'
        appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
        accessKey = f'{fpId + appKey + self.device_id}f8a69f1719916z'
        accessKey = hashlib.md5(accessKey.encode(encoding='UTF-8')).hexdigest()
        
        # 构建 WebSocket URL
        params = Params()
        params.add_param("aid", "6383")
        params.add_param("device_platform", "douyin_pc")
        params.add_param("fpid", fpId)
        params.add_param("device_id", self.device_id)
        params.add_param("token", self.auth.cookie["sessionid"])
        params.add_param("access_key", accessKey)
        
        self.ws_url = f"wss://frontier-im.douyin.com/ws/v2?{params.toString()}"
        self.ws = None
    
    def on_message(self, ws, message):
        """处理收到的消息"""
        try:
            frame = Live_pb2.PushFrame()
            frame.ParseFromString(message)
            
            if frame.payloadType == 'pb':
                response = Response_pb2.Response()
                response.ParseFromString(frame.payload)
                
                notify = response.body.new_message_notify
                if not notify:
                    return
                
                msg = notify.message
                if not msg:
                    return
                
                sender = msg.sender
                content = msg.content
                msg_type = msg.message_type
                conversation_id = msg.conversation_id
                
                # 解析消息内容
                try:
                    content = json.loads(content)
                except:
                    content = {}
                
                # 只处理文本消息
                if msg_type == 7:
                    text = content.get("text", "")
                    if text:
                        print(f"\n💬 收到私信 from {sender}: {text}")
                        
                        # 创建消息对象
                        message = Message(
                            sender=str(sender),
                            content=text,
                            conversation_id=str(conversation_id)
                        )
                        
                        # 调用AI处理（异步）
                        threading.Thread(
                            target=self._process_and_reply,
                            args=(message,),
                            daemon=True
                        ).start()
                        
        except Exception as e:
            print(f"⚠️ 消息处理错误: {e}")
    
    def _process_and_reply(self, message: Message):
        """处理消息并回复"""
        try:
            # 获取AI回复
            reply = self.ai_system.process_message(message)
            
            if reply:
                print(f"\n🤖 AI回复: {reply}")
                
                # 随机延迟模拟人工
                delay = random.uniform(
                    self.ai_system.min_delay,
                    self.ai_system.max_delay
                )
                print(f"⏱️  延迟 {delay:.1f} 秒后发送...")
                time.sleep(delay)
                
                # 发送回复
                self._send_reply(message, reply)
            else:
                print(f"\n⏭️  跳过回复（可能在黑名单或已禁用）")
                
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            traceback.print_exc()
    
    def _send_reply(self, message: Message, reply_text: str):
        """发送回复"""
        try:
            from dy_apis.douyin_api import DouyinAPI
            
            # 获取对话信息
            conversation_id = message.conversation_id
            conversation_short_id = 0
            ticket = ""
            
            # 提取 short_id（从 conversation_id 格式：0:1:uid:xxx）
            parts = conversation_id.split(':')
            if len(parts) >= 4:
                try:
                    conversation_short_id = int(parts[3])
                except:
                    conversation_short_id = 0
            
            # 发送消息
            DouyinAPI.send_msg(
                self.auth,
                conversation_id,
                conversation_short_id,
                ticket,
                reply_text
            )
            
            print(f"✅ 回复发送成功！")
            self.ai_system.logger.log("INFO", "回复发送成功", 
                                   user_id=message.sender,
                                   content=reply_text)
            
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            self.ai_system.logger.log("ERROR", "回复发送失败",
                                     user_id=message.sender,
                                     content=reply_text,
                                     error=str(e))
    
    def on_error(self, ws, error):
        """错误处理"""
        print(f"\n❌ WebSocket错误: {error}")
        if type(error) == websocket._exceptions.WebSocketConnectionClosedException:
            print("🔄 连接断开，尝试重连...")
    
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        print(f"\n⚠️ WebSocket连接关闭: {close_status_code} - {close_msg}")
    
    def on_open(self, ws):
        """连接打开"""
        print("\n✅ WebSocket连接已建立！")
        print("📡 开始监听私信...")
    
    def start(self):
        """启动系统"""
        print("\n" + "=" * 70)
        print("🎯 启动抖音AI自动回复系统")
        print("=" * 70)
        print("按 Ctrl+C 停止系统")
        print("=" * 70)
        
        # 创建 WebSocket 应用
        self.ws = WebSocketApp(
            url=self.ws_url,
            header={
                'Pragma': 'no-cache',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'User-Agent': HeaderBuilder.ua,
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
        
        # 运行
        try:
            self.ws.run_forever(origin='https://www.douyin.com')
        except KeyboardInterrupt:
            print("\n\n👋 正在停止系统...")
            self.ws.close()
            print("✅ 系统已停止")
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")

def main():
    """主函数"""
    try:
        # 创建并启动系统
        system = DouyinAISystem()
        system.start()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        traceback.print_exc()
        input("按 Enter 键退出...")

if __name__ == '__main__':
    main()