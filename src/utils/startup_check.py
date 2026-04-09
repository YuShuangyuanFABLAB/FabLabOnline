"""
启动时检查脚本

在应用启动时自动检查关键方法是否存在，防止因提交遗漏导致的运行时错误。
同时检查字体和 PowerPoint 依赖。
"""

import sys
from typing import List, Tuple

if sys.platform == 'win32' and sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')


def check_method_exists(obj: object, method_name: str, obj_name: str = "object") -> Tuple[bool, str]:
    """
    检查对象是否具有指定方法

    Args:
        obj: 要检查的对象
        method_name: 方法名
        obj_name: 对象名称（用于错误消息）

    Returns:
        (是否存在, 错误消息)
    """
    if not hasattr(obj, method_name):
        return False, f"{obj_name}.{method_name}() 方法不存在"
    if not callable(getattr(obj, method_name)):
        return False, f"{obj_name}.{method_name} 不是可调用的方法"
    return True, ""


def run_startup_checks() -> Tuple[List[str], List[str], List[str]]:
    """
    运行所有启动检查

    Returns:
        (错误消息列表, 警告消息列表, 信息消息列表)
        错误列表为空表示可以启动
    """
    errors = []
    warnings = []
    info = []

    try:
        # 导入关键模块
        from src.core.config_manager import ConfigManager

        # 创建实例
        config_manager = ConfigManager()

        # ============================================
        # 检查 ConfigManager 的关键方法
        # ============================================
        config_manager_methods = [
            # 班级管理
            "get_classes",
            "add_class",
            "remove_class",
            "get_next_lesson_number",
            "set_next_lesson_number",

            # 学员管理
            "get_students_by_class",
            "add_student",
            "remove_student",

            # 学员独立课时编号（关键！曾经遗漏）
            "get_student_next_lesson_number",
            "set_student_next_lesson_number",

            # 评价持久化
            "get_student_last_evaluation",
            "save_student_last_evaluation",

            # 配置
            "get_course_series",
            "get_default_other_notes",
        ]

        for method_name in config_manager_methods:
            exists, error = check_method_exists(config_manager, method_name, "ConfigManager")
            if not exists:
                errors.append(error)

    except ImportError as e:
        errors.append(f"导入模块失败: {e}")
    except Exception as e:
        errors.append(f"启动检查异常: {e}")

    # ============================================
    # 检查 PowerPoint
    # ============================================
    try:
        from src.utils.font_manager import check_powerpoint
        ppt_installed, ppt_version = check_powerpoint()
        if ppt_installed:
            info.append(f"检测到 {ppt_version}")
        else:
            errors.append("未检测到 PowerPoint，请安装 Microsoft PowerPoint 2016 或更高版本")
    except Exception as e:
        warnings.append(f"PowerPoint 检测失败: {e}")

    # ============================================
    # 检查并安装字体
    # ============================================
    try:
        from src.utils.font_manager import check_and_install_fonts, get_font_status
        installed_fonts, font_warnings = check_and_install_fonts()

        if installed_fonts:
            info.append(f"已自动安装字体: {', '.join(installed_fonts)}")

        for w in font_warnings:
            warnings.append(w)

        # 检查必需字体状态
        font_status = get_font_status()
        for font_name, status in font_status.items():
            if status["required"] and not status["installed"]:
                warnings.append(f"必需字体 '{font_name}' 未安装，PPT 可能显示异常")

    except Exception as e:
        warnings.append(f"字体检查失败: {e}")

    return errors, warnings, info


def startup_check_dialog():
    """
    启动检查并显示对话框（如果发现问题）

    Returns:
        True 表示检查通过，False 表示发现问题
    """
    errors, warnings, info = run_startup_checks()

    # 如果有错误，显示错误对话框
    if errors:
        error_msg = "\n".join([f"  ❌ {e}" for e in errors])

        # 尝试使用 Qt 对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("启动检查失败")
            msg.setText("检测到问题，应用无法启动！")
            msg.setInformativeText(
                f"以下问题需要解决：\n\n{error_msg}\n\n"
                "请确保已安装 Microsoft PowerPoint 2016 或更高版本。"
            )
            msg.exec_()

        except ImportError:
            # 如果 PyQt5 不可用，使用控制台输出
            print("\n" + "=" * 60)
            print("  ❌ 启动检查失败！")
            print("=" * 60)
            print("\n以下问题需要解决：")
            print(error_msg)
            print("\n请确保已安装 Microsoft PowerPoint 2016 或更高版本。")
            print("=" * 60 + "\n")

        return False

    # 如果有警告或信息，显示提示
    if warnings or info:
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            # 构建消息
            msg_parts = []

            if info:
                msg_parts.append("检测结果：")
                msg_parts.extend([f"  ✓ {i}" for i in info])

            if warnings:
                if msg_parts:
                    msg_parts.append("")
                msg_parts.append("警告：")
                msg_parts.extend([f"  ⚠ {w}" for w in warnings])

            msg_text = "\n".join(msg_parts)

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning if warnings else QMessageBox.Information)
            msg.setWindowTitle("启动检查")
            msg.setText("应用已准备就绪")
            msg.setInformativeText(msg_text)
            msg.exec_()

        except ImportError:
            print("\n" + "=" * 60)
            print("  启动检查")
            print("=" * 60)
            if info:
                for i in info:
                    print(f"  ✓ {i}")
            if warnings:
                for w in warnings:
                    print(f"  ⚠ {w}")
            print("=" * 60 + "\n")

    return True


if __name__ == "__main__":
    # 命令行测试
    errors, warnings, info = run_startup_checks()

    print("\n" + "=" * 60)
    print("启动检查结果")
    print("=" * 60)

    if info:
        print("\n信息:")
        for i in info:
            print(f"  ✓ {i}")

    if warnings:
        print("\n警告:")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        print("\n错误:")
        for e in errors:
            print(f"  ✗ {e}")
        print("\n❌ 启动检查失败")
        sys.exit(1)
    else:
        print("\n✅ 启动检查通过")
        sys.exit(0)
