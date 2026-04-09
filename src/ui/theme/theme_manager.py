# -*- coding: utf-8 -*-
"""
主题管理器
管理应用程序的主题切换和通知
"""

from PyQt5.QtCore import QObject, pyqtSignal
from .themes import ThemeColors, LightTheme, DarkTheme


class ThemeManager(QObject):
    """
    主题管理器（单例模式）

    负责管理当前主题状态，提供主题切换信号
    """

    _instance = None

    # 主题改变信号
    theme_changed = pyqtSignal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._current_theme = "light"
        self._themes = {
            "light": LightTheme(),
            "dark": DarkTheme()
        }

    @classmethod
    def instance(cls) -> 'ThemeManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_current_theme(self) -> str:
        """获取当前主题名称"""
        return self._current_theme

    def get_colors(self) -> ThemeColors:
        """获取当前主题的颜色配置"""
        return self._themes[self._current_theme]

    def is_dark_mode(self) -> bool:
        """是否为夜间模式"""
        return self._current_theme == "dark"

    def set_theme(self, theme_name: str):
        """
        设置主题

        Args:
            theme_name: "light" 或 "dark"
        """
        if theme_name not in self._themes:
            return

        self._current_theme = theme_name
        self.theme_changed.emit(theme_name)  # 始终发射信号，确保样式更新

    def toggle_theme(self) -> str:
        """
        切换主题

        Returns:
            切换后的主题名称
        """
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme
