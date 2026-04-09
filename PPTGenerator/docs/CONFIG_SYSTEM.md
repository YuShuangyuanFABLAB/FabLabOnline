# 配置系统

本文档描述 `ConfigManager` 类的完整功能，位于 `src/core/config_manager.py`。

## 概述

`ConfigManager` 负责：
- 应用程序设置的持久化存储
- 班级和学员管理
- 课程系列管理
- 布局配置管理
- 最近使用数据管理
- 学员评价数据缓存

## 初始化

```python
from src.core.config_manager import ConfigManager

# 使用默认路径（应用程序目录下的 config 文件夹）
config = ConfigManager()

# 或指定自定义路径
config = ConfigManager(config_dir="/path/to/config")
```

### 文件结构

```
config/
├── settings.json    # 主配置文件
└── colors.json      # 颜色配置文件
```

## 默认设置

```python
DEFAULT_SETTINGS = {
    # 窗口设置
    "window_geometry": "",
    "window_state": "",
    "splitter_state": "",

    # 默认值
    "default_teacher": "",
    "default_class_hours": 2,

    # 课程系列配置
    "course_series": [
        {"name": "机械臂设计", "level": 1},
        {"name": "玩具大改造", "level": 1}
    ],
    "current_series_index": 0,

    # 班级管理
    "classes": [],                      # 班级列表
    "current_class_id": "",             # 当前选择的班级 ID
    "students_by_class": {},            # 按班级分组的学员

    # 最近使用的数据
    "recent_students": [],              # 最近使用的学生
    "recent_teachers": [],              # 最近使用的教师
    "recent_courses": [],               # 最近使用的课程内容

    # 布局配置
    "layout_config": {
        "include_course_info": True,
        "include_model_display": True,
        "model_display_count": 1,
        "include_double_image": False,
        "include_program_display": False,
        "include_vehicle_display": False,
        "include_work_display": True
    },

    # 模板路径
    "template_path": "templates/课程反馈.pptx",
    "output_path": "output",

    # 其他设置
    "auto_save": True,
    "show_preview": True,

    # 学员评价持久化
    "student_last_evaluation": {},      # {class_id: {student_name: {评价数据}}}
    "default_other_notes": ""           # 默认注意事项
}
```

## 基本操作

### 读取和保存设置

```python
# 获取设置值
value = config.get("key", default_value)

# 设置值（自动保存）
config.set("key", value)

# 获取/设置颜色
color = config.get_color("highlight")
```

### 重置设置

```python
config.reset_to_defaults()
```

## 班级管理

### 添加班级

```python
class_id = config.add_class(
    name="星期一 14:00",    # 班级名称
    teacher="张老师"        # 默认教师（可选）
)
# 返回班级 ID，如 "cls_a1b2c3d4"
# 如果班级名称已存在，返回空字符串
```

### 删除班级

```python
success = config.remove_class(class_id)
# 同时删除该班级的学员数据
```

### 获取班级信息

```python
# 获取所有班级列表
classes = config.get_classes()
# 返回: [{"id": "cls_xxx", "name": "星期一 14:00", "teacher": "张老师", "series_index": 0}, ...]

# 获取当前选择的班级
current = config.get_current_class()

# 设置当前班级
config.set_current_class(class_id)
```

### 更新班级教师

```python
success = config.update_class_teacher(class_id, "新老师")
```

### 班级关联课程系列

```python
# 获取班级关联的课程系列索引
series_index = config.get_class_series_index(class_id)

# 设置班级关联的课程系列
config.set_class_series_index(class_id, 2)
```

### 班级输出路径

```python
# 获取班级的输出路径（如果无效则返回默认路径）
path = config.get_class_output_path(class_id)

# 设置班级的输出路径
config.set_class_output_path(class_id, "/custom/output/path")
```

## 学员管理

### 添加学员

```python
success = config.add_student(
    class_id=class_id,
    name="张三",
    nickname="小明"    # 可选
)
```

### 删除学员

```python
success = config.remove_student(class_id, index)  # index 为学员在列表中的索引
```

### 更新学员信息

```python
success = config.update_student(
    class_id=class_id,
    index=0,
    name="张三",
    nickname="小明"
)
```

### 获取班级学员列表

```python
students = config.get_students_by_class(class_id)
# 返回: [{"name": "张三", "nickname": "小明"}, {"name": "李四", "nickname": ""}]
```

## 课程系列管理

### 获取系列列表

```python
series_list = config.get_course_series()
# 返回: [{"name": "机械臂设计", "level": 1}, ...]
```

### 添加课程系列

```python
success = config.add_course_series(
    name="军卡大改造",
    level=2
)
# 如果已存在相同名称和阶数，返回 False
```

