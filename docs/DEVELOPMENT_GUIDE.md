# 开发指南

> 本文档为法贝实验室课程反馈助手的综合开发指南，涵盖架构设计、开发流程、技术决策、经验教训，以及多智能体联合开发的协作规范。

---

## 1. 项目概述

### 1.1 项目定位

法贝实验室课程反馈助手是一个桌面应用程序，用于教育培训机构快速生成标准化、个性化的课程反馈 PPT。用户填写课程信息、课堂评价、上传图片后，一键生成专业的课程反馈报告。

### 1.2 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 语言 | Python 3.14+ | 主力开发语言 |
| GUI | PyQt5 | 界面框架 |
| PPT | python-pptx | PPT 文件读写 |
| 图像 | Pillow | 图片裁剪/缩放 |
| XML | lxml | PPT 底层 XML 操作 |
| 打包 | PyInstaller | 生成便携版 exe |

### 1.3 版本历程

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v1.0.0 | 2025-02-27 | 核心功能完成：班级管理、评价系统、PPT 生成、批量生成 |
| v1.1.0+ | 2026-02 ~ 2026-04 | 夜间模式、图片同步、学员独立课时、配置导出/导入、程序展示图片等比缩放 |

---

## 2. 架构设计

### 2.1 目录结构

```
src/
├── core/                  # 核心业务逻辑（与 UI 无关）
│   ├── models.py          # 数据模型（CourseUnitData, LayoutConfig, ImageData）
│   ├── config_manager.py  # 配置管理（JSON 持久化）
│   ├── ppt_generator.py   # PPT 生成核心
│   ├── content_filler.py  # PPT 内容填充
│   ├── batch_generator.py # 批量生成
│   ├── image_processor.py # 图片处理（裁剪/缩放）
│   ├── checkbox_handler.py# 评价复选框处理
│   └── ...                # 其他核心模块
├── ui/
│   ├── main_window.py     # 主窗口（~2800行，UI 交互核心）
│   ├── theme/             # 主题系统
│   │   ├── theme_manager.py  # 主题管理器（单例）
│   │   └── themes.py      # 日间/夜间主题颜色定义
│   ├── widgets/           # 可复用 UI 组件
│   │   ├── class_selector.py   # 班级选择器
│   │   ├── series_selector.py  # 课程系列选择器
│   │   ├── student_tab_bar.py  # 学员标签栏
│   │   ├── image_upload.py     # 图片上传组件
│   │   ├── arrow_spinbox.py    # 自定义 SpinBox（三角形箭头）
│   │   └── ...
│   └── dialogs/           # 对话框
│       ├── config_transfer_dialog.py  # 配置导出/导入选择
│       ├── batch_progress_dialog.py   # 批量生成进度
│       ├── crop_dialog.py             # 图片裁剪
│       └── excel_import_dialog.py     # Excel 导入
└── utils/
    └── font_helper.py     # 字体工具
```

### 2.2 核心设计模式

#### 2.2.1 数据流架构

```
用户输入 → CourseUnitData（内存缓存）→ PPTGenerator → .pptx 文件
                              ↑
                         ConfigManager（JSON 持久化）
```

- **CourseUnitData** 是核心数据类，承载一份 PPT 的所有数据
- **ConfigManager** 负责持久化（班级、学员、评价记录、课时编号等）
- **MainWindow** 维护 `_student_data_cache` 字典缓存每个学员的数据

#### 2.2.2 学员数据缓存机制

```python
# MainWindow 中的缓存
self._student_data_cache: dict = {}  # {student_name: CourseUnitData}
self._class_shared_data = CourseUnitData()  # 班级级共享数据（课程内容等）
```

**关键设计决策**：将数据分为"共享"和"独立"两类：

| 数据类型 | 共享数据（班级级） | 独立数据（学员级） |
|----------|-------------------|-------------------|
| 课程内容 | ✅ 知识点、重点难点 | ❌ |
| 图片 | ✅ 可同步 | ✅ 可独立 |
| 评价 | ❌ | ✅ 12项评价、总体评价 |
| 课时编号 | ❌ | ✅ 每人独立编号 |
| 补充说明 | ❌ | ✅ 可同步可独立 |

#### 2.2.3 主题系统（v1.1.0 新增）

