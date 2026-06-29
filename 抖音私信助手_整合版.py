import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
import os
import sys
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR / 'config_ai.env')

from ai_auto_reply import AutoReplySystem, Message
import hashlib
from builder.params import Params
from builder.header import HeaderBuilder
import websocket
from websocket import WebSocketApp
from static import Live_pb2, Response_pb2
from builder.auth import DouyinAuth
from account_manager import AccountManager, safe_print
from account_gui import AccountManagerWindow


class KnowledgeBaseManager:
    def __init__(self, parent):
        self.parent = parent
        self.kb_path = BASE_DIR / 'datas' / 'knowledge_base.json'
        self.knowledge_base = []
        self._metadata = {}
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        self.knowledge_base = []
        self._metadata = {}
        if not self.kb_path.exists():
            return
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                self.knowledge_base = data
            elif isinstance(data, dict):
                self.knowledge_base = data.get('knowledge_base', [])
                self._metadata = {k: v for k, v in data.items() if k != 'knowledge_base'}
        except Exception as e:
            safe_print(f"加载知识库失败: {e}")
            
    def save_knowledge_base(self):
        try:
            if not self.kb_path.parent.exists():
                self.kb_path.parent.mkdir(parents=True)
            payload = dict(self._metadata)
            payload['knowledge_base'] = self.knowledge_base
            if 'version' not in payload:
                payload['version'] = '2.0'
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            if hasattr(self.parent, 'system') and self.parent.system:
                self.parent.system.knowledge_base.load()
            return True
        except Exception as e:
            safe_print(f"保存知识库失败: {e}")
            return False
            
    def add_entry(self, question, answer):
        entry = {
            "question": question,
            "answer": answer
        }
        self.knowledge_base.append(entry)
        return self.save_knowledge_base()
        
    def update_entry(self, index, question, answer):
        if 0 <= index < len(self.knowledge_base):
            self.knowledge_base[index] = {
                "question": question,
                "answer": answer
            }
            return self.save_knowledge_base()
        return False
        
    def delete_entry(self, index):
        if 0 <= index < len(self.knowledge_base):
            del self.knowledge_base[index]
            return self.save_knowledge_base()
        return False
        
    def get_entry(self, index):
        if 0 <= index < len(self.knowledge_base):
            return self.knowledge_base[index]
        return None
    
    def match_knowledge(self, text):
        text = text.strip()
        for entry in self.knowledge_base:
            if not isinstance(entry, dict):
                continue
            question = entry.get('question', '').strip()
            if question and (question in text or text in question):
                return entry.get('answer', '')
        return None


class KnowledgeBaseWindow:
    def __init__(self, parent, kb_manager):
        self.parent = parent
        self.kb_manager = kb_manager
        
        self.window = tk.Toplevel(parent.root)
        self.window.title("知识库管理")
        self.window.geometry("800x600")
        self.window.transient(parent.root)
        self.window.grab_set()
        
        self.setup_ui()
        self.refresh_list()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.listbox = tk.Listbox(list_frame, width=50, height=15)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(content_frame, text="问题:").pack(anchor=tk.W)
        self.question_text = scrolledtext.ScrolledText(content_frame, height=3, width=80)
        self.question_text.pack(fill=tk.X, pady=2)
        
        ttk.Label(content_frame, text="回答:").pack(anchor=tk.W)
        self.answer_text = scrolledtext.ScrolledText(content_frame, height=8, width=80)
        self.answer_text.pack(fill=tk.X, pady=2)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="添加", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="修改", command=self.update_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="刷新", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.selected_index = -1
        
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, entry in enumerate(self.kb_manager.knowledge_base):
            question = entry.get('question', '')[:30] + '...' if len(entry.get('question', '')) > 30 else entry.get('question', '')
            self.listbox.insert(tk.END, f"{i+1}. {question}")
        self.clear_fields()
        
    def clear_fields(self):
        self.question_text.delete(1.0, tk.END)
        self.answer_text.delete(1.0, tk.END)
        self.selected_index = -1
        
    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            self.selected_index = selection[0]
            entry = self.kb_manager.get_entry(self.selected_index)
            if entry:
                self.question_text.delete(1.0, tk.END)
                self.question_text.insert(tk.END, entry.get('question', ''))
                self.answer_text.delete(1.0, tk.END)
                self.answer_text.insert(tk.END, entry.get('answer', ''))
                
    def add_entry(self):
        question = self.question_text.get(1.0, tk.END).strip()
        answer = self.answer_text.get(1.0, tk.END).strip()
        
        if not question or not answer:
            messagebox.showwarning("提示", "请输入问题和回答")
            return
            
        if self.kb_manager.add_entry(question, answer):
            messagebox.showinfo("成功", "添加成功")
            self.refresh_list()
            self.clear_fields()
        else:
            messagebox.showerror("失败", "添加失败")
            
    def update_entry(self):
        if self.selected_index == -1:
            messagebox.showwarning("提示", "请先选择要修改的条目")
            return
            
        question = self.question_text.get(1.0, tk.END).strip()
        answer = self.answer_text.get(1.0, tk.END).strip()
        
        if not question or not answer:
            messagebox.showwarning("提示", "请输入问题和回答")
            return
            
        if self.kb_manager.update_entry(self.selected_index, question, answer):
            messagebox.showinfo("成功", "修改成功")
            self.refresh_list()
            self.clear_fields()
        else:
            messagebox.showerror("失败", "修改失败")
            
    def delete_entry(self):
        if self.selected_index == -1:
            messagebox.showwarning("提示", "请先选择要删除的条目")
            return
            
        if messagebox.askyesno("确认", "确定要删除这个条目吗？"):
            if self.kb_manager.delete_entry(self.selected_index):
                messagebox.showinfo("成功", "删除成功")
                self.refresh_list()
                self.clear_fields()
            else:
                messagebox.showerror("失败", "删除失败")


class DouyinGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("抖音私信自动回复系统 v2.3 (整合版)")
        self.root.geometry("900x650")
        
        self.system = None
        self.ws = None
        self.running = False
        self.auth = None
        self.my_uid = None
        self.kb_manager = KnowledgeBaseManager(self)
        self.account_manager = AccountManager()
        
        self.setup_ui()
        self.check_existing_cookie()
        
    def check_existing_cookie(self):
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path, override=True)
        cookies_str = os.getenv('DY_COOKIES', '')
        if cookies_str and len(cookies_str) > 100:
            self.status_label.config(text="✅ 已登录", fg="green")
            self.log(f"✅ 检测到已有Cookie，长度: {len(cookies_str)} 字符")
            self.log("✅ 状态已更新为已登录")
        else:
            self.status_label.config(text="⚠️ 未登录", fg="orange")
            self.log("⚠️ 未检测到有效Cookie")
        
    def setup_ui(self):
        title = tk.Label(self.root, text="🎵 抖音私信AI自动回复系统", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        self.status_label = tk.Label(self.root, text="⚠️ 未登录", font=("Arial", 12), fg="orange")
        self.status_label.pack(pady=5)
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🔑 自动登录", command=self.auto_login, width=15, height=2, bg="blue", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 刷新配置", command=self.refresh_config, width=15, height=2, bg="orange", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="▶️ 启动系统", command=self.start_system, width=15, height=2, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="⏹️ 停止系统", command=self.stop_system, width=15, height=2, bg="red", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📚 知识库", command=self.open_knowledge_base, width=15, height=2, bg="purple", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ 清空日志", command=self.clear_log, width=15, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="👤 账号管理", command=self.open_account_manager, width=15, height=2, bg="teal", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.log_area = scrolledtext.ScrolledText(self.root, width=100, height=32, font=("Consolas", 10))
        self.log_area.pack(pady=10, padx=10)
        
        self.log("=" * 60)
        self.log("📌 使用说明:")
        self.log("  1. 点击【账号管理】添加或切换抖音账号")
        self.log("  2. 选择账号后点击【重新登录】获取Cookie")
        self.log("  3. 等待浏览器窗口弹出，扫码登录")
        self.log("  4. 登录成功后点击【启动系统】开始接收私信")
        self.log("  5. 收到私信会自动根据知识库回复")
        self.log("  6. 点击【知识库】按钮管理回复内容")
        self.log("  7. 点击【停止系统】结束服务")
        self.log("=" * 60)
        self.log(f"📚 知识库已加载，共 {len(self.kb_manager.knowledge_base)} 条")
        
        current_acc = self.account_manager.get_current_account()
        if current_acc:
            self.log(f"👤 当前账号: {current_acc.name} ({current_acc.nickname or '未设置'})")
        self.log("系统就绪，等待操作...")
        
    def open_knowledge_base(self):
        KnowledgeBaseWindow(self, self.kb_manager)
        
    def open_account_manager(self):
        AccountManagerWindow(self, self.account_manager)
        
    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}\n"

        def append():
            self.log_area.insert(tk.END, line)
            self.log_area.see(tk.END)

        try:
            self.root.after(0, append)
        except tk.TclError:
            safe_print(msg)

    def ui_call(self, callback):
        try:
            self.root.after(0, callback)
        except tk.TclError:
            pass
        
    def clear_log(self):
        self.log_area.delete(1.0, tk.END)
        self.log("日志已清空")
    
    def refresh_config(self):
        self.log("🔄 正在刷新配置...")
        
        if self.running:
            if messagebox.askyesno("确认", "系统正在运行，刷新配置需要重启系统，确定继续吗？"):
                self.stop_system()
                time.sleep(1)
            else:
                self.log("⚠️ 用户取消刷新")
                return
        
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path, override=True)
        cookies_str = os.getenv('DY_COOKIES', '')
        
        if cookies_str and len(cookies_str) > 100:
            self.status_label.config(text="✅ 已登录", fg="green")
            self.log(f"✅ 配置刷新成功，Cookie长度: {len(cookies_str)} 字符")
            messagebox.showinfo("成功", "配置刷新成功！")
        else:
            self.status_label.config(text="⚠️ 未登录", fg="orange")
            self.log("⚠️ 未检测到有效Cookie")
            messagebox.showwarning("提示", "未检测到有效Cookie，请先登录")
        
        self.kb_manager.load_knowledge_base()
        self.log(f"📚 知识库已重新加载，共 {len(self.kb_manager.knowledge_base)} 条")

        if not self.running:
            try:
                self.system = AutoReplySystem(str(BASE_DIR / 'config_ai.env'))
                self.log("✅ AI/回复配置已重新加载")
                if self.system.ai_fallback and self.system.ai_config.api_key:
                    if self.system.test_ai_connection():
                        self.log("✅ AI 接口可用")
                    else:
                        self.log("⚠️ AI 接口不可用，请更新 API Key")
            except Exception as e:
                self.system = None
                self.log(f"⚠️ AI系统重新加载失败: {e}")
        
        self.account_manager.load_accounts()
        current_acc = self.account_manager.get_current_account()
        if current_acc:
            self.log(f"👤 当前账号: {current_acc.name}")
        
    def auto_login(self):
        if self.running:
            messagebox.showwarning("提示", "请先停止系统后再重新登录")
            return
            
        self.log("=" * 60)
        self.log("🔑 开始自动登录...")
        self.log("📱 正在启动浏览器，请稍候...")
        self.log("⚠️ 浏览器窗口将在几秒后弹出，请扫码登录抖音")
        self.log("=" * 60)
        
        threading.Thread(target=self._auto_login_thread, daemon=True).start()
        
    def _auto_login_thread(self):
        try:
            self.log("📋 正在启动自动登录...")
            self.log("🌐 浏览器窗口即将弹出，请在浏览器中扫码登录")
            self.log("⏳ 登录完成后会自动检测Cookie...")
            
            login_bat = Path(__file__).parent / "start_login.bat"
            
            self.login_process = subprocess.Popen(
                str(login_bat),
                cwd=str(Path(__file__).parent),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            self.log("🔄 登录进程已启动，请在新窗口中完成登录")
            
            import time
            timeout = 180  
            check_interval = 3  
            elapsed = 0
            
            while elapsed < timeout:
                time.sleep(check_interval)
                elapsed += check_interval
                
                load_dotenv('.env', override=True)
                cookies_str = os.getenv('DY_COOKIES', '')
                
                if len(cookies_str) > 100:
                    self.log(f"✅ Cookie检测到！长度: {len(cookies_str)} 字符")
                    self.ui_call(lambda: self.status_label.config(text="✅ 已登录", fg="green"))
                    self.ui_call(lambda: messagebox.showinfo("成功", "登录成功！Cookie已保存到.env文件"))
                    return
                
                self.log(f"⏳ 等待中... ({elapsed}秒)")
                
                if self.login_process.poll() is not None:
                    self.log("⚠️ 登录进程已结束")
                    break
            
            load_dotenv('.env', override=True)
            cookies_str = os.getenv('DY_COOKIES', '')
            
            if len(cookies_str) > 100:
                self.log(f"✅ Cookie保存成功！长度: {len(cookies_str)} 字符")
                self.ui_call(lambda: self.status_label.config(text="✅ 已登录", fg="green"))
                self.ui_call(lambda: messagebox.showinfo("成功", "登录成功！Cookie已保存到.env文件"))
            else:
                self.log("⚠️ 登录超时或未完成")
                
                if os.getenv('DY_COOKIES', '') and len(os.getenv('DY_COOKIES', '')) > 100:
                    self.ui_call(lambda: self.status_label.config(text="✅ 已登录", fg="green"))
                    self.ui_call(lambda: messagebox.showwarning("提示", "检测到已有Cookie，继续使用原有Cookie"))
                else:
                    self.ui_call(lambda: self.status_label.config(text="❌ 登录失败", fg="red"))
                    self.ui_call(lambda: messagebox.showerror("失败", f"登录超时（{timeout}秒）\n\n请手动运行 python auto_login.py"))
            
        except Exception as e:
            self.log(f"❌ 自动登录出错: {e}")
            import traceback
            traceback.print_exc()
            
            cookies_str = os.getenv('DY_COOKIES', '')
            if cookies_str and len(cookies_str) > 100:
                self.ui_call(lambda: self.status_label.config(text="✅ 已登录", fg="green"))
                self.ui_call(lambda: messagebox.showwarning("提示", f"自动登录出错: {e}\n\n保持使用原有Cookie"))
            else:
                self.ui_call(lambda: self.status_label.config(text="❌ 登录失败", fg="red"))
                self.ui_call(lambda: messagebox.showerror("错误", f"自动登录失败:\n{e}"))
            
    def start_system(self):
        if self.running:
            self.log("⚠️ 系统已在运行中")
            return

        load_dotenv(BASE_DIR / '.env', override=True)
        cookies_str = os.getenv('DY_COOKIES', '')
        web_protect_str = os.getenv('WEB_PROTECT', '')
        keys_str = os.getenv('KEYS', '')

        if not cookies_str or len(cookies_str) < 100:
            messagebox.showwarning("提示", "请先点击【自动登录】或通过【账号管理】获取 Cookie")
            return
        if not web_protect_str or not keys_str:
            messagebox.showwarning(
                "提示",
                "缺少 WEB_PROTECT 或 KEYS，私信可能无法发送。\n\n"
                "请在浏览器控制台运行 get_web_protect.js 获取后写入 .env，或通过账号管理重新登录。"
            )
            
        self.log("🚀 正在启动系统...")
        threading.Thread(target=self.run_system, daemon=True).start()
        
    def stop_system(self):
        self.log("⏹️ 正在停止...")
        self.running = False
        if self.ws:
            self.ws.close()
        self.log("✅ 系统已停止")
        
    def run_system(self):
        try:
            from dy_apis.douyin_api import DouyinAPI
            
            load_dotenv(BASE_DIR / '.env', override=True)
            cookies_str = os.getenv('DY_COOKIES', '')
            web_protect_str = os.getenv('WEB_PROTECT', '')
            keys_str = os.getenv('KEYS', '')
            
            auth = DouyinAuth()
            auth.perepare_auth(cookies_str, web_protect_str, keys_str)
            self.auth = auth
            self.log("✅ 认证成功")

            try:
                self.my_uid = str(auth.get_uid())
                self.log(f"✅ 当前账号 UID: {self.my_uid}")
            except Exception as e:
                self.my_uid = None
                self.log(f"⚠️ 无法获取 UID，将跳过自身消息过滤: {e}")
            
            try:
                device_id = DouyinAPI.get_device_id(auth=auth)
                self.log(f"✅ device_id: {device_id}")
            except Exception:
                device_id = auth.cookie.get('a11y_device_id') or '7631877838707'
                self.log(f"⚠️ 使用备用device_id: {device_id}")
            
            try:
                self.system = AutoReplySystem(str(BASE_DIR / 'config_ai.env'))
                self.system.knowledge_base.load()
                self.log("✅ AI/回复系统就绪")
                if self.system.ai_fallback:
                    if self.system.ai_config.api_key:
                        self.log("🧪 正在测试 AI 连接...")
                        if self.system.test_ai_connection():
                            self.log("✅ AI 接口可用")
                        else:
                            self.log("⚠️ AI 接口不可用：API Key 无效或已过期")
                            self.log("   请到 https://platform.minimaxi.com 重新生成 Key")
                            self.log("   写入 config_ai.env 的 ANTHROPIC_API_KEY 或 .env 的 MINIMAX_API_KEY")
                    else:
                        self.log("⚠️ 未配置 API Key，AI 降级回复不可用")
            except Exception as e:
                self.log(f"⚠️ AI系统初始化失败: {e}")
                self.system = None
            
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
            
            self.running = True
            self.log("🔌 WebSocket连接中...")
            
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
            self.log(f"❌ 系统启动失败: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
            
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
                conversation_short_id = msg.conversation_short_id
                
                if self.my_uid and str(sender) == self.my_uid:
                    return
                
                try:
                    content = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    content = {}
                
                if msg_type == 7:
                    text = content.get("text", "")
                    if text:
                        self.log(f"💬 收到私信 from {sender}: {text}")
                        threading.Thread(
                            target=self.reply_async,
                            args=(text, str(conversation_id), sender, conversation_short_id),
                            daemon=True
                        ).start()
                        
        except Exception as e:
            self.log(f"⚠️ 消息处理错误: {e}")
    
    def reply_async(self, text, conversation_id, sender, conversation_short_id=0):
        try:
            import random

            if self.system:
                min_delay = self.system.min_delay
                max_delay = self.system.max_delay
            else:
                min_delay, max_delay = 8, 20

            delay = random.uniform(min_delay, max_delay)
            self.log(f"⏳ 延迟 {delay:.1f}秒后回复...")
            time.sleep(delay)
            
            reply = None
            
            if self.system:
                message = Message(sender=str(sender), content=text, conversation_id=conversation_id)
                reply = self.system.process_message(message)
                
                if reply:
                    source = "知识库" if self.system.knowledge_first and self.system.knowledge_base.find_match(text) else "AI"
                    self.log(f"🤖 {source}回复: {reply}")
                else:
                    self.log("⚠️ 自动回复未生成内容（可能未命中知识库或已关闭 AI 降级）")
            
            if not reply:
                reply = self.kb_manager.match_knowledge(text)
                if reply:
                    self.log(f"📚 知识库匹配回复: {reply}")
                else:
                    self.log("⚠️ 知识库未匹配到相关内容")
            
            if reply:
                self.send_reply(conversation_id, conversation_short_id, reply)
            else:
                self.log("⚠️ 没有可用的回复内容")
                
        except Exception as e:
            self.log(f"❌ 回复错误: {e}")
    
    def send_reply(self, conversation_id, conversation_short_id, reply_text):
        try:
            from dy_apis.douyin_api import DouyinAPI
            
            auth = self.auth
            if auth is None:
                load_dotenv(BASE_DIR / '.env', override=True)
                auth = DouyinAuth()
                auth.perepare_auth(
                    os.getenv('DY_COOKIES', ''),
                    os.getenv('WEB_PROTECT', ''),
                    os.getenv('KEYS', '')
                )

            if not conversation_short_id:
                parts = str(conversation_id).split(':')
                if len(parts) >= 4:
                    try:
                        conversation_short_id = int(parts[3])
                    except ValueError:
                        conversation_short_id = 0
            
            ticket = auth.ticket or ""
            
            DouyinAPI.send_msg(
                auth,
                conversation_id,
                conversation_short_id,
                ticket,
                reply_text
            )
            self.log(f"✅ 发送成功: {reply_text[:30]}...")
            
        except Exception as e:
            self.log(f"❌ 发送失败: {e}")
    
    def on_error(self, ws, error):
        self.log(f"❌ WebSocket错误: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        self.log(f"📴 连接已断开 ({close_status_code})")
        if self.running:
            self.log("🔄 30秒后尝试重新连接...")
            threading.Thread(target=self._schedule_reconnect, daemon=True).start()

    def _schedule_reconnect(self):
        time.sleep(30)
        if self.running:
            self.log("🔄 正在重新连接...")
            threading.Thread(target=self.run_system, daemon=True).start()

    def on_open(self, ws):
        self.log("✅ WebSocket连接成功！")
        self.log("📝 开始监听私信消息...")


if __name__ == '__main__':
    app = DouyinGUI()
    app.root.mainloop()