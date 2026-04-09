# -*- coding: utf-8 -*-
"""
路径工具模块
提供兼容开发和打包环境的路径处理函数
"""

import sys
from pathlib import Path


def get_base_path() -> Path:
    """
    获取应用程序基础路径

    - 开发环境：返回项目根目录
    - 打包环境：返回 PyInstaller 临时目录 (_MEIPASS)

    Returns:
        Path: 基础路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    else:
        # 开发环境 - 从此文件向上两级到项目根目录
        return Path(__file__).parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径

    Args:
        relative_path: 相对于项目根目录的路径

    Returns:
        Path: 资源文件的绝对路径
    """
    return get_base_path() / relative_path


def get_app_dir() -> Path:
    """
    获取应用程序所在目录（用于写入配置、输出文件等）

    - 开发环境：返回项目根目录
    - 打包环境：返回 exe 文件所在目录

    Returns:
        Path: 应用程序目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后 - exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境 - 项目根目录
        return Path(__file__).parent.parent.parent


def get_config_dir() -> Path:
    """
    获取配置文件目录

    Returns:
        Path: 配置文件目录
    """
    return get_app_dir() / "config"


def get_output_dir() -> Path:
    """
    获取输出目录

    Returns:
        Path: 输出目录
    """
    return get_app_dir() / "output"


def get_templates_dir() -> Path:
    """
    获取模板文件目录

    Returns:
        Path: 模板文件目录
    """
    return get_base_path() / "templates"


def get_fonts_dir() -> Path:
    """
    获取字体文件目录

    Returns:
        Path: 字体文件目录
    """
    return get_base_path() / "fonts"
