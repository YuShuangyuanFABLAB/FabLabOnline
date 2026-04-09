# -*- coding: utf-8 -*-
"""
字体管理模块

检测和安装 PPT 生成所需的字体，确保在任何 Windows 10 系统上都能正常显示。
"""

import sys
import os
import ctypes
from pathlib import Path
from typing import Dict, List, Tuple, Optional

if sys.platform == 'win32' and sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')


# PPT 模板中使用的字体
REQUIRED_FONTS = {
    # 字体名称: (字体文件名, 是否必须安装, 描述)
    "华文琥珀": ("STHUPO.TTF", True, "标题装饰字体"),
    "微软雅黑": ("msyh.ttc", False, "Windows 系统自带"),
    "等线": ("Deng.ttf", False, "Windows 10+ 自带"),
    "Bahnschrift": ("bahnschrift.ttf", False, "Windows 10+ 自带"),
}

# 需要打包的字体文件（非 Windows 自带的）
BUNDLED_FONTS = ["STHUPO.TTF"]


def get_fonts_dir() -> Path:
    """获取打包的字体目录"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / "fonts"
    else:
        return Path(__file__).parent.parent.parent / "fonts"


def get_system_fonts_dir() -> Path:
    """获取 Windows 系统字体目录"""
    return Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Fonts'


def is_font_installed(font_name: str) -> bool:
    """
    检查字体是否已安装在系统中

    Args:
        font_name: 字体名称（如 "华文琥珀"）

    Returns:
        bool: 是否已安装
    """
    try:
        import winreg

        # 字体名称映射（中文名 -> 英文名）
        font_name_map = {
            "华文琥珀": "STHUPO",
            "微软雅黑": "msyh",
            "等线": "Deng",
            "Bahnschrift": "bahnschrift",
        }

        font_file_prefix = font_name_map.get(font_name, font_name)

        # 方法1: 检查系统字体目录
        system_fonts_dir = get_system_fonts_dir()
        for font_file in system_fonts_dir.iterdir():
            if font_file.is_file():
                fname = font_file.name.lower()
                if font_file_prefix.lower() in fname:
                    return True

        # 方法2: 检查用户字体目录
        user_fonts_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Windows' / 'Fonts'
        if user_fonts_dir.exists():
            for font_file in user_fonts_dir.iterdir():
                if font_file.is_file():
                    fname = font_file.name.lower()
                    if font_file_prefix.lower() in fname:
                        return True

        # 方法3: 检查注册表（系统字体）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            )
            try:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if font_name in name or font_file_prefix.lower() in value.lower():
                            return True
                        i += 1
                    except OSError:
                        break
            finally:
                winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            pass

        # 方法4: 检查注册表（用户字体）
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            )
            try:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if font_name in name or font_file_prefix.lower() in value.lower():
                            return True
                        i += 1
                    except OSError:
                        break
            finally:
                winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            pass

        return False
    except Exception:
        return False


def install_font(font_path: Path) -> Tuple[bool, str]:
    """
    安装字体到系统（需要管理员权限）

    Args:
        font_path: 字体文件路径

    Returns:
        (是否成功, 消息)
    """
    try:
        if not font_path.exists():
            return False, f"字体文件不存在: {font_path}"

        # 目标路径
        system_fonts_dir = get_system_fonts_dir()
        target_path = system_fonts_dir / font_path.name

        # 如果已存在，跳过
        if target_path.exists():
            return True, f"字体已存在: {font_path.name}"

        # 复制字体文件
        import shutil
        shutil.copy2(font_path, target_path)

        # 注册字体
        # 使用 Windows API
        gdi32 = ctypes.windll.gdi32

        # AddFontResource 需要使用宽字符
        result = gdi32.AddFontResourceW(str(target_path))

        if result == 0:
            # 如果 AddFontResource 失败，尝试写入注册表
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
                0,
                winreg.KEY_SET_VALUE
            )
            try:
                # 获取字体显示名称
                font_display_name = font_path.stem + " (TrueType)"
                winreg.SetValueEx(key, font_display_name, 0, winreg.REG_SZ, font_path.name)
            finally:
                winreg.CloseKey(key)

            # 广播字体变更消息
            user32 = ctypes.windll.user32
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

        return True, f"字体安装成功: {font_path.name}"

    except PermissionError:
        return False, "权限不足，无法安装字体到系统目录"
    except Exception as e:
        return False, f"安装字体失败: {e}"


def install_font_user(font_path: Path) -> Tuple[bool, str]:
    """
    安装字体到当前用户（不需要管理员权限）

    Args:
        font_path: 字体文件路径

    Returns:
        (是否成功, 消息)
    """
    try:
        if not font_path.exists():
            return False, f"字体文件不存在: {font_path}"

        # 用户字体目录
        user_fonts_dir = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Windows' / 'Fonts'
        user_fonts_dir.mkdir(parents=True, exist_ok=True)

        target_path = user_fonts_dir / font_path.name

        # 如果已存在，跳过
        if target_path.exists():
            return True, f"字体已安装: {font_path.name}"

        # 复制字体文件
        import shutil
        shutil.copy2(font_path, target_path)

        # 注册到用户字体注册表
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts",
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            font_display_name = font_path.stem + " (TrueType)"
            winreg.SetValueEx(key, font_display_name, 0, winreg.REG_SZ, font_path.name)
        finally:
            winreg.CloseKey(key)

        # 广播字体变更消息
        user32 = ctypes.windll.user32
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        user32.SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)

        return True, f"字体安装成功（当前用户）: {font_path.name}"

    except Exception as e:
        return False, f"安装字体失败: {e}"


def check_and_install_fonts() -> Tuple[List[str], List[str]]:
    """
    检查并安装缺失的字体

    Returns:
        (已安装的字体列表, 警告消息列表)
    """
    installed = []
    warnings = []

    fonts_dir = get_fonts_dir()

    for font_name, (font_file, is_required, description) in REQUIRED_FONTS.items():
        if is_required:
            # 检查是否已安装
            if is_font_installed(font_name):
                continue

            # 尝试从打包目录安装
            font_path = fonts_dir / font_file
            if font_path.exists():
                # 先尝试用户级安装（不需要管理员权限）
                success, msg = install_font_user(font_path)
                if success:
                    installed.append(font_name)
                else:
                    # 如果用户级安装失败，尝试系统级
                    success, msg = install_font(font_path)
                    if success:
                        installed.append(font_name)
                    else:
                        warnings.append(f"无法安装字体 {font_name}: {msg}")
            else:
                warnings.append(f"字体文件缺失: {font_file}")

    return installed, warnings


def check_powerpoint() -> Tuple[bool, Optional[str]]:
    """
    检查 PowerPoint 是否已安装

    Returns:
        (是否安装, 版本信息)
    """
    try:
        import winreg

        # 检查 Office 安装
        office_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Office"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Office"),
        ]

        versions_found = []

        for hive, path in office_paths:
            try:
                key = winreg.OpenKey(hive, path)
                i = 0
                while True:
                    try:
                        version = winreg.EnumKey(key, i)
                        # 检查版本号（16.0 = 2016, 15.0 = 2013, etc.）
                        if version.replace('.', '').isdigit():
                            try:
                                ppt_key = winreg.OpenKey(key, f"{version}\\PowerPoint\\InstallRoot")
                                path_val, _ = winreg.QueryValueEx(ppt_key, "Path")
                                if path_val:
                                    version_names = {
                                        "16.0": "2016/2019/365",
                                        "15.0": "2013",
                                        "14.0": "2010",
                                        "12.0": "2007",
                                    }
                                    ver_name = version_names.get(version, version)
                                    versions_found.append(f"PowerPoint {ver_name}")
                                winreg.CloseKey(ppt_key)
                            except (FileNotFoundError, OSError):
                                pass
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except (FileNotFoundError, OSError):
                pass

        if versions_found:
            return True, ", ".join(versions_found)

        # 尝试 COM 检测
        try:
            import win32com.client
            ppt = win32com.client.Dispatch("PowerPoint.Application")
            version = ppt.Version
            ppt.Quit()
            version_names = {
                "16.0": "2016/2019/365",
                "15.0": "2013",
                "14.0": "2010",
            }
            ver_name = version_names.get(version, version)
            return True, f"PowerPoint {ver_name}"
        except Exception:
            pass

        return False, None

    except Exception:
        return False, None


def get_font_status() -> Dict[str, dict]:
    """
    获取所有字体的安装状态

    Returns:
        字体状态字典
    """
    status = {}
    for font_name, (font_file, is_required, description) in REQUIRED_FONTS.items():
        status[font_name] = {
            "installed": is_font_installed(font_name),
            "required": is_required,
            "bundled": font_file in BUNDLED_FONTS,
            "description": description,
            "file": font_file,
        }
    return status


if __name__ == "__main__":
    print("=" * 60)
    print("字体和依赖检查")
    print("=" * 60)

    # 检查字体状态
    print("\n字体状态:")
    for font_name, info in get_font_status().items():
        status_icon = "✓" if info["installed"] else "✗"
        required = "必需" if info["required"] else "系统自带"
        bundled = "已打包" if info["bundled"] else "-"
        print(f"  {status_icon} {font_name}: {required}, {bundled}")

    # 检查 PowerPoint
    print("\nPowerPoint 状态:")
    installed, version = check_powerpoint()
    if installed:
        print(f"  ✓ {version}")
    else:
        print("  ✗ 未检测到 PowerPoint")

    # 尝试安装缺失的字体
    print("\n检查并安装字体...")
    installed_fonts, warnings = check_and_install_fonts()
    if installed_fonts:
        print(f"  已安装: {', '.join(installed_fonts)}")
    if warnings:
        for w in warnings:
            print(f"  警告: {w}")
    if not installed_fonts and not warnings:
        print("  所有字体已就绪")
