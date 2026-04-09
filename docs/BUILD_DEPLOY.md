# 打包部署

本文档描述如何将应用打包为 Windows 可执行文件。

## 概述

- **打包工具**：PyInstaller
- **输出格式**：Windows .exe
- **目标平台**：Windows 10+

## 打包脚本

位于 `build.py`。

### 运行打包

```bash
python build.py
```

### 输出结构

```
dist/
├── 法贝实验室课程反馈助手/         # 可执行文件目录
│   ├── 法贝实验室课程反馈助手.exe  # 主程序
│   ├── templates/                  # 模板文件
│   ├── config/                     # 配置文件
│   ├── fonts/                      # 字体文件
│   └── ... (其他依赖)
│
└── 法贝实验室课程反馈助手_便携版.zip  # 便携版压缩包
```

## 打包配置

### 包含的数据文件

```python
DATA_FILES = [
    ("templates", "templates"),  # PPT 模板
    ("config", "config"),        # 配置文件
    ("fonts", "fonts"),          # 字体文件
]
```

### 隐藏导入

```python
HIDDEN_IMPORTS = [
    "lxml.etree",
    "lxml._elementpath",
    "PIL._tkinter_finder",
]
```

### PyInstaller 参数

```python
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "法贝实验室课程反馈助手",
    "--windowed",      # 不显示控制台
    "--noconfirm",     # 不询问确认
    "--clean",         # 清理临时文件
    # ... 数据文件和隐藏导入
    "main.py"
]
```

## 路径适配

### 开发环境 vs 打包环境

```python
def get_base_path() -> Path:
    """获取应用程序基础路径（用于读取资源）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent

def get_app_dir() -> Path:
    """获取应用程序所在目录（用于写入配置）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后 - exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境 - 项目根目录
        return Path(__file__).parent
```

### 资源路径 vs 配置路径

| 类型 | 开发环境 | 打包环境 |
|------|----------|----------|
| 模板文件 | 项目根目录/templates | _MEIPASS/templates |
| 配置文件 | 项目根目录/config | exe 所在目录/config |
| 字体文件 | 项目根目录/fonts | _MEIPASS/fonts |

## 字体处理

### 字体检测

程序启动时检测必需字体：

```python
def check_required_fonts():
    """检查必需字体"""
    required = ["华文琥珀"]
    missing = []

    # Windows 字体目录
    fonts_dir = Path("C:/Windows/Fonts")

    for font_name in required:
        # 检查系统字体
        if not is_font_in_system(font_name):
            # 检查本地 fonts 目录
            local_font = get_base_path() / "fonts" / f"{font_name}.ttf"
            if not local_font.exists():
                missing.append(font_name)

    return missing
```

### 字体安装提示

如果缺少字体，显示安装提示对话框：

```python
def prompt_font_installation(missing_fonts):
    """提示用户安装字体"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("字体缺失")
    msg.setText(f"检测到以下字体未安装：{', '.join(missing_fonts)}")
    msg.setInformativeText("建议安装字体以获得最佳显示效果。\n\n是否打开字体文件夹？")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    if msg.exec_() == QMessageBox.Yes:
        # 打开字体文件夹
        fonts_dir = get_base_path() / "fonts"
        os.startfile(str(fonts_dir))
```

## 便携版结构

### 目录结构

```
法贝实验室课程反馈助手_便携版/
├── 法贝实验室课程反馈助手/
│   ├── 法贝实验室课程反馈助手.exe
│   ├── templates/
│   ├── config/
│   ├── fonts/
│   └── ...
│
├── output/                  # 输出目录
│
└── 使用说明.txt             # 使用说明
```

### 使用说明内容

```
# 法贝实验室课程反馈助手

## 使用说明

1. 双击运行 `法贝实验室课程反馈助手.exe`
2. 填写课程信息
3. 点击"生成PPT"按钮

## 目录说明

- `法贝实验室课程反馈助手/` - 程序目录（包含模板和字体）
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
```

## 构建流程

### 1. 检查 PyInstaller

```python
def check_pyinstaller():
    try:
        import PyInstaller
        return True
    except ImportError:
        # 自动安装
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pyinstaller"
        ])
        return True
```

### 2. 清理旧文件

```python
def clean_build():
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)

    # 删除 .spec 文件
    for spec_file in ROOT_DIR.glob("*.spec"):
        spec_file.unlink()
```

### 3. 构建可执行文件

```python
def build_exe():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",
        "--noconfirm",
        "--clean",
    ]

    # 添加数据文件
    for src, dst in DATA_FILES:
        cmd.extend(["--add-data", f"{src};{dst}"])

    # 添加隐藏导入
    for hidden in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden])

    cmd.append("main.py")

    subprocess.run(cmd)
```

### 4. 创建便携版

```python
def create_portable_package():
    # 复制可执行文件目录
    # 创建输出目录
    # 创建说明文件
    # 打包为 zip
    shutil.make_archive(output_name, "zip", output_dir)
```

## 发布检查清单

- [ ] 更新版本号
- [ ] 测试所有功能
- [ ] 检查模板文件是否完整
- [ ] 检查字体文件是否完整
- [ ] 在干净的 Windows 系统上测试
- [ ] 检查生成的 PPT 是否正确
- [ ] 验证配置文件读写正常

## 常见问题

### 打包后运行报错

1. 检查隐藏导入是否完整
2. 检查数据文件路径是否正确
3. 使用 `--debug all` 参数重新打包查看详细信息

### 找不到模板文件

确保使用 `get_base_path()` 获取资源路径：

```python
# 正确
template_path = get_base_path() / "templates" / "课程反馈.pptx"

# 错误（打包后会找不到）
template_path = "templates/课程反馈.pptx"
```

### 配置无法保存

确保使用 `get_app_dir()` 获取配置路径：

```python
# 正确
config_dir = get_app_dir() / "config"

# 错误（打包后可能无写入权限）
config_dir = get_base_path() / "config"
```

## 相关文档

- [项目概述](PROJECT_OVERVIEW.md) - 目录结构
- [经验总结](EXPERIENCE_NOTES.md) - 打包常见问题
