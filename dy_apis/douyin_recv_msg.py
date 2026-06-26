import hashlib
import json
import os
import sys
import pathlib
import threading
import time

# 添加项目根目录到路径
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import websocket
from websocket import WebSocketApp

from dy_apis.douyin_api import DouyinAPI
from builder.auth import DouyinAuth
from builder.header import HeaderBuilder
from builder.params import Params
from static import Live_pb2, Response_pb2

# 加载知识库
def load_knowledge_base():
    """加载知识库"""
    try:
        with open('datas/knowledge_base.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('knowledge_base', [])
    except:
        return []

def find_knowledge_reply(knowledge_base, user_message):
    """在知识库中查找回复"""
    user_message = user_message.lower().strip()
    for item in knowledge_base:
        question = item.get('question', '').lower().strip()
        if question in user_message or user_message in question:
            return item.get('answer', '')
    return None

class DouyinRecvMsg:
    appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
    fpId = '9'

    def __init__(self, auth: DouyinAuth, auto_reconnect=True):
        self.auto_reconnect = auto_reconnect
        self.auth = auth
        self.ws = None
        self.knowledge_base = load_knowledge_base()
        self.conversation_id = None
        self.conversation_short_id = None
        self.ticket = None
        self.sender = None
        print(f"✅ 知识库已加载，共 {len(self.knowledge_base)} 条")

        # 获取 device_id
        self._get_device_id()
        
        # 构建 WebSocket URL
        fpId = '9'
        appKey = "e1bd35ec9db7b8d846de66ed140b1ad9"
        accessKey = f'{fpId + appKey + self.device_id}f8a69f1719916z'
        accessKey = hashlib.md5(accessKey.encode(encoding='UTF-8')).hexdigest()
        
        params = Params()
        params.add_param("aid", "6383")
        params.add_param("device_platform", "douyin_pc")
        params.add_param("fpid", fpId)
        params.add_param("device_id", self.device_id)
        params.add_param("token", self.auth.cookie["sessionid"])
        params.add_param("access_key", accessKey)
        
        self.url = f"wss://frontier-im.douyin.com/ws/v2?{params.toString()}"

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

    def on_open(self, ws):
        print("WebSocket connection open.")

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
                        print(f'\n💬 收到私信！来自: {sender}')
                        print(f'📝 内容: {text}')
                        
                        # 自动知识库回复
                        knowledge_reply = find_knowledge_reply(self.knowledge_base, text)
                        if knowledge_reply:
                            print(f'✅ 知识库匹配: {knowledge_reply}')
                            time.sleep(random.uniform(8, 20))  # 延迟
                            self.send_reply(conversation_id, sender, knowledge_reply)
                        else:
                            print(f'⚠️ 知识库无匹配')

            elif frame.payloadType == 'text/json':
                pass
        except Exception as e:
            print(f"⚠️ 消息处理错误: {e}")

    def send_reply(self, conversation_id, sender, reply_text):
        """发送回复"""
        try:
            conv_short_id = 0
            ticket = ""
            
            DouyinAPI.send_msg(
                self.auth,
                str(conversation_id),
                conv_short_id,
                ticket,
                reply_text
            )
            print(f"✅ 回复发送成功: {reply_text}")
            
        except Exception as e:
            print(f"❌ 发送失败: {e}")

    def on_error(self, ws, error):
        print(f"\033[31m### error: {error}\033[m")
        if type(error) == websocket._exceptions.WebSocketConnectionClosedException and self.auto_reconnect:
            self.start()

    def on_close(self, ws, close_status_code, close_msg):
        print(f"\033[31m### closed: {close_status_code}, {close_msg}\033[m")

    def start(self):
        self.ws = WebSocketApp(
            url=self.url,
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
        try:
            self.ws.run_forever(origin='https://www.douyin.com')
        except KeyboardInterrupt:
            self.ws.close()
        except:
            self.ws.close()

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    cookies_str = os.getenv('DY_COOKIES', '')
    web_protect_str = os.getenv('WEB_PROTECT', '')
    keys_str = os.getenv('KEYS', '')

    auth_ = DouyinAuth()
    auth_.perepare_auth(cookies_str, web_protect_str, keys_str)
    douyinMsg = DouyinRecvMsg(auth_)

    ws_thread = threading.Thread(target=douyinMsg.start)
    ws_thread.daemon = True
    ws_thread.start()

    print("=" * 50)
    print("✅ 抖音私信接收服务已启动！")
    print("📝 等待接收私信...")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        douyinMsg.ws.close()
        print("服务已停止")