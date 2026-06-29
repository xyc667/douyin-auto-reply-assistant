import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from dotenv import load_dotenv, set_key


def safe_print(msg: str):
    """安全打印函数，处理Windows GBK编码问题"""
    encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode(encoding, errors='replace').decode(encoding, errors='replace'))


@dataclass
class Account:
    """账号数据模型"""
    id: str
    name: str
    nickname: str = ""
    cookies: str = ""
    web_protect: str = ""
    keys: str = ""
    is_active: bool = False
    created_at: str = ""
    last_login: str = ""


class AccountManager:
    """账号管理器"""
    
    def __init__(self):
        self.accounts_file = Path(__file__).parent / 'accounts.json'
        self.accounts: List[Account] = []
        self.current_account: Optional[Account] = None
        self.load_accounts()
    
    def load_accounts(self):
        """加载账号列表"""
        try:
            if self.accounts_file.exists():
                with open(self.accounts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = [Account(**acc) for acc in data.get('accounts', [])]
                
                active_acc = next((acc for acc in self.accounts if acc.is_active), None)
                if active_acc:
                    self.current_account = active_acc
                    self.apply_account(active_acc)
                
                safe_print(f"已加载 {len(self.accounts)} 个账号")
            else:
                self.accounts = []
                self.migrate_from_env()
        except Exception as e:
            safe_print(f"加载账号失败: {e}")
            self.accounts = []
    
    def migrate_from_env(self):
        """从.env文件迁移账号（兼容旧版本）"""
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            cookies = os.getenv('DY_COOKIES', '')
            web_protect = os.getenv('WEB_PROTECT', '')
            keys = os.getenv('KEYS', '')
            
            if cookies and len(cookies) > 100:
                account = Account(
                    id="default",
                    name="默认账号",
                    nickname="未知",
                    cookies=cookies,
                    web_protect=web_protect,
                    keys=keys,
                    is_active=True
                )
                self.accounts.append(account)
                self.save_accounts()
                safe_print("已从.env迁移账号")
    
    def save_accounts(self):
        """保存账号列表"""
        try:
            data = {
                'accounts': [acc.__dict__ for acc in self.accounts]
            }
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            safe_print(f"保存账号失败: {e}")
            return False
    
    def add_account(self, name: str, cookies: str, web_protect: str = "", keys: str = "", nickname: str = "") -> bool:
        """添加新账号"""
        import uuid
        account = Account(
            id=str(uuid.uuid4())[:8],
            name=name,
            nickname=nickname,
            cookies=cookies,
            web_protect=web_protect,
            keys=keys,
            is_active=False
        )
        self.accounts.append(account)
        return self.save_accounts()
    
    def update_account(self, account_id: str, **kwargs) -> bool:
        """更新账号信息"""
        account = self.get_account(account_id)
        if account:
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            return self.save_accounts()
        return False
    
    def delete_account(self, account_id: str) -> bool:
        """删除账号"""
        account = self.get_account(account_id)
        if account and len(self.accounts) > 1:
            self.accounts = [acc for acc in self.accounts if acc.id != account_id]
            if self.current_account and self.current_account.id == account_id:
                self.current_account = self.accounts[0]
                self.current_account.is_active = True
            return self.save_accounts()
        return False
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """获取账号"""
        return next((acc for acc in self.accounts if acc.id == account_id), None)
    
    def get_account_list(self) -> List[Dict]:
        """获取账号列表（用于显示）"""
        return [{
            'id': acc.id,
            'name': acc.name,
            'nickname': acc.nickname,
            'is_active': acc.is_active,
            'has_cookie': len(acc.cookies) > 100
        } for acc in self.accounts]
    
    def set_active_account(self, account_id: str) -> bool:
        """设置活跃账号"""
        account = self.get_account(account_id)
        if account:
            for acc in self.accounts:
                acc.is_active = (acc.id == account_id)
            self.current_account = account
            self.apply_account(account)
            return self.save_accounts()
        return False
    
    def apply_account(self, account: Account):
        """应用账号配置到.env"""
        env_path = Path(__file__).parent / '.env'
        
        if not env_path.exists():
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("")
        
        set_key(str(env_path), 'DY_COOKIES', account.cookies)
        set_key(str(env_path), 'WEB_PROTECT', account.web_protect)
        set_key(str(env_path), 'KEYS', account.keys)
        
        load_dotenv(env_path, override=True)
        safe_print(f"已切换到账号: {account.name}")
    
    def get_current_account(self) -> Optional[Account]:
        """获取当前活跃账号"""
        return self.current_account
    
    def has_accounts(self) -> bool:
        """检查是否有账号"""
        return len(self.accounts) > 0
    
    def get_default_account(self) -> Optional[Account]:
        """获取默认账号（第一个）"""
        return self.accounts[0] if self.accounts else None