# UI 组件

本文档描述所有用户界面组件，位于 `src/ui/` 目录。

## 主窗口 (MainWindow)

位于 `src/ui/main_window.py`。

### 窗口结构

```
MainWindow
├── MenuBar（菜单栏）
│   ├── 文件
│   │   ├── 生成PPT
│   │   ├── 批量生成
│   │   ├── ──────────
│   │   └── 退出
│   ├── 设置
│   │   └── 选择模板
│   └── 帮助
│       └── 关于
│
├── ToolBar（工具栏）
│   ├── 生成PPT
│   └── 批量生成
│
├── CentralWidget（中心部件）
│   └── QSplitter（分割器）
│       ├── LeftPanel（左侧面板）
│       │   ├── 系列选择
│       │   ├── 班级选择
│       │   ├── 学员管理
│       │   └── 布局选择
│       │
│       └── RightPanel（右侧面板）
│           ├── TabWidget
│           │   ├── 基本信息
│           │   ├── 课堂知识
│           │   ├── 课堂评价
│           │   └── 图片上传
│           │
│           └── 学员标签栏
│
├── StatusBar（状态栏）
│
└── Dialogs（对话框）
    ├── BatchProgressDialog
    ├── ExcelImportDialog
    └── CropDialog
```

### 主要属性

```python
class MainWindow(QMainWindow):
    def __init__(self):
        self.config_manager = ConfigManager()  # 配置管理器
        self.current_data = {}                 # 当前表单数据
        self.student_cache = {}                # 学员数据缓存
```

### 主要方法

```python
def generate_ppt(self):
    """生成单个 PPT"""

def batch_generate(self):
    """批量生成 PPT"""

def on_student_tab_changed(self, index):
    """学员标签切换"""

def save_current_student_data(self):
    """保存当前学员数据到缓存"""

def load_student_data(self, student_name):
    """从缓存加载学员数据"""
```

## 左侧面板组件

### SeriesSelectorWidget - 系列选择器

位于 `src/ui/widgets/series_selector.py`。

**功能**：
- 显示课程系列下拉列表
- 支持添加/删除系列
- 选择系列后自动填充课程内容

**信号**：
```python
series_changed = pyqtSignal(str, int)  # 系列名称, 阶数
```

**方法**：
```python
def get_current_series(self) -> tuple:
    """返回 (name, level)"""

def set_current_series(self, index: int):
    """设置当前系列"""
```

### ClassSelectorWidget - 班级选择器

位于 `src/ui/widgets/class_selector.py`。

**功能**：
- 显示班级下拉列表
- 支持添加/删除班级
- 显示班级详情（默认教师）
- 修改班级默认教师

**信号**：
```python
class_changed = pyqtSignal(str)           # 班级 ID
teacher_changed = pyqtSignal(str)         # 教师姓名
class_series_changed = pyqtSignal(int)    # 班级关联的系列索引
```

**方法**：
```python
def get_current_class_id(self) -> str:
def refresh_class_list(self):
```

### StudentManagerWidget - 学员管理器

位于 `src/ui/widgets/student_manager.py`。

**功能**：
- 显示班级学员列表
- 添加/编辑/删除学员
- 导入学员（从 Excel）

**信号**：
```python
student_changed = pyqtSignal()  # 学员列表变化
```

### LayoutSelectorWidget - 布局选择器

位于 `src/ui/widgets/layout_selector.py`。

**功能**：
- 选择 PPT 包含的页面类型
- 模型展示、精彩瞬间、程序展示、车辆展示

## 右侧面板组件

### CourseInfoWidget - 课程信息

位于 `src/ui/widgets/course_info.py`。

**功能**：
- 输入课时编号、课程内容、学生姓名、教师、课时数、日期
- 学生姓名支持自动补全
- 教师姓名支持自动补全

**方法**：
```python
def get_data(self) -> dict:
def set_data(self, data: dict):
def clear(self):
```

### RichTextEditor - 富文本编辑器

位于 `src/ui/widgets/rich_text_editor.py`。

**功能**：
- 富文本编辑
- 重点标记（蓝色）
- 难点标记（橙色）
- 支持撤销/重做

**按钮**：
- 重点：将选中文字标记为蓝色
- 难点：将选中文字标记为橙色
- 清除：清除选中文字的颜色标记

**方法**：
```python
def get_content(self) -> str:
def set_content(self, html: str):
def get_highlights(self) -> list:
def get_difficulties(self) -> list:
```

### EvaluationWidget - 评价组件

