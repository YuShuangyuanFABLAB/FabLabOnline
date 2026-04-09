# -*- coding: utf-8 -*-
"""
打包发布脚本 (F027)
使用PyInstaller将程序打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("法贝实验室课程反馈助手 - 打包脚本")
print("=" * 60)
print()

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 打包配置
APP_NAME = "法贝实验室课程反馈助手"
MAIN_SCRIPT = "main.py"
ICON_FILE = None  # 如果有图标文件，设置路径

# 需要包含的数据文件
DATA_FILES = [
    ("templates", "templates"),
    ("config", "config"),
    ("fonts", "fonts"),  # 包含所有字体（华文琥珀等）
]

# 需要包含的隐藏导入
HIDDEN_IMPORTS = [
    "lxml.etree",
    "lxml._elementpath",
    "PIL._tkinter_finder",
    "winreg",  # 字体检测需要
    "win32com.client",  # PowerPoint COM 需要
]


def check_pyinstaller():
    """检查PyInstaller是否安装"""
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller",
                 "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
                check=True
            )
            print("PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("PyInstaller 安装失败")
            return False


def clean_build():
    """清理构建目录"""
    print("清理构建目录...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  已删除: {dir_name}")
            except PermissionError:
                print(f"  警告: 无法删除 {dir_name}（文件被占用），跳过清理")

    # 删除spec文件
    for spec_file in ROOT_DIR.glob("*.spec"):
        try:
            spec_file.unlink()
            print(f"  已删除: {spec_file.name}")
        except PermissionError:
            print(f"  警告: 无法删除 {spec_file.name}")


def build_exe():
    """构建可执行文件"""
    print()
    print("构建可执行文件...")

    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",  # 不显示控制台
        "--noconfirm",  # 不询问确认
        "--clean",  # 清理临时文件
    ]

    # 添加图标
    if ICON_FILE and Path(ICON_FILE).exists():
        cmd.extend(["--icon", ICON_FILE])

    # 添加数据文件
    for src, dst in DATA_FILES:
        src_path = ROOT_DIR / src
        if src_path.exists():
            cmd.extend(["--add-data", f"{src};{dst}"])

    # 添加隐藏导入
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])

    # 添加主脚本
    cmd.append(str(ROOT_DIR / MAIN_SCRIPT))

    print(f"执行命令: {' '.join(cmd[:10])}...")

    # 切换到项目目录
    os.chdir(ROOT_DIR)

    # 执行打包
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("构建成功!")
        return True
    else:
        print("构建失败!")
        print("错误信息:")
        print(result.stderr)
        return False


def create_portable_package():
    """创建便携版压缩包"""
    print()
    print("创建便携版...")

    dist_dir = ROOT_DIR / "dist" / APP_NAME
    if not dist_dir.exists():
        print("找不到构建输出目录")
        return False

    # 创建输出目录结构
    output_dir = ROOT_DIR / "dist" / f"{APP_NAME}_便携版"
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
        except PermissionError:
            print("  警告: 旧便携版目录被占用，尝试创建新目录...")
            # 尝试使用新名称
            import time
            output_dir = ROOT_DIR / "dist" / f"{APP_NAME}_便携版_{int(time.time())}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 复制可执行文件目录
    exe_dir = output_dir / APP_NAME
    shutil.copytree(dist_dir, exe_dir)

    # 创建输出目录
    (output_dir / "output").mkdir(exist_ok=True)

    # 创建说明文件
    readme_content = f"""# {APP_NAME}

## 使用说明

1. 双击运行 `{APP_NAME}.exe`
2. 填写课程信息
3. 点击"生成PPT"按钮

## 目录说明

- `{APP_NAME}/` - 程序目录（包含模板和字体）
- `output/` - 输出目录（生成的PPT保存在这里）

## 系统要求

- Windows 10 或更高版本
- 不需要安装Python环境

## 字体说明

本程序使用"华文琥珀"字体作为标题装饰。如果系统缺少此字体：
- 首次运行时会提示安装
- 也可以手动双击 fonts 文件夹中的字体文件进行安装

## 注意事项

- 请勿删除 templates 文件夹中的模板文件
- 请勿删除 fonts 文件夹中的字体文件
- 首次运行可能需要几秒钟初始化
"""

    with open(output_dir / "使用说明.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 创建压缩包
    shutil.make_archive(
        str(ROOT_DIR / "dist" / f"{APP_NAME}_便携版"),
        "zip",
        output_dir.parent,
        output_dir.name
    )

    print(f"便携版已创建: dist/{APP_NAME}_便携版.zip")
    return True


def main():
    """主函数"""
    # 检查PyInstaller
    if not check_pyinstaller():
        print()
        print("请手动安装 PyInstaller: pip install pyinstaller")
        return 1

    # 清理旧文件
    clean_build()

    # 构建
    if not build_exe():
        return 1

    # 创建便携版
    create_portable_package()

    print()
    print("=" * 60)
    print("打包完成!")
    print("=" * 60)
    print()
    print(f"可执行文件位置: dist/{APP_NAME}/{APP_NAME}.exe")
    print(f"便携版位置: dist/{APP_NAME}_便携版.zip")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
