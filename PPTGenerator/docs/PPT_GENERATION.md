# PPT 生成逻辑

本文档描述 PPT 生成的核心流程，涉及 `PPTGenerator` 和 `ContentFiller` 类。

## 概述

PPT 生成分为以下步骤：

1. **加载模板** - 读取 `templates/课程反馈.pptx`
2. **生成页面结构** - 根据布局配置添加/删除幻灯片
3. **填充内容** - 将课程数据写入 PPT
4. **后处理** - 调整高度、布局
5. **保存文件** - 输出到指定目录

## PPTGenerator 类

位于 `src/core/ppt_generator.py`。

### 布局索引映射

模板中有 7 种布局：

```python
LAYOUT_INDEX = {
    "cover": 0,           # 4_标题和内容 - 封面页
    "course_info": 1,     # 标题和内容 - 课程信息页
    "work": 2,            # 3_标题和内容 - 精彩瞬间页
    "vehicle": 3,         # 5_标题和内容 - 车辆展示页
    "program": 4,         # 2_标题和内容 - 程序展示页
    "double_image": 5,    # 1_标题和内容 - 双图布局
    "model": 6,           # 6_标题和内容 - 模型展示页
}
```

### 初始化

```python
from src.core.ppt_generator import PPTGenerator

generator = PPTGenerator("templates/课程反馈.pptx")
```

### 生成流程

#### generate_from_template()

核心方法，根据配置生成 PPT 页面结构。

```python
def generate_from_template(
    self,
    layout_config: LayoutConfig,
    model_image_count: int = 0,
    work_image_count: int = 0,
    program_image_count: int = 0,
    vehicle_image_count: int = 0,
    include_cover: bool = True
) -> bool:
```

**重要原则：先添加后删除**

> python-pptx 在删除幻灯片后添加新幻灯片会产生重复的 ZIP 条目，导致 PPT 损坏。
> 因此必须**先添加新幻灯片，后删除不需要的幻灯片**。

**页面顺序**：
```
封面（可选）→ 课程信息 → 模型展示页(N张) → 程序展示页(P张) → 车辆展示页(V张) → 精彩瞬间(M张)
```

**处理步骤**：

1. 重新加载模板
2. 获取需要的布局对象
3. **先添加**新幻灯片（按顺序：模型→程序→车辆→精彩瞬间）
4. **后删除**不需要的原始幻灯片
5. 保存到临时文件
6. 重新加载文件

#### 示例

```python
from src.core.models import LayoutConfig

layout = LayoutConfig(
    include_course_info=True,
    include_model_display=True,
    include_work_display=True
)

generator.generate_from_template(
    layout,
    model_image_count=2,    # 2 张模型图 = 2 页模型展示
    work_image_count=3,     # 3 张精彩瞬间 = 3 页精彩瞬间
    include_cover=True      # 第1课包含封面
)
```

### 图片处理

#### 图片位置配置

```python
IMAGE_POSITIONS = {
    "model": {
        "left": 507918, "top": 1436402,
        "width": 5842163, "height": 6546959
    },
    "work": {
        "left": 405000, "top": 1114428,
        "width": 6048000, "height": 7560000
    },
    # ... 其他布局类似
}
```

> 位置单位为 EMU（English Metric Unit），1 英寸 = 914400 EMU

#### 插入图片

```python
# 基本插入
generator.insert_image(slide, image_path, left, top, width, height)

# 根据布局类型插入（自动选择位置和尺寸）
generator.insert_image_for_layout(slide, image_path, "model")

# 带裁剪的插入
generator.insert_image(
    slide, image_path, left, top, width, height,
    layout_type="model"  # 自动裁剪保持比例
)
```

### 幻灯片管理

#### 复制幻灯片

```python
new_slide = generator.duplicate_slide(slide_index)
```

#### 删除幻灯片

```python
generator.delete_slide(slide_index)
generator.delete_slides_after(keep_count)  # 保留前 N 页
```

### 保存

```python
# 生成文件名
filename = PPTGenerator.generate_filename(
    student_name="张三",
    lesson_number=1,
    prefix="课程反馈"
)
# 返回: "张三_第1课_课程反馈_20250115_143000.pptx"

# 保存
success = generator.save(output_path)

# 或使用数据自动命名
success, path = generator.save_course_unit(output_dir, unit_data)
```

## ContentFiller 类

位于 `src/core/content_filler.py`。

### 功能

将 `CourseUnitData` 中的数据填充到 PPT 幻灯片中。

### 颜色常量

```python
DEFAULT_TEXT_COLOR = RGBColor(0x40, 0x40, 0x40)  # #404040 默认文字
HIGHLIGHT_COLOR = RGBColor(0x00, 0x70, 0xC0)    # #0070C0 重点-蓝色
DIFFICULTY_COLOR = RGBColor(0xED, 0x7D, 31)     # #ED7D31 难点-橙色
```

### 填充课程信息

```python
from src.core.content_filler import ContentFiller

filler = ContentFiller(presentation)
filler.fill_course_info(
    data=course_data,
    series_name="机械臂设计",
    series_level=1,
    slide_index=1  # 有封面时为1，无封面时为0
)
```