```python
# 单例模式
ThemeManager.instance().get_colors()  # 获取当前主题颜色
ThemeManager.instance().set_theme("dark")  # 切换主题

# 颜色定义在 themes.py
@dataclass
class ThemeColors:
    background_primary: str = "#ffffff"  # 日间
    text_primary: str = "#212121"
    # ... 40+ 颜色字段

@dataclass
class DarkTheme(ThemeColors):
    background_primary: str = "#1e1e1e"  # 夜间
    text_primary: str = "#e0e0e0"
```

**使用方式**：所有组件通过 `ThemeManager.instance().get_colors()` 获取颜色，不在代码中硬编码颜色值。对话框需自行调用 `setStyleSheet()` 应用主题。

---

## 3. 关键技术决策与经验

### 3.1 python-pptx 陷阱

#### 删除后添加导致 PPT 损坏

python-pptx 在删除幻灯片后添加新幻灯片，会产生重复 ZIP 条目导致文件损坏。

**解决方案**：采用"先添加后删除"顺序。

```python
# ❌ 错误
for i in range(10):
    delete_slide(i)
add_slide(layout)  # PPT 损坏！

# ✅ 正确
for i in range(10):
    add_slide(layout)
for i in range(10):
    delete_slide(i)
```

#### 幻灯片索引规则

- 0-based 索引：`prs.slides[0]` 是第一张
- 删除幻灯片后索引会变化，需要从后往前删除

#### 图片单位换算

```python
1 英寸 = 914400 EMU
1 厘米 = 360000 EMU
# 使用辅助类
from pptx.util import Inches, Cm, Emu
```

### 3.2 图片处理策略

#### 不同图片类型采用不同策略

| 类型 | 方法 | 尺寸 | 位置 |
|------|------|------|------|
| 模型展示 | 居中裁剪为 4:5 | 16×20cm | top=4cm |
| 程序展示 | **等比缩放不裁剪** | 宽≤16cm 或 高≤20cm | top=4cm, 水平居中 |
| 车辆/精彩瞬间 | 居中裁剪为 4:5 | 16.8×21cm | top=3.6cm |

**程序展示图片算法**（v1.1.0 重写）：
```python
# 判断图片偏宽还是偏高
aspect = img.width / img.height
if aspect < 4/5:  # 偏高：锁定高度
    target_height = Cm(20)
    target_width = int(target_height * aspect)
else:  # 偏宽：锁定宽度
    target_width = Cm(16)
    target_height = int(target_width / aspect)
```

### 3.3 SpinBox 箭头样式

**已尝试但失败的方案**：
1. base64 SVG data URI → Qt 不支持
2. QProxyStyle + QPainterPath → 与 QSS 冲突
3. QProxyStyle + Unicode 字符 → 同上
4. 移除按钮样式用 Qt 默认 → 按钮不清晰

**成功方案**：子类化 QSpinBox + 重写 paintEvent 绘制三角形

```python
# src/ui/widgets/arrow_spinbox.py
class ArrowSpinBox(QSpinBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        # 使用 QPainter 在按钮区域绘制三角形
```

### 3.4 夜间模式实现要点

1. **主窗口**：通过 `_on_theme_changed()` 回调设置全局 stylesheet
2. **对话框**：需自行调用 `setStyleSheet()` 应用主题（QDialog 不会自动继承父窗口样式）
3. **颜色标记**：清除颜色后需确保恢复为主题文字色而非固定黑色

```python
# 清除颜色时使用主题色
colors = ThemeManager.instance().get_colors()
cursor.setCharFormat(default_format)  # 使用主题 text_primary 色
```

### 3.5 班级/学员数据持久化

```json
// config/settings.json 核心结构
{
  "classes": [{"id": "cls_xxx", "name": "星期三 18:30", "teacher": "于双源"}],
  "students_by_class": {"cls_xxx": [{"name": "张三", "nickname": "小明"}]},
  "student_last_evaluation": {"cls_xxx": {"张三": {/*12项评价*/}}},
  "student_next_lesson": {"cls_xxx": {"张三": 5}},
  "course_series": [{"name": "机械臂设计", "level": 1}],
  "theme": "light"
}
```

**班级 ID 格式**：`cls_` + 8位十六进制（如 `cls_55818768`），使用 `uuid.uuid4().hex[:8]` 生成。

