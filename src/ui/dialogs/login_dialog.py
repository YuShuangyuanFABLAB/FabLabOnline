# -*- coding: utf-8 -*-
"""
微信扫码登录对话框
使用 FabLab SDK 进行扫码登录
"""

import logging
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

logger = logging.getLogger(__name__)


class PollThread(QThread):
    """后台轮询扫码状态的线程"""
    status_result = pyqtSignal(str, str, str)  # status, token, user_id

    def __init__(self, client, state: str):
        super().__init__()
        self.client = client
        self.state = state
        self._running = True

    def run(self):
        import asyncio
        while self._running:
            try:
                result = asyncio.run(
                    self.client.auth.poll_qr_status(self.state)
                )
                status = result.get("status", "pending")
                if status == "authenticated":
                    token = result.get("token", "")
                    user_id = result.get("user_id", "")
                    self.status_result.emit(status, token, user_id)
                    return
                elif status == "expired":
                    self.status_result.emit(status, "", "")
                    return
            except Exception as e:
                logger.warning(f"轮询扫码状态失败: {e}")
            self.msleep(2000)  # 每 2 秒轮询一次

    def stop(self):
        self._running = False
        self.wait(3000)


class LoginDialog(QDialog):
    """微信扫码登录对话框"""

    login_success = pyqtSignal(str, str)  # user_id, token

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.poll_thread: Optional[PollThread] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("法贝实验室 — 登录")
        self.setFixedSize(400, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("请使用微信扫码登录")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 二维码显示区域
        self.qr_label = QLabel("正在获取二维码...")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setStyleSheet(
            "border: 1px solid #ddd; border-radius: 8px; "
            "background: #f5f5f5; font-size: 14px; color: #666;"
        )
        layout.addWidget(self.qr_label)

        # 状态提示
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 按钮行
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新二维码")
        self.refresh_btn.clicked.connect(self._load_qrcode)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def showEvent(self, event):
        """对话框显示时自动加载二维码"""
        super().showEvent(event)
        self._load_qrcode()

    def _load_qrcode(self):
        """加载并显示二维码"""
        self.qr_label.setText("正在获取二维码...")
        self.status_label.setText("")

        try:
            qr_url = self.client.auth.get_qrcode_url()
            if not qr_url:
                self.qr_label.setText("获取二维码失败")
                return

            # 下载二维码图片
            import requests
            response = requests.get(qr_url, timeout=10)
            if response.status_code == 200:
                img = QImage()
                img.loadFromData(response.content)
                if not img.isNull():
                    pixmap = QPixmap.fromImage(img)
                    scaled = pixmap.scaled(
                        280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.qr_label.setPixmap(scaled)
                    self.status_label.setText("请使用微信扫描二维码")
                    self._start_polling(qr_url)
                else:
                    self.qr_label.setText("二维码图片加载失败")
            else:
                self.qr_label.setText(f"获取二维码失败 (HTTP {response.status_code})")

        except Exception as e:
            logger.error(f"加载二维码失败: {e}")
            self.qr_label.setText(f"加载失败: {e}")

    def _start_polling(self, qr_url: str):
        """启动扫码状态轮询"""
        if self.poll_thread and self.poll_thread.isRunning():
            self.poll_thread.stop()

        # 从 URL 中提取 state 参数
        import urllib.parse
        parsed = urllib.parse.urlparse(qr_url)
        params = urllib.parse.parse_qs(parsed.query)
        state = params.get("state", [""])[0]

        if not state:
            # 如果 URL 中没有 state，使用默认值
            state = "default"

        self.poll_thread = PollThread(self.client, state)
        self.poll_thread.status_result.connect(self._on_poll_result)
        self.poll_thread.start()

    def _on_poll_result(self, status: str, token: str, user_id: str):
        """轮询结果回调"""
        if status == "authenticated":
            self.status_label.setText("登录成功！")
            self.status_label.setStyleSheet("color: green; font-size: 14px;")
            self.login_success.emit(user_id, token)

            # 更新 SDK token
            from src.core.sdk_integration import SdkIntegration
            import platformdirs
            cache_dir = platformdirs.user_cache_dir("fablab-ppt")
            integration = SdkIntegration(client=self.client, cache_dir=cache_dir)
            integration.on_login_success(user_id, token)

            QTimer.singleShot(500, self.accept)

        elif status == "expired":
            self.qr_label.setText("二维码已过期\n点击「刷新二维码」重新获取")
            self.status_label.setText("二维码已过期")

    def closeEvent(self, event):
        """关闭时停止轮询线程"""
        if self.poll_thread and self.poll_thread.isRunning():
            self.poll_thread.stop()
        super().closeEvent(event)
