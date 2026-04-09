# 数据同步逻辑

本文档描述班级共享数据、学员缓存和评价持久化的机制。

## 概述

### 数据分类

| 类型 | 范围 | 存储位置 |
|------|------|----------|
| 共享数据 | 班级级别，所有学员相同 | 内存缓存 |
| 独立数据 | 学员级别，每个学员不同 | 内存缓存 + 配置文件 |
| 配置数据 | 应用级别 | 配置文件 |

### 共享数据字段

以下字段在同一个班级中所有学员共享：

```python
SHARED_FIELDS = [
    'course_content',      # 课程内容
    'teacher_name',        # 授课教师
    'class_hours',         # 课时数
    'class_date',          # 上课日期
    'knowledge_content',   # 知识内容
    'knowledge_html',      # 知识内容 HTML
    'highlights',          # 重点词汇
    'difficulties',        # 难点词汇
    'homework',            # 课堂作业
    'lesson_number',       # 课时编号
]
```

### 独立数据字段

以下字段每个学员独立保存：

```python
INDEPENDENT_FIELDS = [
    'student_name',        # 学生姓名
    'logic_thinking',      # 逻辑思维
    'content_understanding', # 内容理解
    'task_completion',     # 任务完成
    'listening_habit',     # 听课习惯
    'problem_solving',     # 解决问题
    'independent_analysis', # 独立分析
    'knowledge_proficiency', # 知识熟练
    'imagination_creativity', # 想象力创新
    'frustration_handling', # 挫折应对
    'learning_method',     # 学习方法
    'hands_on_ability',    # 动手能力
    'focus_efficiency',    # 专注效率
    'overall_evaluation',  # 总体评价
    'last_homework_status', # 上次作业
    'additional_comments', # 补充说明
    'other_notes',         # 注意事项
    'model_images',        # 模型图片
    'work_images',         # 作品图片
]
```

## 学员数据缓存

### 缓存结构

```python
# 在 MainWindow 中
self.student_cache = {
    "class_id_123": {
        "张三": {
            # 独立数据
            "logic_thinking": "优",
            "overall_evaluation": "良",
            # ... 其他字段
        },
        "李四": {...}
    }
}
```

### 缓存流程

#### 1. 切换学员时保存

```python
def on_student_tab_changed(self, index):
    # 1. 保存当前学员数据
    self.save_current_student_data()

    # 2. 持久化评价数据
    self._persist_evaluation_data()

    # 3. 加载新学员数据
    student_name = self.student_tab_bar.tabText(index)
    self.load_student_data(student_name)
```

#### 2. 保存当前学员数据

```python
def save_current_student_data(self):
    """保存当前学员数据到缓存"""
    if not self.current_student_name:
        return

    class_id = self.class_selector.get_current_class_id()
    if not class_id:
        return

    # 确保缓存结构存在
    if class_id not in self.student_cache:
        self.student_cache[class_id] = {}

    # 获取当前表单数据
    data = self._collect_form_data()

    # 只保存独立字段
    independent_data = {k: v for k, v in data.items()
                        if k in INDEPENDENT_FIELDS}

    self.student_cache[class_id][self.current_student_name] = independent_data
```

#### 3. 加载学员数据

```python
def load_student_data(self, student_name: str):
    """从缓存加载学员数据"""
    class_id = self.class_selector.get_current_class_id()

    # 1. 尝试从内存缓存加载
    cached_data = self.student_cache.get(class_id, {}).get(student_name, {})

    # 2. 如果缓存中没有，尝试从配置文件加载
    if not cached_data:
        cached_data = self.config_manager.get_student_last_evaluation(
            class_id, student_name
        )

    # 3. 填充表单
    self._fill_form_with_data(cached_data)

    # 4. 加载共享数据
    self._load_shared_data()
```

## 评价数据持久化

### 保存时机

1. 切换学员时
2. 切换班级时
3. 生成 PPT 后
4. 关闭窗口时

### 持久化方法

```python
def _persist_evaluation_data(self):
    """持久化当前学员的评价数据"""
    if not self.current_student_name:
        return

    class_id = self.class_selector.get_current_class_id()
    if not class_id:
        return

    # 获取评价数据
    eval_data = self.evaluation_widget.get_data()

    # 保存到配置文件
    self.config_manager.save_student_last_evaluation(
        class_id,
        self.current_student_name,
        eval_data
    )
```

### ConfigManager 中的存储

