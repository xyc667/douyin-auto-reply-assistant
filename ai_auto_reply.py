#!/usr/bin/env python3
"""
AI智能回复系统 - 支持MiniMax API
"""

import os
import sys
import json
import time
import random
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import hashlib

# 加载环境变量
from dotenv import load_dotenv
from account_manager import safe_print

@dataclass
class Message:
    """消息结构"""
    sender: str
    content: str
    conversation_id: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class AIConfig:
    """AI配置"""
    provider: str = "anthropic"
    api_key: str = ""
    base_url: str = "https://api.minimaxi.com/anthropic"
    model: str = "MiniMax-M2.7"
    max_tokens: int = 1000
    temperature: float = 0.7

class KnowledgeBase:
    """知识库"""
    
    def __init__(self, kb_file: str):
        self.kb_file = kb_file
        self.knowledge = []
        self.load()
    
    def load(self):
        """加载知识库"""
        try:
            if os.path.exists(self.kb_file):
                with open(self.kb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge = data.get('knowledge_base', [])
                safe_print(f"✅ 知识库加载成功，共 {len(self.knowledge)} 条")
            else:
                safe_print(f"⚠️ 知识库文件不存在: {self.kb_file}")
        except Exception as e:
            safe_print(f"❌ 知识库加载失败: {e}")
            self.knowledge = []
    
    def find_match(self, question: str, threshold: float = 0.7) -> Optional[str]:
        """查找匹配的知识"""
        question = question.lower().strip()
        
        for item in self.knowledge:
            q = item.get('question', '').lower().strip()
            # 简单的关键词匹配
            if q in question or question in q:
                return item.get('answer', '')
            
            # 检查关键词重叠
            q_words = set(q)
            q_words_user = set(question)
            overlap = len(q_words & q_words_user) / len(q_words | q_words_user) if q_words and q_words_user else 0
            
            if overlap >= threshold:
                return item.get('answer', '')
        
        return None

class Blacklist:
    """黑名单管理"""
    
    def __init__(self, blacklist_file: str):
        self.blacklist_file = blacklist_file
        self.blocked_users = set()
        self.lock = Lock()
        self.load()
    
    def load(self):
        """加载黑名单"""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    self.blocked_users = set(line.strip() for line in f if line.strip())
                safe_print(f"✅ 黑名单加载成功，共 {len(self.blocked_users)} 个用户")
            else:
                # 创建空的黑名单文件
                Path(self.blacklist_file).parent.mkdir(parents=True, exist_ok=True)
                with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                    f.write("")
                safe_print("✅ 黑名单文件已创建")
        except Exception as e:
            safe_print(f"❌ 黑名单加载失败: {e}")
    
    def is_blocked(self, user_id: str) -> bool:
        """检查用户是否在黑名单中"""
        with self.lock:
            return user_id in self.blocked_users
    
    def add(self, user_id: str):
        """添加用户到黑名单"""
        with self.lock:
            self.blocked_users.add(user_id)
            self.save()
    
    def remove(self, user_id: str):
        """从黑名单移除用户"""
        with self.lock:
            self.blocked_users.discard(user_id)
            self.save()
    
    def save(self):
        """保存黑名单"""
        try:
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(self.blocked_users)))
        except Exception as e:
            safe_print(f"❌ 保存黑名单失败: {e}")

