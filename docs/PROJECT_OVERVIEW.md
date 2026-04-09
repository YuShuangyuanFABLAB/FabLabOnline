# 项目概述

## 项目简介

**法贝实验室课程反馈助手** 是一个用于自动生成课程反馈 PPT 的桌面应用程序，适用于教育培训机构快速生成标准化、个性化的课程反馈报告。

### 核心功能

- 班级与学员管理
- 课程信息录入
- 课堂评价系统（12项评价）
- 图片上传与管理
- PPT 自动生成

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 编程语言 | Python | 3.14+ |
| GUI 框架 | PyQt5 | - |
| PPT 处理 | python-pptx | - |
| 图像处理 | Pillow (PIL) | - |
| 打包工具 | PyInstaller | - |

## 目录结构

```
课程反馈PPT生成器/
├── main.py                    # 主入口文件
├── build.py                   # 打包脚本
├── requirements.txt           # 依赖清单
├── README.md                  # 项目说明
│
├── config/                    # 配置文件目录
│   ├── settings.json          # 应用设置（运行时生成）
│   └── colors.json            # 颜色配置
│
├── templates/                 # PPT 模板目录
│   └── 课程反馈.pptx          # 主模板文件
│
├── fonts/                     # 字体文件目录
│   └── STHUPO.TTF             # 华文琥珀字体
│
├── output/                    # 默认输出目录
│
├── src/                       # 源代码目录
│   ├── __init__.py
│   │
│   ├── core/                  # 核心逻辑模块
│   │   ├── __init__.py
│   │   ├── models.py          # 数据模型定义
│   │   ├── config_manager.py  # 配置管理器
│   │   ├── ppt_generator.py   # PPT 生成器
│   │   ├── content_filler.py  # 内容填充器
│   │   ├── batch_generator.py # 批量生成器
│   │   ├── image_processor.py # 图片处理器
│   │   ├── checkbox_handler.py# 复选框处理器
│   │   ├── excel_importer.py  # Excel 导入器
│   │   ├── form_serializer.py # 表单序列化
│   │   ├── layout_manager.py  # 布局管理
│   │   ├── slide_content_manager.py  # 幻灯片内容管理
│   │   └── text_formatter.py  # 文本格式化
│   │
│   ├── ui/                    # 用户界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py     # 主窗口
│   │   │
│   │   ├── widgets/           # UI 组件
│   │   │   ├── __init__.py
│   │   │   ├── course_info.py      # 课程信息组件
│   │   │   ├── evaluation.py       # 评价组件
│   │   │   ├── image_upload.py     # 图片上传组件
│   │   │   ├── rich_text_editor.py # 富文本编辑器
│   │   │   ├── series_selector.py  # 系列选择器
│   │   │   ├── class_selector.py   # 班级选择器
│   │   │   ├── student_manager.py  # 学员管理器
│   │   │   ├── student_tab_bar.py  # 学员标签栏
│   │   │   └── layout_selector.py  # 布局选择器
│   │   │
│   │   └── dialogs/           # 对话框
│   │       ├── batch_progress_dialog.py  # 批量进度对话框
│   │       ├── crop_dialog.py            # 图片裁剪对话框
│   │       └── excel_import_dialog.py    # Excel 导入对话框
│   │
│   ├── utils/                 # 工具模块
│   │   └── font_helper.py     # 字体辅助工具
│   │
│   ├── import_export/         # 导入导出模块
│   │
│   └── widgets/               # 旧版组件（已废弃）
│
├── tests/                     # 测试文件目录
│
├── docs/                      # 文档目录
│   ├── PROJECT_OVERVIEW.md    # 本文档
│   ├── DATA_MODELS.md         # 数据模型文档
│   ├── CONFIG_SYSTEM.md       # 配置系统文档
│   ├── PPT_GENERATION.md      # PPT 生成逻辑文档
│   ├── UI_COMPONENTS.md       # UI 组件文档
│   ├── DATA_SYNC.md           # 数据同步文档
│   ├── TEMPLATE_SPEC.md       # 模板规范文档
│   ├── BUILD_DEPLOY.md        # 打包部署文档
│   ├── EXPERIENCE_NOTES.md    # 经验总结文档
│   └── CHANGELOG.md           # 变更日志
│
├── dist/                      # 打包输出目录
│
└── build/                     # 构建临时目录
```

## 入口点和启动流程

### 主入口 (main.py)

```python
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

# 配置控制台编码
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def main():
    """主函数"""
    from src.ui.main_window import run_app
    run_app()

if __name__ == "__main__":
    main()
```

### 启动流程

```
1. main.py 执行
   ↓
2. 设置工作目录（兼容开发和打包环境）
   ↓
3. 配置控制台编码（UTF-8）
   ↓
4. 调用 run_app()
   ↓
5. 创建 QApplication
   ↓
6. 初始化 ConfigManager（加载配置）
   ↓
7. 创建 MainWindow
   ↓
8. 显示窗口，进入事件循环
```

## 依赖关系

### 核心依赖

```
PyQt5          → GUI 界面
python-pptx    → PPT 文件操作
Pillow         → 图像处理
lxml           → XML 解析（python-pptx 依赖）
```

### 模块依赖图

```
main.py
  └── src.ui.main_window
        ├── src.core.config_manager
        ├── src.core.ppt_generator
        │     ├── src.core.models
        │     └── src.core.image_processor
        ├── src.core.content_filler
        │     ├── src.core.models
        │     └── src.core.checkbox_handler
        ├── src.core.batch_generator
        │     ├── src.core.ppt_generator
        │     └── src.core.content_filler
        └── src.ui.widgets.*
              └── src.core.config_manager
```

## 关键文件说明

| 文件 | 行数 | 说明 |
|------|------|------|
| main_window.py | ~2600 | 主窗口，包含所有 UI 交互逻辑 |
| content_filler.py | ~1900 | PPT 内容填充，处理文本和颜色标记 |
| ppt_generator.py | ~1170 | PPT 生成核心逻辑 |
| config_manager.py | ~750 | 配置管理，班级/学员数据持久化 |
| checkbox_handler.py | ~650 | 处理 PPT 中的评价复选框 |

## 运行环境

### 开发环境

```bash
# 安装依赖
pip install PyQt5 python-pptx Pillow

# 运行程序
python main.py
```

### 生产环境（打包后）

- 双击 `法贝实验室课程反馈助手.exe` 运行
- 需要 Windows 10 或更高版本
- 不需要安装 Python 环境

## 相关文档

- [数据模型](DATA_MODELS.md) - 所有 dataclass 定义
- [配置系统](CONFIG_SYSTEM.md) - 配置管理详解
- [PPT 生成](PPT_GENERATION.md) - 核心生成逻辑
- [UI 组件](UI_COMPONENTS.md) - 界面组件说明
- [模板规范](TEMPLATE_SPEC.md) - PPT 模板要求
- [打包部署](BUILD_DEPLOY.md) - 打包流程说明
