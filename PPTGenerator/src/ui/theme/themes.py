# -*- coding: utf-8 -*-
"""
主题颜色定义
定义日间模式和夜间模式的颜色方案
"""

from dataclasses import dataclass


@dataclass
class ThemeColors:
    """主题颜色基类"""

    # 背景色
    background_primary: str = "#ffffff"      # 主背景
    background_secondary: str = "#f5f5f5"    # 次背景
    background_tertiary: str = "#e8e8e8"     # 三级背景

    # 文字色
    text_primary: str = "#212121"            # 主文字
    text_secondary: str = "#666666"          # 次文字
    text_hint: str = "#999999"               # 提示文字

    # 主色调
    primary: str = "#0078d4"                 # 主色
    primary_hover: str = "#106ebe"           # 主色悬停
    primary_pressed: str = "#005a9e"         # 主色按下

    # 成功色
    success: str = "#4caf50"                 # 成功色
    success_hover: str = "#66bb6a"           # 成功悬停
    success_background: str = "#e8f4e8"      # 成功背景
    success_border: str = "#4caf50"          # 成功边框
    success_text: str = "#2e7d32"            # 成功文字

    # 错误色
    error: str = "#f44336"                   # 错误色
    error_hover: str = "#ef5350"             # 错误悬停
    error_background: str = "#ffebee"        # 错误背景
    error_border: str = "#f44336"            # 错误边框
    error_text: str = "#c62828"              # 错误文字

    # 边框色
    border_normal: str = "#cccccc"           # 普通边框
    border_hover: str = "#999999"            # 悬停边框
    border_focused: str = "#0078d4"          # 聚焦边框

    # 按钮色
    button_normal: str = "#f0f0f0"           # 按钮背景
    button_checked: str = "#0078d4"          # 选中按钮
    button_disabled: str = "#e0e0e0"         # 禁用按钮
    button_disabled_text: str = "#999999"    # 禁用文字

    # 滚动区域
    scroll_area_background: str = "transparent"

    # 图片预览
    preview_background: str = "#f0f0f0"
    preview_border: str = "#cccccc"
    preview_border_hover: str = "#0078d4"


@dataclass
class LightTheme(ThemeColors):
    """日间主题"""
    pass  # 使用默认值


@dataclass
class DarkTheme(ThemeColors):
    """夜间主题"""

    # 背景色
    background_primary: str = "#1e1e1e"
    background_secondary: str = "#2d2d2d"
    background_tertiary: str = "#3d3d3d"

    # 文字色
    text_primary: str = "#e0e0e0"
    text_secondary: str = "#b0b0b0"
    text_hint: str = "#707070"

    # 主色调
    primary: str = "#3da5f4"
    primary_hover: str = "#5cb5f8"
    primary_pressed: str = "#2d8ed4"

    # 成功色
    success: str = "#66bb6a"
    success_hover: str = "#81c784"
    success_background: str = "#2e4a2e"
    success_border: str = "#66bb6a"
    success_text: str = "#a5d6a7"

    # 错误色
    error: str = "#ef5350"
    error_hover: str = "#e57373"
    error_background: str = "#4a2e2e"
    error_border: str = "#ef5350"
    error_text: str = "#ef9a9a"

    # 边框色
    border_normal: str = "#4a4a4a"
    border_hover: str = "#6a6a6a"
    border_focused: str = "#3da5f4"

    # 按钮色
    button_normal: str = "#3d3d3d"
    button_checked: str = "#3da5f4"
    button_disabled: str = "#2d2d2d"
    button_disabled_text: str = "#707070"

    # 滚动区域
    scroll_area_background: str = "#2d2d2d"

    # 图片预览
    preview_background: str = "#2d2d2d"
    preview_border: str = "#4a4a4a"
    preview_border_hover: str = "#3da5f4"