class AIClient:
    """AI客户端 - MiniMax API"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.session_history = {}  # 按用户保存对话历史
        self.session_lock = Lock()
    
    def chat(self, message: str, user_id: str = "default", system_prompt: str = "") -> str:
        """发送对话请求"""
        try:
            import requests
            
            # 获取或创建对话历史
            with self.session_lock:
                if user_id not in self.session_history:
                    self.session_history[user_id] = []
                
                history = self.session_history[user_id]
            
            # 构建消息列表
            messages = []
            
            # 添加系统提示
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加历史对话（保留最近10条）
            messages.extend(history[-10:])
            
            # 添加当前消息
            messages.append({
                "role": "user",
                "content": message
            })
            
            # 调用API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
                "anthropic-version": "2023-06-01",
            }
            
            data = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            response = requests.post(
                f"{self.config.base_url}/v1/messages",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # MiniMax API 返回格式：{"content":[{"text":"...","type":"text"}]}
                reply = ""
                content = result.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if item.get('type') == 'text':
                            reply = item.get('text', '').strip()
                            break
                
                if not reply:
                    safe_print(f"⚠️ AI返回为空: {result}")
                    return None
                
                # 保存对话历史
                with self.session_lock:
                    self.session_history[user_id].append({
                        "role": "user",
                        "content": message
                    })
                    self.session_history[user_id].append({
                        "role": "assistant",
                        "content": reply
                    })
                
                return reply
            else:
                safe_print(f"❌ API调用失败: {response.status_code} - {response.text}")
                return None
                
        except ImportError:
            safe_print("❌ 请安装requests库: pip install requests")
            return None
        except Exception as e:
            safe_print(f"❌ AI调用失败: {e}")
            traceback.print_exc()
            return None

class ReplyLogger:
    """日志记录"""
    
    def __init__(self, log_file: str, keep_days: int = 30):
        self.log_file = log_file
        self.keep_days = keep_days
        self.lock = Lock()
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # 设置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, level: str, message: str, **kwargs):
        """记录日志"""
        log_data = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message
        }
        log_data.update(kwargs)
        
        log_msg = json.dumps(log_data, ensure_ascii=False)
        
        with self.lock:
            if level == "INFO":
                self.logger.info(log_msg)
            elif level == "ERROR":
                self.logger.error(log_msg)
            elif level == "WARNING":
                self.logger.warning(log_msg)

class AutoReplySystem:
    """自动回复系统"""
    
    def __init__(self, config_file: str = "config_ai.env"):
        config_path = Path(config_file)
        load_dotenv(config_path)
        if config_path.parent.exists():
            load_dotenv(config_path.parent / '.env')
        
        api_key = (
            os.getenv('ANTHROPIC_API_KEY', '').strip()
            or os.getenv('MINIMAX_API_KEY', '').strip()
        )
        
        # 初始化配置
        self.ai_config = AIConfig(
            provider=os.getenv('AI_PROVIDER', 'anthropic'),
            api_key=api_key,
            base_url=os.getenv('ANTHROPIC_BASE_URL', 'https://api.minimaxi.com/anthropic'),
            model=os.getenv('AI_MODEL', 'MiniMax-M2.7'),
            max_tokens=int(os.getenv('MAX_TOKENS', '1000')),
            temperature=float(os.getenv('TEMPERATURE', '0.7'))
        )
        
        # 初始化组件
        self.ai_client = AIClient(self.ai_config)
        self.knowledge_base = KnowledgeBase(os.getenv('KNOWLEDGE_BASE_PATH', 'datas/knowledge_base.json'))
        self.blacklist = Blacklist(os.getenv('BLACKLIST_FILE', 'datas/blacklist.txt'))
        self.logger = ReplyLogger(
            os.getenv('LOG_FILE', 'datas/reply_log.txt'),
            int(os.getenv('LOG_KEEP_DAYS', '30')))
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=int(os.getenv('MAX_CONCURRENT', '10')))
        
        # 系统提示词
        self.system_prompt = os.getenv('SYSTEM_PROMPT', 
            '你是一个智能客服助手，请用友好、专业的态度回复用户的问题。'
            '如果不确定答案，请诚实地告诉用户你会转人工处理。'
            '保持回答简洁明了，不超过200字。')
        
        # 配置项
        self.min_delay = int(os.getenv('MIN_REPLY_DELAY', '2'))
        self.max_delay = int(os.getenv('MAX_REPLY_DELAY', '8'))
        self.max_retry = int(os.getenv('MAX_RETRY', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        self.auto_reply_enabled = os.getenv('AUTO_REPLY_ENABLED', 'true').lower() == 'true'
        self.knowledge_first = os.getenv('KNOWLEDGE_FIRST', 'false').lower() == 'true'
        self.ai_fallback = os.getenv('AI_FALLBACK', 'true').lower() == 'true'
        
        safe_print("=" * 60)
        safe_print("🤖 AI自动回复系统初始化完成！")
        safe_print("=" * 60)
        safe_print(f"AI服务商: {self.ai_config.provider}")
        safe_print(f"API地址: {self.ai_config.base_url}")
        safe_print(f"模型: {self.ai_config.model}")
        safe_print(f"自动回复: {'启用' if self.auto_reply_enabled else '禁用'}")
        safe_print(f"知识库优先: {'是' if self.knowledge_first else '否'}")
        safe_print(f"AI降级: {'启用' if self.ai_fallback else '禁用（纯知识库模式）'}")
        safe_print(f"API Key: {'已配置' if self.ai_config.api_key else '未配置'}")
        safe_print(f"并发数: {os.getenv('MAX_CONCURRENT', '10')}")
        safe_print("=" * 60)
    
    def test_ai_connection(self) -> bool:
        """测试 AI API 是否可用"""
        if not self.ai_config.api_key:
            safe_print("❌ 未配置 API Key")
            return False
        reply = self.ai_client.chat("你好", user_id="__api_test__", system_prompt="请用一句话回复")
        if reply:
            safe_print(f"✅ AI 连接测试成功: {reply[:50]}")
            return True
        safe_print("❌ AI 连接测试失败，请检查 API Key 是否有效")
        return False
    
    def process_message(self, message: Message) -> Optional[str]:
        """处理单条消息"""
        # 检查黑名单
        if self.blacklist.is_blocked(message.sender):
            self.logger.log("INFO", "用户在黑名单中，跳过", user_id=message.sender)
            return None
        
        # 检查自动回复是否启用
        if not self.auto_reply_enabled:
            self.logger.log("INFO", "自动回复已禁用，跳过", user_id=message.sender)
            return None
        
        # 知识库优先模式
        if self.knowledge_first:
            kb_reply = self.knowledge_base.find_match(message.content)
            if kb_reply:
                self.logger.log("INFO", "知识库命中", user_id=message.sender, 
                             content=message.content, reply=kb_reply)
                return kb_reply
            
            if not self.ai_fallback:
                self.logger.log("INFO", "知识库未命中且关闭AI降级，跳过", user_id=message.sender)
                return None
        
        # 调用AI
        for attempt in range(self.max_retry):
            try:
                self.logger.log("INFO", "调用AI", user_id=message.sender, 
                             content=message.content, attempt=attempt + 1)
                
                reply = self.ai_client.chat(
                    message=message.content,
                    user_id=message.sender,
                    system_prompt=self.system_prompt
                )
                
                if reply:
                    self.logger.log("INFO", "AI回复成功", user_id=message.sender, reply=reply)
                    return reply
                
                self.logger.log("WARNING", "AI未返回有效回复", user_id=message.sender,
                             attempt=attempt + 1)
                
            except Exception as e:
                self.logger.log("ERROR", "AI调用失败", user_id=message.sender, 
                             error=str(e), attempt=attempt + 1)
                if attempt < self.max_retry - 1:
                    time.sleep(self.retry_delay)
        
        # 所有重试都失败
        return None
    
    def auto_reply_with_delay(self, message: Message) -> Optional[str]:
        """带延迟的自动回复"""
        # 模拟人工回复延迟
        delay = random.uniform(self.min_delay, self.max_delay)
        safe_print(f"⏱️  延迟 {delay:.1f} 秒后回复...")
        time.sleep(delay)
        
        return self.process_message(message)
    
    def handle_received_message(self, sender: str, content: str, conversation_id: str):
        """处理接收到的消息"""
        message = Message(
            sender=sender,
            content=content,
            conversation_id=conversation_id
        )
        
        safe_print(f"\n📩 收到消息 from {sender}: {content}")
        
        # 提交到线程池处理
        future = self.executor.submit(self.auto_reply_with_delay, message)
        return future

# 主程序入口
if __name__ == '__main__':
    safe_print("=" * 60)
    safe_print("🚀 AI自动回复系统")
    safe_print("=" * 60)
    
    # 初始化系统
    system = AutoReplySystem()
    
    # 测试AI连接
    safe_print("\n🧪 测试AI连接...")
    test_reply = system.ai_client.chat("你好", user_id="test")
    safe_print(f"AI回复: {test_reply}")
    
    safe_print("\n" + "=" * 60)
    safe_print("✅ 系统初始化完成！")
    safe_print("=" * 60)
    safe_print("\n使用方法：")
    safe_print("1. 配置 config_ai.env 中的 API 密钥")
    safe_print("2. 运行 抖音私信助手_整合版.py")
    safe_print("3. 修改知识库 datas/knowledge_base.json")
    safe_print("\n或直接运行此文件进行测试")