# 数据模型

本文档描述项目中所有的数据类定义，位于 `src/core/models.py`。

## 枚举类型

### EvaluationLevel - 评价等级

用于 12 项课堂评价。

```python
class EvaluationLevel(Enum):
    """评价等级枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    MEDIUM = "中"
    POOR = "差"
    NOT_SHOWN = "未体现"
```

### OverallEvaluation - 总体评价

用于学员整体表现评价。

```python
class OverallEvaluation(Enum):
    """总体评价枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    NEED_EFFORT = "仍需努力"
    NEED_IMPROVEMENT = "需要改进"
```

### HomeworkEvaluation - 作业评价

用于上次作业情况评价。

```python
class HomeworkEvaluation(Enum):
    """作业评价枚举"""
    EXCELLENT = "优"
    GOOD = "良"
    MEDIUM = "中"
    POOR = "差"
    NONE = "无"
```

## CourseUnitData - 课程单元数据

核心数据类，包含一节课的所有信息。

```python
@dataclass
class CourseUnitData:
    """课程单元数据类"""
```

### 基本信息

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `lesson_number` | int | 1 | 课时编号（第几课） |
| `course_content` | str | "" | 课程内容描述 |
| `student_name` | str | "" | 学生姓名 |
| `teacher_name` | str | "" | 授课教师姓名 |
| `class_hours` | int | 2 | 课时数 |
| `class_date` | str | "" | 上课日期时间 |

### 课程内容

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `knowledge_content` | str | "" | 课堂知识内容（纯文本） |
| `knowledge_html` | str | "" | 知识内容 HTML（保留格式） |
| `highlights` | List[Union[str, Tuple[str, int]]] | [] | 重点词汇列表 |
| `difficulties` | List[Union[str, Tuple[str, int]]] | [] | 难点词汇列表 |

#### 重点/难点格式说明

支持两种格式：

1. **简单字符串列表** - 标记第一次出现
   ```python
   highlights = ["词汇1", "词汇2"]
   ```

2. **元组列表** - 标记指定索引的出现（1 表示第 1 次，2 表示第 2 次...）
   ```python
   highlights = [("词汇1", 1), ("词汇2", 2)]
   ```

### 课堂评价（12 项）

所有评价项默认值为 `EvaluationLevel.NOT_SHOWN`。

| 字段 | 说明 |
|------|------|
| `logic_thinking` | 逻辑思维表现 |
| `content_understanding` | 课堂内容理解 |
| `task_completion` | 课堂任务完成 |
| `listening_habit` | 课堂听课习惯 |
| `problem_solving` | 解决问题表现 |
| `independent_analysis` | 独立分析思考 |
| `knowledge_proficiency` | 知识熟练程度 |
| `imagination_creativity` | 想象力与创新 |
| `frustration_handling` | 挫折困难应对 |
| `learning_method` | 学习方法习惯 |
| `hands_on_ability` | 动手实践能力 |
| `focus_efficiency` | 专注度与效率 |

### 总体评价

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `overall_evaluation` | OverallEvaluation | GOOD | 总体评价 |

### 补充信息

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `additional_comments` | str | "" | 补充说明 |
| `homework` | str | "" | 课堂作业 |
| `other_notes` | str | "" | 注意事项 |
| `last_homework_status` | HomeworkEvaluation | NONE | 上次作业评价 |

### 图片路径

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_images` | List[str] | [] | 模型展示图片路径列表 |
| `work_images` | List[str] | [] | 精彩瞬间图片路径列表 |
| `program_images` | List[str] | [] | 程序展示图片路径列表 |
| `vehicle_images` | List[str] | [] | 车辆展示图片路径列表 |

### 完整定义

```python
@dataclass
class CourseUnitData:
    """课程单元数据类"""
    # 基本信息
    lesson_number: int = 1
    course_content: str = ""
    student_name: str = ""
    teacher_name: str = ""
    class_hours: int = 2
    class_date: str = ""

    # 课程内容
    knowledge_content: str = ""
    knowledge_html: str = ""
    highlights: List[Union[str, Tuple[str, int]]] = field(default_factory=list)
    difficulties: List[Union[str, Tuple[str, int]]] = field(default_factory=list)

    # 课堂评价
    logic_thinking: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    content_understanding: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    task_completion: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    listening_habit: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    problem_solving: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    independent_analysis: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    knowledge_proficiency: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    imagination_creativity: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    frustration_handling: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    learning_method: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    hands_on_ability: EvaluationLevel = EvaluationLevel.NOT_SHOWN
    focus_efficiency: EvaluationLevel = EvaluationLevel.NOT_SHOWN

    # 总体评价
    overall_evaluation: OverallEvaluation = OverallEvaluation.GOOD

    # 补充信息
    additional_comments: str = ""
    homework: str = ""
    other_notes: str = ""
    last_homework_status: HomeworkEvaluation = HomeworkEvaluation.NONE

    # 图片路径
    model_images: List[str] = field(default_factory=list)
    work_images: List[str] = field(default_factory=list)
    program_images: List[str] = field(default_factory=list)
    vehicle_images: List[str] = field(default_factory=list)
