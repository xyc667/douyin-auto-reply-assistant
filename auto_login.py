#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
import re
import time
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


class AutoLogin:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.cookies = {}
        self.web_protect = ""
        self.keys = ""
        self.login_success = False
        self.user_nickname = ""
        self.auth = None

    async def init_browser(self, headless=False):
        p = await async_playwright().start()
        self.playwright = p
        self.browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        )
        self.page = await self.context.new_page()

    async def get_initial_cookies(self):
        from builder.auth import DouyinAuth

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            page = await browser.new_page()
            await page.goto('https://www.douyin.com/')
            await page.wait_for_load_state("load")
            await asyncio.sleep(10)

            keys_str = await page.evaluate('localStorage.getItem("security-sdk/s_sdk_crypt_sdk") || ""')

            cookies = dict()
            page_cookies = await page.context.cookies()
            for cookie in page_cookies:
                cookies[cookie['name']] = cookie['value']

            await browser.close()

            self.auth = DouyinAuth()
            if keys_str:
                self.auth.perepare_auth('', '', keys_str)
            else:
                self.auth.perepare_auth('', '', '')
            self.auth.cookie = cookies

            return self.auth

    def get_qrcode(self, auth):
        import requests
        from builder.auth import DouyinAuth
        from builder.header import HeaderBuilder, HeaderType
        from builder.params import Params

        api = "get_qrcode/"
        headers = HeaderBuilder().build(HeaderType.GET)
        headers.set_referer("https://www.douyin.com/")

        params = Params()
        params.add_param("service", 'https://www.douyin.com')
        params.add_param("need_logo", 'false')
        params.add_param("need_short_url", 'false')
        params.add_param("passport_jssdk_version", "1.0.26")
        params.add_param("passport_jssdk_type", "pro")
        params.add_param("aid", '6383')
        params.add_param("language", 'zh')
        params.add_param("account_sdk_source", 'sso')
        params.add_param("account_sdk_source_info", "")
        params.add_param("passport_ztsdk", '3.0.20')
        params.add_param("passport_verify", '1.0.17')
        params.add_param("device_platform", 'web_app')
        params.add_param("msToken", auth.cookie.get('msToken', ''))
        params.with_a_bogus()

        try:
            resp = requests.get(f"https://sso.douyin.com/{api}", headers=headers.get(),
                             cookies=auth.cookie, params=params.get(), verify=False, timeout=10)
            return json.loads(resp.text)
        except Exception as e:
            print(f"获取二维码失败: {e}")
            return None

    def check_qrcode_login(self, auth, token):
        import requests
        from builder.auth import DouyinAuth
        from builder.header import HeaderBuilder, HeaderType
        from builder.params import Params

        api = 'check_qrconnect/'
        headers = HeaderBuilder().build(HeaderType.GET)
        headers.set_referer("https://www.douyin.com/")

        params = Params()
        params.add_param("service", 'https://www.douyin.com')
        params.add_param("token", token)
        params.add_param("need_logo", 'false')
        params.add_param("is_frontier", 'false')
        params.add_param("need_short_url", 'false')
        params.add_param("passport_jssdk_version", "1.0.26")
        params.add_param("passport_jssdk_type", "pro")
        params.add_param("aid", '6383')
        params.add_param("language", 'zh')
        params.add_param("account_sdk_source", 'sso')
        params.add_param("account_sdk_source_info", "")
        params.add_param("passport_ztsdk", '3.0.20')
        params.add_param("passport_verify", '1.0.17')
        params.add_param("biz_trace_id", auth.cookie.get('biz_trace_id', ''))
        params.add_param("device_platform", 'web_app')
        params.add_param("msToken", auth.cookie.get('msToken', ''))
        params.with_a_bogus()

        try:
            resp = requests.get(f"https://sso.douyin.com/{api}", headers=headers.get(),
                             cookies=auth.cookie, params=params.get(), verify=False, timeout=10)
            return json.loads(resp.text)
        except Exception as e:
            print(f"检查扫码状态失败: {e}")
            return None

    def generate_qrcode_image(self, verify_url):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.show()

    async def check_login_status(self):
        try:
            await self.page.goto("https://www.douyin.com/", wait_until='domcontentloaded')
            await asyncio.sleep(3)

            cookies = await self.context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'sessionid' and cookie['value']:
                    return True

            await self.page.goto("https://www.douyin.com/", wait_until='domcontentloaded')
            await asyncio.sleep(5)

            cookies = await self.context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'sessionid' and cookie['value']:
                    return True

            return False
        except Exception as e:
            print(f"检测登录状态失败: {e}")
            return False

    async def get_local_storage_data(self):
        web_protect = await self.page.evaluate('''() => {
            return localStorage.getItem('security-sdk/s_sdk_sign_data_key/web_protect') || '';
        }''')

        keys = await self.page.evaluate('''() => {
            return localStorage.getItem('security-sdk/s_sdk_crypt_sdk') || '';
        }''')

        return web_protect, keys

    async def get_all_cookies(self):
        cookies = await self.context.cookies()
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies if c['value']])
        return cookie_str, cookies

    async def login_with_qrcode(self):
        print("\n正在生成二维码...")

        try:
            self.auth = await self.get_initial_cookies()
            qr_code_dict = self.get_qrcode(self.auth)

            if not qr_code_dict or 'data' not in qr_code_dict:
                print("❌ 获取二维码失败，尝试直接访问抖音...")
                await self._fallback_login()
                return self.login_success

            token = qr_code_dict['data'].get('token', '')
            verify_url = qr_code_dict['data'].get('qrcode_index_url', '')

            if not token or not verify_url:
                print("❌ 二维码数据不完整，尝试直接访问抖音...")
                await self._fallback_login()
                return self.login_success

            print("✅ 二维码获取成功，正在显示...")
            self.generate_qrcode_image(verify_url)
            print("📱 请打开抖音App扫描二维码登录")

            timeout = 120
            start_time = time.time()
            login_status = None

            while time.time() - start_time < timeout:
                check_result = self.check_qrcode_login(self.auth, token)

                if check_result:
                    status = check_result.get('data', {}).get('status')

                    if status == 'confirmed':
                        print("✅ 扫码成功！正在获取登录信息...")

                        redirect_url = check_result['data'].get('redirect_url', '')
                        await self._process_redirect(redirect_url)

                        cookies = await self.context.cookies()
                        for cookie in cookies:
                            if cookie['name'] == 'sessionid':
                                self.login_success = True
                                break

                        if self.login_success:
                            return True

                    elif status == 'expired':
                        print("❌ 二维码已过期，请重新运行程序")
                        return False
                    elif status == 'waiting':
                        pass
                    elif status == 'scanned':
                        print("📱 请在手机上确认登录")

                await asyncio.sleep(2)

            print("❌ 扫码登录超时")
            return False

        except Exception as e:
            print(f"❌ 扫码登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _fallback_login(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled'],
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            await page.goto("https://www.douyin.com/", wait_until='domcontentloaded')
            await asyncio.sleep(3)

            try:
                login_btn = page.locator('text=登录').first
                if login_btn and await login_btn.is_visible():
                    await login_btn.click()
                    await asyncio.sleep(2)

                    try:
                        qr_tab = page.locator('text=扫码登录').first
                        if qr_tab and await qr_tab.is_visible():
                            await qr_tab.click()
                            print("📱 请扫描页面上的二维码登录")
                    except:
                        pass

                timeout = 180
                start_time = time.time()
                sessionid = None

                print("⏳ 等待扫码登录...")
                print("提示：请使用抖音App扫描二维码，并在手机上确认登录")
                print("程序将持续等待直到登录成功或超时...")

                while time.time() - start_time < timeout:
                    cookies = await context.cookies()
                    for cookie in cookies:
                        if cookie['name'] == 'sessionid' and cookie['value']:
                            sessionid = cookie['value']
                            print(f"✅ 检测到sessionid: {sessionid[:20]}...")
                            break

                    if sessionid:
                        self.login_success = True
                        self.cookies = cookies
                        print("✅ 登录成功！正在准备保存Cookie...")
                        
                        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies if c['value']])
                        if len(cookie_str) > 100:
                            await self.save_to_env(cookie_str)
                            print(f"✅ Cookie 长度: {len(cookie_str)} 字符")
                            
                            print("\n" + "=" * 60)
                            print("🎉 登录成功！")
                            print("=" * 60)
                            print("\n你可以运行以下命令测试:")
                            print("  python check_cookie.py  - 检查Cookie")
                            print("  python main.py         - 运行主程序")
                        else:
                            print("⚠️ Cookie为空或不完整")
                        break

                    if int(time.time() - start_time) % 10 == 0:
                        print(f"⏳ 等待中... ({int(time.time() - start_time)}秒)")

                    await asyncio.sleep(1)

                if not self.login_success:
                    print("⚠️ 超时，请重新运行程序")

            except Exception as e:
                print(f"备用登录失败: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(2)
            await browser.close()

    async def _process_redirect(self, redirect_url):
        if not redirect_url:
            return

        try:
            await self.page.goto(redirect_url, wait_until='domcontentloaded')
            await asyncio.sleep(5)

            final_cookies = await self.context.cookies()
            self.cookies = {c['name']: c['value'] for c in final_cookies}

            web_protect, keys = await self.get_local_storage_data()
            if web_protect:
                self.web_protect = web_protect
            if keys:
                self.keys = keys

        except Exception as e:
            print(f"处理重定向失败: {e}")

    async def save_to_env(self, cookie_str, web_protect="", keys=""):
        env_path = Path(__file__).parent / '.env'

        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        new_content = []
        for line in lines:
            if line.startswith('DY_COOKIES='):
                new_content.append(f'DY_COOKIES={cookie_str}\n')
            elif line.startswith('WEB_PROTECT='):
                if web_protect:
                    new_content.append(f'WEB_PROTECT={web_protect}\n')
                else:
                    new_content.append(line)
            elif line.startswith('KEYS='):
                if keys:
                    new_content.append(f'KEYS={keys}\n')
                else:
                    new_content.append(line)
            else:
                new_content.append(line)

        if not any(l.startswith('DY_COOKIES=') for l in new_content):
            new_content.append(f'DY_COOKIES={cookie_str}\n')
        if web_protect and not any(l.startswith('WEB_PROTECT=') for l in new_content):
            new_content.append(f'WEB_PROTECT={web_protect}\n')
        if keys and not any(l.startswith('KEYS=') for l in new_content):
            new_content.append(f'KEYS={keys}\n')

        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(new_content)

        print(f"✅ Cookie 已保存到 .env 文件")
        print(f"Cookie 长度: {len(cookie_str)} 字符")

    async def run(self):
        print("=" * 60)
        print("🚀 抖音自动登录工具")
        print("=" * 60)
        print("\n正在初始化...")

        try:
            await self.init_browser(headless=True)
            print("✅ 浏览器启动成功")

            print("\n正在检测登录状态...")
            is_logged_in = await self.check_login_status()

            if is_logged_in:
                print("✅ 检测到已登录，开始获取参数...")

                cookie_str, self.cookies = await self.get_all_cookies()

                cookies_dict = {c['name']: c['value'] for c in self.cookies}
                sessionid_value = cookies_dict.get('sessionid', '')

                if sessionid_value:
                    print("✅ 获取到 sessionid")
                    self.login_success = True
                else:
                    print("⚠️ 未检测到有效的sessionid，跳过Cookie保存")
                    self.login_success = False

                try:
                    self.user_nickname = await self.page.evaluate('''() => {
                        const nicknames = document.querySelectorAll('[class*="nickname"], [class*="name"]');
                        for (let el of nicknames) {
                            if (el.textContent.trim()) return el.textContent.trim();
                        }
                        return '';
                    }''')
                    if self.user_nickname:
                        print(f"👤 登录用户: {self.user_nickname}")
                except:
                    pass

                web_protect, keys = await self.get_local_storage_data()
                if web_protect:
                    print("✅ 获取到 web_protect 参数")
                if keys:
                    print("✅ 获取到 keys 参数")

            else:
                print("❌ 未登录，开始扫码登录流程...")
                self.login_success = await self.login_with_qrcode()

            if self.login_success:
                cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in self.cookies if c['value']])

                if len(cookie_str) > 100:
                    await self.save_to_env(cookie_str, self.web_protect, self.keys)
                    print("\n" + "=" * 60)
                    print("🎉 登录成功！")
                    print("=" * 60)
                    print("\n你可以运行以下命令测试:")
                    print("  python check_cookie.py  - 检查Cookie")
                    print("  python main.py         - 运行主程序")
                else:
                    print("\n⚠️ Cookie为空或不完整，保存失败")
                    print("请手动登录或检查网络连接")
            else:
                print("\n❌ 登录失败，请重试")
                print("提示:")
                print("  1. 确保抖音App已登录")
                print("  2. 扫码后及时确认")
                print("  3. 检查网络连接")

        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.browser:
                await self.browser.close()


def main():
    print("\n" + "=" * 60)
    print("📌 使用说明")
    print("=" * 60)
    print("1. 运行此脚本将自动打开抖音扫码登录")
    print("2. 使用抖音App扫描二维码")
    print("3. 在手机上确认登录")
    print("4. 等待自动获取Cookie并保存")
    print("=" * 60 + "\n")

    auto_login = AutoLogin()
    asyncio.run(auto_login.run())
    
    if auto_login.login_success:
        print(f"\n✅ 登录成功标记: {auto_login.login_success}")
        print("✅ Cookie文件已更新")
        return 0
    else:
        print(f"\n❌ 登录成功标记: {auto_login.login_success}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())