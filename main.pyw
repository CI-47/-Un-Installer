from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Optional, Callable
from subprocess import run, CalledProcessError
import sys
import webbrowser
from threading import Thread


class PipCommandHandler:
    """处理所有pip命令的执行和源管理"""
    
    SOURCES = {
        '阿里云  Aliyun': 'https://mirrors.aliyun.com/pypi/simple',
        'PyPI': 'https://pypi.org/simple',
        '清华大学  Tsinghua University': 'https://pypi.tuna.tsinghua.edu.cn/simple'
    }

    def __init__(self):
        self.pip_base = [sys.executable, "-m", "pip"]

    def execute_command(self, command: List[str]) -> Dict[str, str]:
        """执行命令并返回标准化结果"""
        try:
            result = run(command, capture_output=True, text=True, check=True)
            return {"success": True, "output": result.stdout}
        except CalledProcessError as e:
            return {"success": False, "output": e.stderr}

    def get_install_command(self, package: str, source: str) -> List[str]:
        """构建安装命令"""
        return self.pip_base + ["install", "-i", source, package]

    def get_upgrade_command(self, package: str, source: str) -> List[str]:
        """构建升级命令"""
        return self.pip_base + ["install", "--upgrade", "-i", source, package]

    def get_uninstall_command(self, package: str) -> List[str]:
        """构建卸载命令"""
        return self.pip_base + ["uninstall", "-y", package]

    @property
    def source_names(self) -> Tuple[str, ...]:
        """获取所有源名称"""
        return tuple(self.SOURCES.keys())

    def get_source_url(self, name: str) -> str:
        """根据名称获取源URL"""
        return self.SOURCES[name]


class AsyncTaskHandler:
    """处理异步任务调度和线程管理"""
    
    def __init__(self, ui_callback: Callable[[Dict], None]):
        self.running = False
        self.ui_callback = ui_callback

    def execute_async(self, command: List[str]) -> None:
        """异步执行命令并回调UI更新"""
        if self.running:
            messagebox.showwarning("警告", "当前有其他任务正在执行")
            return

        self.running = True

        def task():
            result = run(command, capture_output=True, text=True)
            self.ui_callback({
                "success": result.returncode == 0,
                "output": result.stdout or result.stderr
            })
            self.running = False

        Thread(target=task, daemon=True).start()


class MainUI:
    """主界面UI组件管理"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("-Un-Installer")
        self.root.resizable(False, False)
        
        self.pip_handler = PipCommandHandler()
        self.task_handler = AsyncTaskHandler(self.update_ui)
        
        # 主控件
        self.package_entry = ttk.Entry(width=50)
        self.source_combobox = ttk.Combobox(width=48, state="readonly")
        self.action_buttons: Dict[str, ttk.Button] = {}

        self.setup_ui()

    def setup_ui(self) -> None:
        """初始化界面布局"""
        # 输入区域
        ttk.Label(self.root, text="需要装卸的包  Name of Package:").grid(row=0, column=0, padx=5, pady=5)
        self.package_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 源选择
        ttk.Label(self.root, text="下载源  Source:").grid(row=1, column=0, padx=5, pady=5)
        self.source_combobox["values"] = self.pip_handler.source_names
        self.source_combobox.current(0)
        self.source_combobox.grid(row=1, column=1, padx=5, pady=5)

        # 操作按钮
        buttons = [
            ("安装  Install", self.on_install),
            ("升级  Upgrade", self.on_upgrade),
            ("卸载  Uninstall", self.on_uninstall),
            ("包详情  Details", self.show_details),
            ("关于  About", self.show_about)
        ]
        
        for row, (text, command) in enumerate(buttons, start=2):
            btn = ttk.Button(self.root, text=text, command=command, width=68)
            btn.grid(row=row, columnspan=2, padx=5, pady=2)
            self.action_buttons[text.split()[0]] = btn

    def update_ui(self, result: Dict) -> None:
        """更新UI状态"""
        if result["success"]:
            messagebox.showinfo("操作成功", result["output"])
        else:
            messagebox.showerror("操作失败", result["output"])

    def get_current_package(self) -> str:
        """获取当前输入的包名"""
        return self.package_entry.get().strip()

    def on_install(self) -> None:
        """安装按钮回调"""
        if package := self.get_current_package():
            source = self.pip_handler.get_source_url(self.source_combobox.get())
            self.task_handler.execute_async(
                self.pip_handler.get_install_command(package, source)
        else:
            messagebox.showerror("错误", "请输入包名")

    def on_upgrade(self) -> None:
        """升级按钮回调"""
        if package := self.get_current_package():
            source = self.pip_handler.get_source_url(self.source_combobox.get())
            self.task_handler.execute_async(
                self.pip_handler.get_upgrade_command(package, source