```

## LayoutConfig - 布局配置

控制 PPT 包含哪些页面。

```python
@dataclass
class LayoutConfig:
    """母版配置类"""
    include_course_info: bool = True      # 包含课程信息页
    include_model_display: bool = True    # 包含模型展示页
    model_display_count: int = 1          # 模型展示页数量
    include_double_image: bool = False    # 包含双图布局
    include_program_display: bool = False # 包含程序展示页
    include_vehicle_display: bool = False # 包含车辆展示页
    include_work_display: bool = True     # 包含精彩瞬间页
```

### 方法

```python
def get_total_pages(self, model_image_count: int = 1, work_image_count: int = 1,
                    program_image_count: int = 1, vehicle_image_count: int = 1) -> int:
    """
    计算总页数

    Args:
        model_image_count: 模型展示图片数量
        work_image_count: 精彩瞬间图片数量
        program_image_count: 程序展示图片数量
        vehicle_image_count: 车辆展示图片数量
    """
```

## ImageData - 图片数据

```python
@dataclass
class ImageData:
    """图片数据类"""
    path: str                      # 图片路径
    target_width: float = 6.55     # 目标宽度（英寸）
    target_height: float = 8.07    # 目标高度（英寸）
    crop_mode: str = "center"      # 裁剪模式：center, manual
    crop_x: float = 0.0            # 裁剪起始 X（比例）
    crop_y: float = 0.0            # 裁剪起始 Y（比例）
    rotation: int = 0              # 旋转角度
```

## 使用示例

### 创建课程数据

```python
from src.core.models import CourseUnitData, LayoutConfig, EvaluationLevel, OverallEvaluation

# 创建课程数据
data = CourseUnitData(
    lesson_number=1,
    course_content="机械臂设计（1阶）",
    student_name="张三",
    teacher_name="李老师",
    class_hours=2,
    class_date="2025.1.15 14:00-16:00",
    knowledge_content="学习机械臂的基本结构\n理解关节的运动原理",
    highlights=["机械臂", "关节"],
    logic_thinking=EvaluationLevel.EXCELLENT,
    overall_evaluation=OverallEvaluation.GOOD,
    model_images=["path/to/model.jpg"],
    work_images=["path/to/work.jpg"]
)

# 创建布局配置
layout = LayoutConfig(
    include_course_info=True,
    include_model_display=True,
    include_work_display=True
)

# 计算页数
total_pages = layout.get_total_pages(
    model_image_count=len(data.model_images),
    work_image_count=len(data.work_images)
)
```

### 评价等级转换

```python
# 从字符串转换为枚举
level = EvaluationLevel("优")  # EvaluationLevel.EXCELLENT

# 从枚举获取字符串
text = level.value  # "优"

# 总体评价
overall = OverallEvaluation.GOOD
text = overall.value  # "良"
```

## 数据验证

### 必填字段

虽然 dataclass 有默认值，但以下字段应在生成 PPT 前填写：

- `student_name` - 学生姓名（必须）
- `teacher_name` - 授课教师（必须）
- `class_date` - 上课日期（必须）
- `lesson_number` - 课时编号（必须）

### 图片路径验证

```python
# 在使用图片前验证路径存在
import os

for img_path in data.model_images:
    if not os.path.exists(img_path):
        print(f"警告：图片不存在 {img_path}")
```

## 相关文档

- [配置系统](CONFIG_SYSTEM.md) - 如何持久化数据
- [PPT 生成](PPT_GENERATION.md) - 如何使用数据生成 PPT
