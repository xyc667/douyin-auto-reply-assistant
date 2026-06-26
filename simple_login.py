#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
import time
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class SimpleLogin:
    def __init__(self):
        self.cookies = {}
        self.login_success = False
        self.login_completed = False

    def get_chrome_cookies_path(self):
        import platform
        
        if platform.system() == 'Windows':
            return Path(os.environ['USERPROFILE']) / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Network' / 'Cookies'
        elif platform.system() == 'Darwin':
            return Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'Network' / 'Cookies'
        else:
            return Path.home() / '.config' / 'google-chrome' / 'Default' / 'Network' / 'Cookies'

    def extract_douyin_cookies(self):
        cookies_path = self.get_chrome_cookies_path()
        
        if not cookies_path.exists():
            print(f"❌ Cookie文件不存在: {cookies_path}")
            return None
            
        try:
            temp_path = Path('.') / 'cookies_temp'
            shutil.copy2(cookies_path, temp_path)
            
            import sqlite3
            conn = sqlite3.connect(str(temp_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, value FROM cookies WHERE host_key LIKE '%douyin.com%'")
            cookies = cursor.fetchall()
            
            conn.close()
            temp_path.unlink()
            
            return {name: value for name, value in cookies}
            
        except Exception as e:
            print(f"❌ 读取Cookie失败: {e}")
            return None

    def save_to_env(self, cookies_dict):
        cookie_str = '; '.join([f"{name}={value}" for name, value in cookies_dict.items()])
        
        env_path = Path('.env')
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""

        content = re.sub(r'^DY_COOKIES=.*$', f'DY_COOKIES={cookie_str}', content, flags=re.MULTILINE)
        if 'DY_COOKIES=' not in content:
            content += f'\nDY_COOKIES={cookie_str}'

        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Cookie已保存到.env文件")
        print(f"📋 Cookie包含 {len(cookies_dict)} 个字段")

    def open_browser(self):
        print("🌐 正在打开浏览器...")
        webbrowser.open('https://www.douyin.com')
        print("✅ 浏览器已打开，请登录抖音账号")

    def wait_for_login(self):
        print("⏳ 等待登录完成...")
        print("💡 登录成功后，请在GUI中点击'已登录'按钮")
        
        timeout = 300
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.login_completed:
                break
            time.sleep(1)
        
        if self.login_completed:
            return True
        else:
            print("❌ 等待超时")
            return False

    def run(self, auto_open_browser=True):
        print("🔑 抖音Cookie提取工具")
        print("=" * 60)
        
        if auto_open_browser:
            self.open_browser()
        
        print("💡 请在浏览器中完成以下操作:")
        print("  1. 如果未登录，请点击右上角'登录'按钮")
        print("  2. 选择'扫码登录'或'密码登录'")
        print("  3. 完成登录后关闭浏览器")
        print("=" * 60)
        print("⏳ 等待登录完成...")
        
        time.sleep(5)
        
        cookies = self.extract_douyin_cookies()
        
        if cookies and 'sessionid' in cookies and cookies['sessionid']:
            print(f"✅ 检测到登录状态！")
            print(f"📊 sessionid: {cookies['sessionid'][:20]}...")
            self.save_to_env(cookies)
            print("=" * 60)
            print("🎉 Cookie提取成功！")
            print("=" * 60)
            self.login_success = True
            return True
        else:
            print("❌ 未检测到登录状态")
            print("💡 请确保已在Chrome浏览器中登录抖音")
            return False


if __name__ == '__main__':
    login = SimpleLogin()
    login.run()