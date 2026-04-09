#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法贝实验室课程反馈助手
主入口文件
"""

import sys
import os
from pathlib import Path


def get_app_dir():
    """获取应用程序目录，兼容开发和打包环境"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys.executable).parent
    else:
        # 开发环境
        return Path(__file__).parent


# 设置工作目录
os.chdir(get_app_dir())

# 配置控制台编码（仅在控制台存在时）
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# 启动日志（仅在有控制台时）
if sys.stdout is not None:
    print(f"[INFO] 应用启动 - 工作目录: {os.getcwd()}")
    print(f"[INFO] Python 版本: {sys.version}")


def main():
    """主函数"""
    # 初始化 SDK 集成（登录认证）
    sdk_client = None
    try:
        from fablab_sdk.client import FablabClient
        import platformdirs

        app_key = os.environ.get("FABLAB_APP_KEY", "ppt-generator")
        server_url = os.environ.get("FABLAB_SERVER_URL", "http://localhost:8000")
        sdk_client = FablabClient(app_key=app_key, server_url=server_url)
    except ImportError:
        pass  # SDK 未安装，离线模式
    except Exception as e:
        if sys.stdout is not None:
            print(f"[WARN] SDK 初始化失败: {e}")

    # 检查认证状态
    if sdk_client is not None:
        try:
            from src.core.sdk_integration import SdkIntegration

            cache_dir = platformdirs.user_cache_dir("fablab-ppt")
            integration = SdkIntegration(client=sdk_client, cache_dir=cache_dir)
            if not integration.check_auth():
                # 弹出登录对话框
                from PyQt5.QtWidgets import QApplication
                app = QApplication.instance()
                if app is None:
                    app = QApplication(sys.argv)
                from src.ui.dialogs.login_dialog import LoginDialog
                dialog = LoginDialog(sdk_client)
                if dialog.exec_() != dialog.Accepted:
                    # 登录取消，尝试离线缓存
                    if not integration.check_auth():
                        sys.exit(0)
        except Exception as e:
            if sys.stdout is not None:
                print(f"[WARN] 认证检查失败，继续离线模式: {e}")

    # 启动时检查关键方法是否存在（防止提交遗漏）
    from src.utils.startup_check import startup_check_dialog
    if not startup_check_dialog():
        sys.exit(1)

    from src.ui.main_window import run_app
    run_app(client=sdk_client)


if __name__ == "__main__":
    main()