### 删除课程系列

```python
success = config.remove_course_series(index)
```

### 获取/设置当前系列

```python
# 获取当前选择的系列
current = config.get_current_series()
# 返回: {"name": "机械臂设计", "level": 1}

# 设置当前系列
config.set_current_series(index)
```

## 布局配置管理

### 获取布局配置

```python
layout_config = config.get_layout_config()
# 返回: {"include_course_info": True, "include_model_display": True, ...}
```

### 设置布局配置

```python
config.set_layout_config({
    "include_course_info": True,
    "include_model_display": True,
    "model_display_count": 1,
    "include_double_image": False,
    "include_program_display": False,
    "include_vehicle_display": False,
    "include_work_display": True
})
```

### 班级特定布局

```python
# 获取班级的自定义布局（如果没有则返回 None）
layout = config.get_class_layout_config(class_id)

# 设置班级的自定义布局
config.set_class_layout_config(class_id, layout_dict)
```

## 最近使用数据管理

### 学生

```python
# 添加到最近使用
config.add_recent_student("张三")

# 获取最近使用列表
recent = config.get_recent_students()  # 最多 20 条
```

### 教师

```python
config.add_recent_teacher("李老师")
recent = config.get_recent_teachers()
```

### 课程内容

```python
config.add_recent_course("机械臂设计（1阶）")
recent = config.get_recent_courses()
```

## 学员评价持久化

用于保存每个学员上次填写的评价数据，下次切换时自动恢复。

### 保存评价

```python
eval_data = {
    'logic_thinking': '优',
    'content_understanding': '良',
    'task_completion': '优',
    # ... 其他评价项
    'overall_evaluation': '优',
    'last_homework_status': '无',
    'additional_comments': '今天学习表现很好'
}
config.save_student_last_evaluation(class_id, "张三", eval_data)
```

**注意**：只保存独立字段，不保存共享字段（如课程内容、教师等）。

### 获取评价

```python
eval_data = config.get_student_last_evaluation(class_id, "张三")
# 如果不存在，返回空字典 {}
```

### 默认注意事项

```python
# 获取/设置默认注意事项
notes = config.get_default_other_notes()
config.save_default_other_notes("上课专注，继续加油！")
```

## 课时编号管理

### 获取下次课时编号

```python
next_lesson = config.get_next_lesson_number(class_id)
# 默认返回 1
```

### 设置下次课时编号

```python
config.set_next_lesson_number(class_id, 3)
```

### 记录已生成课时

```python
# 生成后调用，自动设置下次课时 = 当前 + 1
config.record_lesson_generated(class_id, lesson_number=2)
```

## 路径管理

### 模板路径

```python
# 获取模板路径
template_path = config.get_template_path()  # 默认 "templates/课程反馈.pptx"

# 设置模板路径
config.set_template_path("/custom/path/template.pptx")
```

### 输出路径

```python
# 获取默认输出路径
output_path = config.get_output_path()  # 默认 "output"

# 设置默认输出路径
config.set_output_path("/custom/output")
```

## 配置文件格式

### settings.json 示例

```json
{
  "window_geometry": "...",
  "window_state": "...",
  "splitter_state": "...",
  "default_teacher": "",
  "default_class_hours": 2,
  "course_series": [
    {"name": "机械臂设计", "level": 1},
    {"name": "玩具大改造", "level": 1}
  ],
  "current_series_index": 0,
  "classes": [
    {
      "id": "cls_a1b2c3d4",
      "name": "星期一 14:00",
      "teacher": "张老师",
      "series_index": 0
    }
  ],
  "current_class_id": "cls_a1b2c3d4",
  "students_by_class": {
    "cls_a1b2c3d4": [
      {"name": "张三", "nickname": "小明"},
      {"name": "李四", "nickname": ""}
    ]
  },
  "recent_students": ["张三", "李四"],
  "recent_teachers": ["张老师"],
  "recent_courses": ["机械臂设计（1阶）"],
  "layout_config": {
    "include_course_info": true,
    "include_model_display": true,
    "model_display_count": 1,
    "include_double_image": false,
    "include_program_display": false,
    "include_vehicle_display": false,
    "include_work_display": true
  },
  "template_path": "templates/课程反馈.pptx",
  "output_path": "output",
  "auto_save": true,
  "show_preview": true,
  "student_last_evaluation": {
    "cls_a1b2c3d4": {
      "张三": {
        "logic_thinking": "优",
        "overall_evaluation": "优"
      }
    }
  },
  "default_other_notes": ""
}
```

## 相关文档

- [数据模型](DATA_MODELS.md) - 配置中使用的数据类型
- [UI 组件](UI_COMPONENTS.md) - 配置界面的实现