#### 替换逻辑

1. **基本信息替换**
   - 课时编号：`（第 1 课）` → `（第 N 课）`
   - 课程内容：`机械臂设计（1阶）` → 用户填写的内容
   - 学生姓名：`赵如一` → 学生姓名
   - 授课教师：`于双源` → 教师姓名
   - 课时数：`2课时` → `N课时`
   - 上课日期：`2025.7.23 18:30-20:30` → 实际日期

2. **评价复选框处理**
   - 使用 `CheckboxHandler` 处理 12 项评价
   - 自动勾选对应的评价等级

3. **补充文本替换**
   - 补充说明、课堂作业、注意事项

4. **知识内容填充**
   - 支持多段文本（自动编号）
   - 重点/难点颜色标记

### 填充封面

```python
filler.fill_cover_series(
    series_name="机械臂设计",
    series_level=1
)
```

替换封面页中的课程系列名称。

### 填充图片页

```python
# 填充图片到指定幻灯片
filler.fill_image_slide(slide, image_path, layout_type)
```

## 批量生成

### BatchGenerator 类

位于 `src/core/batch_generator.py`。

```python
from src.core.batch_generator import BatchGenerator

batch = BatchGenerator(template_path)

# 添加任务
batch.add_task(data1, series_name="机械臂设计", series_level=1)
batch.add_task(data2, series_name="机械臂设计", series_level=1)

# 设置进度回调
def on_progress(current, total, student_name):
    print(f"正在生成 {current}/{total}: {student_name}")

batch.set_progress_callback(on_progress)

# 执行批量生成
result = batch.generate_all(
    output_dir="output",
    layout_config=layout,
    overwrite=True
)

print(f"成功: {result.success}, 失败: {result.failed}")
```

### 取消批量

```python
batch.cancel()  # 设置取消标志
```

## 后处理函数

在 `content_filler.py` 中定义，用于调整生成后的 PPT。

### adjust_shape_height_by_text()

根据文本内容自动调整形状高度。

```python
adjust_shape_height_by_text(ppt_path, slide_index)
```

### distribute_groups_vertically()

纵向均匀分布多个组合。

```python
distribute_groups_vertically(ppt_path, slide_index)
```

### adjust_additional_comments_height()

调整补充说明区域高度。

```python
adjust_additional_comments_height(ppt_path, slide_index)
```

### 后处理顺序

**重要**：必须按以下顺序执行：

```python
# 1. 先完成所有高度调整
adjust_shape_height_by_text(path, slide_index)
adjust_additional_comments_height(path, slide_index)

# 2. 最后执行纵向分布
distribute_groups_vertically(path, slide_index)
```

> 先调整高度再分布，否则分布位置会不准确。

## 完整生成流程示例

```python
from src.core.models import CourseUnitData, LayoutConfig
from src.core.ppt_generator import PPTGenerator
from src.core.content_filler import fill_ppt_content

# 1. 准备数据
data = CourseUnitData(
    lesson_number=1,
    student_name="张三",
    teacher_name="李老师",
    class_hours=2,
    class_date="2025.1.15 14:00-16:00",
    model_images=["model1.jpg"],
    work_images=["work1.jpg", "work2.jpg"]
)

layout = LayoutConfig(
    include_course_info=True,
    include_model_display=True,
    include_work_display=True
)

# 2. 创建生成器
generator = PPTGenerator("templates/课程反馈.pptx")

# 3. 生成页面结构
generator.generate_from_template(
    layout,
    model_image_count=len(data.model_images),
    work_image_count=len(data.work_images),
    include_cover=(data.lesson_number == 1)
)

# 4. 填充内容
fill_ppt_content(
    generator.prs, data,
    series_name="机械臂设计",
    series_level=1,
    model_image_count=len(data.model_images),
    work_image_count=len(data.work_images),
    include_cover=(data.lesson_number == 1)
)

# 5. 保存
success, path = generator.save_course_unit("output", data)

# 6. 后处理
if success:
    slide_index = 2 if data.lesson_number == 1 else 1
    adjust_shape_height_by_text(path, slide_index)
    adjust_additional_comments_height(path, slide_index)
    distribute_groups_vertically(path, slide_index)
```

## 常见陷阱

### python-pptx 删除后添加 bug

**问题**：删除幻灯片后添加新幻灯片会产生重复的 ZIP 条目，导致 PPT 损坏。

**解决方案**：采用"先添加后删除"的顺序。

### 幻灯片索引

- python-pptx 使用 0-based 索引
- 有封面时，课程信息页索引为 1
- 无封面时，课程信息页索引为 0

### 图片路径

- 必须使用绝对路径或相对于当前工作目录的路径
- 中文路径可能导致问题，建议使用英文路径

## 相关文档

- [数据模型](DATA_MODELS.md) - CourseUnitData 定义
- [模板规范](TEMPLATE_SPEC.md) - PPT 模板要求
- [经验总结](EXPERIENCE_NOTES.md) - 更多陷阱和解决方案
