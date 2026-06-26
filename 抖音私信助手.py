import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入系统
from dotenv import load_dotenv
load_dotenv('.env')
load_dotenv('config_ai.env')

from ai_auto_reply import AutoReplySystem, Message
import hashlib
from builder.params import Params
from builder.header import HeaderBuilder
import websocket
from websocket import WebSocketApp
from static import Live_pb2, Response_pb2
from builder.auth import DouyinAuth
import json

class DouyinGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("抖音私信自动回复系统 v2.0")
        self.root.geometry("800x600")
        
        # 初始化
        self.setup_ui()
        self.system = None
        self.ws = None
        self.running = False
        
    def setup_ui(self):
        # 标题
        title = tk.Label(self.root, text="抖音私信AI自动回复系统", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        # 日志区域
        self.log_area = scrolledtext.ScrolledText(self.root, width=90, height=30, font=("Consolas", 10))
        self.log_area.pack(pady=10)
        
        # 按钮框架
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # 按钮
        tk.Button(btn_frame, text="启动系统", command=self.start_system, width=15, height=2, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="停止系统", command=self.stop_system, width=15, height=2, bg="red", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="清空日志", command=self.clear_log, width=15, height=2).pack(side=tk.LEFT, padx=5)
        
        self.log("系统就绪")
        
    def log(self, msg):
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        
    def clear_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log("日志已清空")
        
    def start_system(self):
        if self.running:
            self.log("系统已在运行中")
            return
            
        self.log("正在启动...")
        threading.Thread(target=self.run_system, daemon=True).start()
        
    def stop_system(self):
        self.log("正在停止...")
        self.running = False
        if self.ws:
            self.ws.close()
        self.log("系统已停止")
        
    def run_system(self):
        try:
            from builder.auth import DouyinAuth
            from dy_apis.douyin_api import DouyinAPI
            
            # 加载配置
            cookies_str = os.getenv('DY_COOKIES_MS', '') or os.getenv('DY_COOKIES', '')
            web_protect_str = os.getenv('WEB_PROTECT', '')
            keys_str = os.getenv('KEYS', '')
            
            # 初始化认证
            auth = DouyinAuth()
            auth.perepare_auth(cookies_str, web_protect_str, keys_str)
            self.auth = auth  # 保存auth用于发送消息
            self.log("认证成功")
            
            # 获取device_id
            try:
                device_id = DouyinAPI.get_device_id(auth=auth)
                self.log(f"device_id: {device_id}")
            except:
                device_id = auth.cookie.get('a11y_device_id') or '7631877838707'
                self.log(f"使用备用device_id: {device_id}")
            
            # 初始化AI
            from ai_auto_reply import AutoReplySystem, Message
            self.system = AutoReplySystem('config_ai.env')
            self.log("AI系统就绪")
            
            # 构建WebSocket URL
            fpId = '9'
            appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
            accessKey = f'{fpId + appKey + device_id}f8a69f1719916z'
            accessKey = hashlib.md5(accessKey.encode()).hexdigest()
            
            params = Params()
            params.add_param("aid", "6383")
            params.add_param("device_platform", "douyin_pc")
            params.add_param("fpid", fpId)
            params.add_param("device_id", device_id)
            params.add_param("token", auth.cookie["sessionid"])
            params.add_param("access_key", accessKey)
            
            self.ws_url = f"wss://frontier-im.douyin.com/ws/v2?{params.toString()}"
            
            # 启动WebSocket
            self.running = True
            self.log("WebSocket连接中...")
            
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
                cookie=auth.cookie_str,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            self.ws.run_forever(origin='https://www.douyin.com')
            
        except Exception as e:
            self.log(f"错误: {e}")
            import traceback
            traceback.print_exc()
            
    def on_message(self, ws, message):
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
                
                try:
                    content = json.loads(content)
                except:
                    content = {}
                
                if msg_type == 7:
                    text = content.get("text", "")
                    if text:
                        self.log(f"收到: {sender}: {text}")
                        threading.Thread(target=self.reply_async, args=(text, str(conversation_id), sender), daemon=True).start()
                        
        except Exception as e:
            self.log(f"消息处理错误: {e}")
    
    def reply_async(self, text, conversation_id, sender):
        try:
            # 延迟
            import random
            delay = random.uniform(8, 20)
            self.log(f"延迟 {delay:.1f}秒...")
            time.sleep(delay)
            
            # AI回复
            message = Message(sender=str(sender), content=text, conversation_id=conversation_id)
            reply = self.system.process_message(message)
            
            if reply:
                self.log(f"AI回复: {reply}")
                self.send_reply(conversation_id, sender, reply)
                
        except Exception as e:
            self.log(f"回复错误: {e}")
    
    def send_reply(self, conversation_id, sender, reply_text):
        try:
            from dy_apis.douyin_api import DouyinAPI
            
            conversation_short_id = 0
            ticket = ""
            
            DouyinAPI.send_msg(
                self.auth,
                conversation_id,
                conversation_short_id,
                ticket,
                reply_text
            )
            self.log(f"✅ 发送成功")
            
        except Exception as e:
            self.log(f"❌ 发送失败: {e}")
    
    def on_error(self, ws, error):
        self.log(f"WebSocket错误: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        self.log("连接已断开")

    def on_open(self, ws):
        self.log("WebSocket连接成功")

if __name__ == '__main__':
    app = DouyinGUI()
    app.root.mainloop()