### 3.6 学员独立课时编号

早期课时编号是班级级的（所有人共用），后改为学员独立编号。

**关键实现**：
- `student_next_lesson`: `{class_id: {student_name: lesson_number}}`
- 生成 PPT 后自动 `+1`
- 切换学员时加载该学员的独立编号

---

## 4. 配置导出/导入系统（v1.1.0 新增）

### 4.1 架构

```
导出流程: 选择对话框 → 选择班级 → 选择可选数据 → 文件保存
导入流程: 文件选择 → 预览 → 选择对话框 → 选择班级+冲突处理 → 合并 → 刷新UI
```

### 4.2 导出文件格式

```json
{
  "_version": "1.0",
  "_export_date": "2026-04-02 12:00:00",
  "_app": "PPTGenerator",
  "settings": {
    "classes": [...],
    "students_by_class": {...},
    "student_last_evaluation": {...},
    "student_next_lesson": {...}
  },
  "colors": {"highlight": "#0070C0", ...}
}
```

### 4.3 导入合并策略

| 数据类型 | 策略 |
|----------|------|
| 班级 | 同名冲突：创建副本（新ID）或跳过 |
| 学员 | 同名跳过，新学员追加 |
| 评价 | 导入覆盖现有 |
| 课时编号 | 取 max(现有, 导入) |
| 课程系列 | 用 `add_course_series()` 去重 |
| 最近记录 | 合并去重，上限 20 条 |

### 4.4 排除项

导出时排除机器相关字段：`window_geometry`、`window_state`、`splitter_state`

---

## 5. 开发流程与规范

### 5.1 分支策略

当前使用单分支 `main` 开发，直接提交推送。

### 5.2 提交规范

```
<type>: <description>

type:
  feat:     新功能
  fix:      Bug 修复
  refactor: 重构
  docs:     文档
  style:    样式调整
  perf:     性能优化
  chore:    构建/工具
```

### 5.3 Pre-commit Hook

项目配置了 `.git/hooks/pre-commit`，提交前自动执行：
1. pyflakes 语法检查
2. 调用链完整性检查（`self.xxx()` 和 `config_manager.xxx()`）
3. 交互确认

### 5.4 打包部署

```bash
python build.py
# 输出: dist/法贝实验室课程反馈助手_便携版.zip
```

PyInstaller 打包为单目录模式（`--windowed`），包含 `templates/`、`config/`、`fonts/` 子目录。

---

## 6. 多智能体联合开发指南

### 6.1 项目上下文注入

新智能体接入项目时，应读取以下文件获取上下文：

| 优先级 | 文件 | 说明 |
|--------|------|------|
| 必读 | `docs/DEVELOPMENT_GUIDE.md` | 本文档 |
| 必读 | `src/core/models.py` | 数据模型定义 |
| 必读 | `src/core/config_manager.py` | 配置管理接口 |
| 推荐 | `docs/EXPERIENCE_NOTES.md` | 已知陷阱和解决方案 |
| 推荐 | `docs/PPT_GENERATION.md` | PPT 生成逻辑 |
| 推荐 | `docs/UI_COMPONENTS.md` | UI 组件说明 |

### 6.2 模块边界

| 模块 | 职责 | 修改频率 | 注意事项 |
|------|------|----------|----------|
| `core/models.py` | 数据结构 | 低 | 修改需同步更新所有使用者 |
| `core/config_manager.py` | 持久化 | 中 | 新增字段需加入 DEFAULT_SETTINGS |
| `core/ppt_generator.py` | PPT 生成 | 低 | 先添加后删除；EMU 单位 |
| `core/content_filler.py` | 内容填充 | 中 | 图片处理按类型区分策略 |
| `ui/main_window.py` | 主窗口 | 高 | ~2800行，最大文件，谨慎修改 |
| `ui/theme/` | 主题系统 | 低 | 颜色值集中管理，不硬编码 |
| `ui/widgets/` | UI 组件 | 中 | 遵循组件封装原则 |
| `ui/dialogs/` | 对话框 | 低 | 需自行应用主题样式 |

### 6.3 开发约定