```python
# settings.json 中的结构
{
    "student_last_evaluation": {
        "cls_a1b2c3d4": {
            "张三": {
                "logic_thinking": "优",
                "overall_evaluation": "良",
                # ... 只有独立字段
            },
            "李四": {...}
        }
    }
}
```

## 补充说明同步

### 强制同步功能

点击"强制同步给所有同学"按钮，将当前学员的补充说明同步给班级所有其他学员。

```python
def on_sync_comments_requested(self):
    """强制同步补充说明"""
    current_comments = self.evaluation_widget.additional_comments.toPlainText()
    current_student = self.current_student_name

    class_id = self.class_selector.get_current_class_id()
    if not class_id:
        return

    # 获取班级所有学员
    students = self.config_manager.get_students_by_class(class_id)

    for student in students:
        name = student.get("name")
        if name == current_student:
            continue

        # 自动替换名字
        personalized_comments = current_comments.replace(
            current_student, name
        )

        # 更新缓存
        if class_id not in self.student_cache:
            self.student_cache[class_id] = {}
        if name not in self.student_cache[class_id]:
            self.student_cache[class_id][name] = {}

        self.student_cache[class_id][name]['additional_comments'] = personalized_comments

        # 持久化
        self.config_manager.save_student_last_evaluation(
            class_id, name,
            {'additional_comments': personalized_comments}
        )

    QMessageBox.information(self, "成功", "已同步给所有同学")
```

## 课时编号管理

### 自动递增

```python
def on_ppt_generated(self, lesson_number: int):
    """PPT 生成成功后的处理"""
    class_id = self.class_selector.get_current_class_id()

    # 记录已生成的课时
    self.config_manager.record_lesson_generated(class_id, lesson_number)

    # 下次自动填充新的课时编号
    next_lesson = self.config_manager.get_next_lesson_number(class_id)
    self.course_info.set_lesson_number(next_lesson)
```

### 班级独立计数

每个班级维护独立的课时编号计数器。

```python
# settings.json
{
    "classes": [
        {
            "id": "cls_aaa",
            "name": "星期一 14:00",
            "next_lesson_number": 5
        },
        {
            "id": "cls_bbb",
            "name": "星期三 18:30",
            "next_lesson_number": 3
        }
    ]
}
```

## 班级切换流程

```python
def on_class_changed(self, class_id: str):
    """班级切换处理"""
    # 1. 保存当前班级的共享数据
    self._save_shared_data()

    # 2. 持久化当前学员评价
    self._persist_evaluation_data()

    # 3. 清空当前缓存
    self.current_student_name = ""

    # 4. 加载新班级的学员列表
    students = self.config_manager.get_students_by_class(class_id)
    self.student_tab_bar.set_students(students)

    # 5. 加载新班级的共享数据
    self._load_shared_data()

    # 6. 如果有学员，选择第一个
    if students:
        self.student_tab_bar.setCurrentIndex(0)
```

## 默认值恢复

### 首次添加学员

当添加新学员时，评价数据使用默认值：

```python
DEFAULT_EVALUATION = {
    # 12 项评价默认为"优"
    'logic_thinking': '优',
    'content_understanding': '优',
    # ... 其他评价项

    # 总体评价默认为"优"
    'overall_evaluation': '优',

    # 上次作业默认为"无"
    'last_homework_status': '无',

    # 文本默认为空
    'additional_comments': '',
    'other_notes': '',
}
```

### 恢复上次评价

如果学员之前生成过 PPT，下次加载时会恢复上次的评价数据。

```python
def load_student_data(self, student_name: str):
    # 先加载默认值
    data = DEFAULT_EVALUATION.copy()

    # 再用缓存数据覆盖
    cached = self.config_manager.get_student_last_evaluation(class_id, student_name)
    data.update(cached)

    # 填充表单
    self._fill_form_with_data(data)
```

## 数据流图

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ UI Components │  │ student_cache │  │ ConfigManager │      │
│  │              │  │ (内存)        │  │ (配置文件)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
│         │  读取/写入      │  读取/写入       │              │
│         └────────┬────────┴────────┬─────────┘              │
│                  │                 │                        │
│                  ▼                 ▼                        │
│         ┌────────────────────────────────┐                 │
│         │        数据同步逻辑            │                 │
│         │  - 保存当前学员                │                 │
│         │  - 加载新学员                  │                 │
│         │  - 持久化评价                  │                 │
│         │  - 同步共享数据                │                 │
│         └────────────────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 相关文档

- [配置系统](CONFIG_SYSTEM.md) - ConfigManager 详解
- [UI 组件](UI_COMPONENTS.md) - 界面组件实现