位于 `src/ui/widgets/evaluation.py`。

**功能**：
- 12 项课堂评价（单选）
- 总体评价
- 上次作业情况
- 补充说明、课堂作业、注意事项

**评价项**（按 PPT 模板顺序）：

| 左列 | 右列 |
|------|------|
| 专注度与效率 | 动手实践能力 |
| 课堂听课习惯 | 逻辑思维表现 |
| 课堂任务完成 | 想象力与创新 |
| 课堂内容理解 | 独立分析思考 |
| 知识熟练程度 | 解决问题表现 |
| 学习方法习惯 | 挫折困难应对 |

**信号**：
```python
data_changed = pyqtSignal()
sync_comments_requested = pyqtSignal()  # 强制同步补充说明
```

**方法**：
```python
def get_data(self) -> dict:
def set_data(self, data: dict):
def clear(self):
```

### ImageUploadWidget - 图片上传

位于 `src/ui/widgets/image_upload.py`。

**功能**：
- 拖拽上传图片
- 点击选择图片
- 图片预览缩略图
- 删除图片
- 裁剪图片

**信号**：
```python
images_changed = pyqtSignal(list)  # 图片路径列表
```

**方法**：
```python
def get_images(self) -> List[str]:
def set_images(self, paths: List[str]):
def clear_images(self):
def add_images(self, paths: List[str]):
```

### ImagePreviewWidget - 图片预览

位于 `src/ui/widgets/image_upload.py`。

**功能**：
- 显示图片缩略图
- 悬停显示删除/裁剪按钮
- 点击在系统程序中打开

**信号**：
```python
delete_clicked = pyqtSignal()
crop_clicked = pyqtSignal()
clicked = pyqtSignal()
```

### StudentTabBar - 学员标签栏

位于 `src/ui/widgets/student_tab_bar.py`。

**功能**：
- 底部显示学员标签
- 切换学员时自动缓存数据
- 支持添加新学员

**信号**：
```python
currentChanged = pyqtSignal(int)
```

## 对话框

### BatchProgressDialog - 批量进度

位于 `src/ui/dialogs/batch_progress_dialog.py`。

**功能**：
- 显示批量生成进度
- 显示当前处理的学生
- 支持取消操作
- 显示成功/失败统计

### CropDialog - 图片裁剪

位于 `src/ui/dialogs/crop_dialog.py`。

**功能**：
- 显示原图预览
- 拖拽选择裁剪区域
- 预览裁剪结果
- 确认/取消操作

### ExcelImportDialog - Excel 导入

位于 `src/ui/dialogs/excel_import_dialog.py`。

**功能**：
- 选择 Excel 文件
- 预览导入数据
- 映射列到字段
- 确认导入

## 数据流

### 学员切换流程

```
1. 用户点击学员标签
     ↓
2. on_student_tab_changed(index)
     ↓
3. save_current_student_data()  # 保存当前学员数据到缓存
     ↓
4. 持久化评价数据到 ConfigManager
     ↓
5. load_student_data(new_name)  # 加载新学员数据
     ↓
6. 从缓存或 ConfigManager 加载数据
     ↓
7. 更新所有 UI 组件
```

### 数据缓存结构

```python
student_cache = {
    "张三": {
        "lesson_number": 1,
        "knowledge_content": "...",
        "highlights": [...],
        "difficulties": [...],
        # ... 其他字段
    },
    "李四": {...}
}
```

### 共享数据 vs 独立数据

**共享数据**（班级级别，所有学员相同）：
- course_content（课程内容）
- teacher_name（教师）
- class_hours（课时数）
- class_date（上课日期）
- knowledge_content（知识内容）
- homework（课堂作业）

**独立数据**（学员级别，每个学员不同）：
- student_name（学生姓名）
- 12 项评价
- overall_evaluation（总体评价）
- additional_comments（补充说明）
- other_notes（注意事项）
- model_images、work_images（图片）

## 样式设置

### 全局样式

```python
# 主窗口
self.setStyleSheet("""
    QMainWindow {
        background-color: #f5f5f5;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #ccc;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        padding: 5px 15px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #106ebe;
    }
    QPushButton:pressed {
        background-color: #005a9e;
    }
""")
```

### 评价组件样式

```python
# 选中的单选按钮
QRadioButton:checked {
    color: #0078d4;
    font-weight: bold;
}
```

## 相关文档

- [数据同步](DATA_SYNC.md) - 学员数据缓存和同步机制
- [配置系统](CONFIG_SYSTEM.md) - 数据持久化
