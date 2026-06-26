import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from account_manager import AccountManager


class AccountManagerWindow:
    """账号管理窗口"""
    
    def __init__(self, parent, account_manager: AccountManager):
        self.parent = parent
        self.account_manager = account_manager
        
        self.window = tk.Toplevel(parent.root)
        self.window.title("账号管理")
        self.window.geometry("700x500")
        self.window.transient(parent.root)
        self.window.grab_set()
        
        self.selected_account_id = None
        
        self.setup_ui()
        self.refresh_account_list()
    
    def setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="账号列表", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.account_listbox = tk.Listbox(list_frame, width=50, height=12)
        self.account_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.account_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.account_listbox.bind('<<ListboxSelect>>', self.on_account_select)
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="账号信息:").pack(anchor=tk.W)
        
        self.info_text = tk.Text(info_frame, height=4, width=70, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="🔧 添加账号", command=self.add_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ 编辑账号", command=self.edit_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除账号", command=self.delete_account).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ 设为活跃", command=self.set_active).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔑 重新登录", command=self.re_login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def refresh_account_list(self):
        """刷新账号列表"""
        self.account_listbox.delete(0, tk.END)
        
        accounts = self.account_manager.get_account_list()
        for acc in accounts:
            status = " ●" if acc['is_active'] else ""
            cookie_status = " ✅" if acc['has_cookie'] else " ❌"
            display_name = f"{acc['name']} ({acc['nickname'] or '未设置'}){status}{cookie_status}"
            self.account_listbox.insert(tk.END, display_name)
        
        self.clear_info()
    
    def clear_info(self):
        """清空信息面板"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        self.selected_account_id = None
    
    def on_account_select(self, event):
        """选择账号"""
        selection = self.account_listbox.curselection()
        if selection:
            index = selection[0]
            accounts = self.account_manager.get_account_list()
            if index < len(accounts):
                account = accounts[index]
                self.selected_account_id = account['id']
                self.show_account_info(account)
    
    def show_account_info(self, account):
        """显示账号信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info = f"账号ID: {account['id']}\n"
        info += f"账号名称: {account['name']}\n"
        info += f"抖音昵称: {account['nickname']}\n"
        info += f"状态: {'活跃' if account['is_active'] else '非活跃'}\n"
        info += f"Cookie状态: {'已配置' if account['has_cookie'] else '未配置'}\n"
        
        self.info_text.insert(tk.END, info)
        self.info_text.config(state=tk.DISABLED)
    
    def add_account(self):
        """添加账号"""
        name = simpledialog.askstring("添加账号", "请输入账号名称:")
        if not name or not name.strip():
            messagebox.showwarning("提示", "账号名称不能为空")
            return
        
        nickname = simpledialog.askstring("添加账号", "请输入抖音昵称（可选）:") or ""
        
        if self.account_manager.add_account(name.strip(), "", "", "", nickname.strip()):
            messagebox.showinfo("成功", "账号添加成功！\n请点击'重新登录'获取Cookie")
            self.refresh_account_list()
        else:
            messagebox.showerror("失败", "添加账号失败")
    
    def edit_account(self):
        """编辑账号"""
        if not self.selected_account_id:
            messagebox.showwarning("提示", "请先选择要编辑的账号")
            return
        
        account = self.account_manager.get_account(self.selected_account_id)
        if not account:
            return
        
        name = simpledialog.askstring("编辑账号", "请输入新的账号名称:", initialvalue=account.name)
        if name is None:
            return
        
        if not name.strip():
            messagebox.showwarning("提示", "账号名称不能为空")
            return
        
        nickname = simpledialog.askstring("编辑账号", "请输入抖音昵称:", initialvalue=account.nickname) or ""
        
        if self.account_manager.update_account(self.selected_account_id, name=name.strip(), nickname=nickname.strip()):
            messagebox.showinfo("成功", "账号信息更新成功")
            self.refresh_account_list()
        else:
            messagebox.showerror("失败", "更新账号失败")
    
    def delete_account(self):
        """删除账号"""
        if not self.selected_account_id:
            messagebox.showwarning("提示", "请先选择要删除的账号")
            return
        
        account = self.account_manager.get_account(self.selected_account_id)
        if not account:
            return
        
        if len(self.account_manager.accounts) <= 1:
            messagebox.showwarning("提示", "至少保留一个账号")
            return
        
        if messagebox.askyesno("确认", f"确定要删除账号 '{account.name}' 吗？"):
            if self.account_manager.delete_account(self.selected_account_id):
                messagebox.showinfo("成功", "账号已删除")
                self.refresh_account_list()
            else:
                messagebox.showerror("失败", "删除账号失败")
    
    def set_active(self):
        """设为活跃账号"""
        if not self.selected_account_id:
            messagebox.showwarning("提示", "请先选择账号")
            return
        
        if self.account_manager.set_active_account(self.selected_account_id):
            messagebox.showinfo("成功", "已切换活跃账号")
            self.parent.check_existing_cookie()
            self.refresh_account_list()
        else:
            messagebox.showerror("失败", "切换账号失败")
    
    def re_login(self):
        """重新登录获取Cookie"""
        if not self.selected_account_id:
            messagebox.showwarning("提示", "请先选择账号")
            return
        
        if self.parent.running:
            if not messagebox.askyesno("确认", "系统正在运行，登录需要停止系统，确定继续吗？"):
                return
            self.parent.stop_system()
        
        account = self.account_manager.get_account(self.selected_account_id)
        if not account:
            return
        
        self.parent.log(f"🔑 正在为账号 '{account.name}' 登录...")
        
        import subprocess
        import os
        from pathlib import Path
        
        login_bat = Path(__file__).parent / "start_login.bat"
        
        def login_callback():
            import time
            from dotenv import load_dotenv
            
            timeout = 180
            check_interval = 3
            elapsed = 0
            
            while elapsed < timeout:
                time.sleep(check_interval)
                elapsed += check_interval
                
                load_dotenv('.env', override=True)
                cookies_str = os.getenv('DY_COOKIES', '')
                web_protect_str = os.getenv('WEB_PROTECT', '')
                keys_str = os.getenv('KEYS', '')
                
                if len(cookies_str) > 100:
                    self.account_manager.update_account(
                        self.selected_account_id,
                        cookies=cookies_str,
                        web_protect=web_protect_str,
                        keys=keys_str
                    )
                    self.account_manager.set_active_account(self.selected_account_id)
                    self.parent.log(f"✅ 账号 '{account.name}' 登录成功")
                    self.parent.check_existing_cookie()
                    self.refresh_account_list()
                    return
                
                if elapsed % 30 == 0:
                    self.parent.log(f"⏳ 等待登录中... ({elapsed}秒)")
            
            self.parent.log("⚠️ 登录超时")
        
        import threading
        threading.Thread(target=login_callback, daemon=True).start()
        
        self.login_process = subprocess.Popen(
            str(login_bat),
            cwd=str(Path(__file__).parent),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        self.parent.log(f"🔄 登录进程已启动，请在新窗口中为账号 '{account.name}' 完成登录")