1. **颜色不硬编码**：使用 `ThemeManager.instance().get_colors()` 获取主题色
2. **路径使用 pathlib**：`Path()` 而非字符串拼接
3. **信号阻塞**：批量更新 UI 前使用 `blockSignals(True/False)`
4. **不可变模式**：修改数据时创建新对象，不直接修改现有对象
5. **错误处理**：系统边界（用户输入、文件 I/O）必须处理异常
6. **新增配置字段**：必须同步在 `DEFAULT_SETTINGS` 中添加默认值

### 6.4 常见任务模式

#### 添加新的 UI 组件

```python
# 1. 在 src/ui/widgets/ 下创建组件文件
# 2. 继承 QWidget 或其子类
# 3. 使用 ThemeManager 获取颜色
from src.ui.theme import ThemeManager

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        colors = ThemeManager.instance().get_colors()
        # ... 构建 UI
```

#### 添加新的对话框

```python
# 1. 在 src/ui/dialogs/ 下创建对话框文件
# 2. 继承 QDialog
# 3. 必须自行应用主题（QDialog 不继承父窗口样式）
# 4. 在 __init__.py 中注册

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_colors = ThemeManager.instance().get_colors()
        self._init_ui()
        self._apply_theme()  # 必须调用

    def _apply_theme(self):
        c = self._theme_colors
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c.background_primary}; color: {c.text_primary}; }}
            QTableView {{ background-color: {c.background_secondary}; color: {c.text_primary}; }}
            # ... 其他组件样式
        """)
```

#### 添加新的配置字段

```python
# 1. 在 ConfigManager.DEFAULT_SETTINGS 中添加默认值
DEFAULT_SETTINGS = {
    # ... 现有字段
    "my_new_field": "default_value",
}

# 2. 在 _load_settings() 中已有的合并逻辑会自动处理新旧配置
```

#### 添加新的图片处理类型

```python
# 在 content_filler.py 中参考现有方法：
# _insert_model_image() - 居中裁剪为 4:5
# _insert_program_image() - 等比缩放不裁剪
# _insert_work_image() - 居中裁剪为 4:5（车辆/精彩瞬间）
```

### 6.5 测试策略

项目目前以手动测试为主。测试检查点：

| 功能 | 测试方法 | 验证要点 |
|------|----------|----------|
| PPT 生成 | 生成后打开检查 | 文本替换、图片位置、复选框状态 |
| 数据同步 | 切换学员/班级 | 共享数据同步、独立数据保持 |
| 主题切换 | Ctrl+T 切换 | 所有控件颜色正确、无硬编码色值 |
| 配置导出/导入 | 导出→导入 | 数据完整、冲突处理正确 |
| 批量生成 | 选择3+学员 | 每人独立数据正确、进度显示正常 |
| 打包 | build.py | exe 运行正常、路径无中文问题 |

---

## 7. 已知问题与待优化

### 7.1 已知问题

1. **main_window.py 过大**（~2800行）：未来应拆分为更小的模块
2. **Excel 导入**：仅支持特定格式
3. **批量生成内存**：大量生成时内存占用较高

### 7.2 待优化方向

1. **架构重构**：将 main_window.py 拆分为多个控制器类
2. **单元测试**：为核心逻辑添加 pytest 测试用例
3. **自定义模板**：支持多种 PPT 模板
4. **PDF 导出**：PPT 生成后自动导出 PDF
5. **数据备份**：自动备份配置文件

---

## 8. 相关文档索引

| 文档 | 说明 |
|------|------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | 项目概述、目录结构、依赖关系 |
| [DATA_MODELS.md](DATA_MODELS.md) | 数据模型定义 |
| [CONFIG_SYSTEM.md](CONFIG_SYSTEM.md) | 配置管理详解 |
| [PPT_GENERATION.md](PPT_GENERATION.md) | PPT 生成逻辑 |
| [UI_COMPONENTS.md](UI_COMPONENTS.md) | UI 组件说明 |
| [TEMPLATE_SPEC.md](TEMPLATE_SPEC.md) | PPT 模板规范 |
| [BUILD_DEPLOY.md](BUILD_DEPLOY.md) | 打包部署流程 |
| [EXPERIENCE_NOTES.md](EXPERIENCE_NOTES.md) | 开发经验与陷阱 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |

---

*最后更新: 2026-04-02*
