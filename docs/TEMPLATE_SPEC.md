# 模板规范

本文档描述 PPT 模板的结构要求。

## 模板文件

- **路径**：`templates/课程反馈.pptx`
- **格式**：PowerPoint 2007+ (.pptx)

## 幻灯片布局

模板必须包含以下 7 种布局（按索引顺序）：

| 索引 | 布局名称 | 用途 |
|------|----------|------|
| 0 | 4_标题和内容 | 封面页 |
| 1 | 标题和内容 | 课程信息页 |
| 2 | 3_标题和内容 | 精彩瞬间页 |
| 3 | 5_标题和内容 | 车辆展示页 |
| 4 | 2_标题和内容 | 程序展示页 |
| 5 | 1_标题和内容 | 双图布局 |
| 6 | 6_标题和内容 | 模型展示页 |

## 页面结构

### 封面页（布局 0）

包含元素：
- 课程系列名称（橙色 #FF6224）
- 副标题（浅蓝色 #D3F1F0）：`FABLAB法贝实验室 — — 机械臂设计（1阶）课程`

**需要替换的文本**：
- `机械臂设计` → 系列名称
- `机械臂设计（1阶）课程` → 系列（阶数）课程

### 课程信息页（布局 1）

包含元素：
- 课时编号：`（第 1 课）`
- 课程内容：`机械臂设计（1阶）`
- 学生姓名：`赵如一`
- 授课教师：`于双源`
- 课时数：`2课时`
- 上课日期：`2025.7.23 18:30-20:30`

**课堂评价区域**（12 项复选框）：

| 位置 | 评价项 |
|------|--------|
| 左列 1 | 专注度与效率 |
| 左列 2 | 课堂听课习惯 |
| 左列 3 | 课堂任务完成 |
| 左列 4 | 课堂内容理解 |
| 左列 5 | 知识熟练程度 |
| 左列 6 | 学习方法习惯 |
| 右列 1 | 动手实践能力 |
| 右列 2 | 逻辑思维表现 |
| 右列 3 | 想象力与创新 |
| 右列 4 | 独立分析思考 |
| 右列 5 | 解决问题表现 |
| 右列 6 | 挫折困难应对 |

**总体评价**（4 个选项）：
- 优、良、仍需努力、需要改进

**上次作业**（5 个选项）：
- 优、良、中、差、无

**文本区域**：
- 课堂知识内容
- 补充说明
- 课程作业
- 注意事项

### 模型展示页（布局 6）

包含元素：
- 标题文本框
- 图片占位区域

**图片位置**（EMU）：
```python
{
    "left": 507918,
    "top": 1436402,
    "width": 5842163,
    "height": 6546959
}
```

### 精彩瞬间页（布局 2）

包含元素：
- 标题文本框
- 图片占位区域

**图片位置**（EMU）：
```python
{
    "left": 405000,
    "top": 1114428,
    "width": 6048000,
    "height": 7560000
}
```

## 颜色配置

### 主题颜色

| 用途 | 颜色值 | RGB |
|------|--------|-----|
| 重点标记 | #0070C0 | (0, 112, 192) |
| 难点标记 | #ED7D31 | (237, 125, 49) |
| 标题背景 | #D3F1F0 | (211, 241, 240) |
| 强调色 | #36A4A4 | (54, 164, 164) |
| 默认文字 | #404040 | (64, 64, 64) |

### 配置文件

```json
// config/colors.json
{
    "highlight_color": "0070C0",
    "difficulty_color": "ED7D31",
    "header_color": "D3F1F0",
    "accent_color": "36A4A4"
}
```

## 字体要求

### 主要字体

| 场景 | 字体 |
|------|------|
| 中文正文 | 等线 |
| 西文正文 | -apple-system |
| 标题装饰 | 华文琥珀 |

### 字体文件

- 位置：`fonts/STHUPO.TTF`
- 用途：标题装饰

### 字体检测

程序启动时会检测系统是否安装"华文琥珀"字体，如未安装则提示用户安装。

```python
# src/utils/font_helper.py
def check_required_fonts():
    """检查必需字体"""
    required_fonts = ["华文琥珀", "等线"]
    missing = []
    for font in required_fonts:
        if not is_font_installed(font):
            missing.append(font)
    return missing
```

## 文本框命名

模板中的关键文本框应使用有意义的名称：

| 文本框内容 | 建议名称 |
|------------|----------|
| 课程系列 | series_name |
| 课时编号 | lesson_number |
| 学生姓名 | student_name |
| 教师姓名 | teacher_name |
| 知识内容 | knowledge_content |
| 补充说明 | additional_comments |

## 复选框结构

### 评价复选框

每个评价项有 5 个复选框（优、良、中、差、未体现），使用形状组合实现：

```
评价组
├── 优 (复选框)
├── 良 (复选框)
├── 中 (复选框)
├── 差 (复选框)
└── 未体现 (复选框)
```

### CheckboxHandler

使用 `CheckboxHandler` 类操作复选框：

```python
from src.core.checkbox_handler import CheckboxHandler

handler = CheckboxHandler(slide)

# 设置第 0 项评价为"优"
handler.set_evaluation(0, "优")

# 设置总体评价
handler.set_overall_evaluation("良")

# 设置作业评价
handler.set_homework_evaluation("无")
```

## 图片规格

### 推荐尺寸

| 布局类型 | 宽度 (英寸) | 高度 (英寸) |
|----------|-------------|-------------|
| model | 6.55 | 8.07 |
| work | 6.55 | 8.07 |
| program | 6.55 | 8.07 |
| vehicle | 6.55 | 8.07 |
| double_image | 3.2 | 4.0 |

### 支持的图片格式

- JPG / JPEG
- PNG
- BMP
- GIF
- WebP
- TIFF

## 模板验证

### 验证方法

```python
generator = PPTGenerator(template_path)
result = generator.verify_template()

# 返回结果
{
    "valid": True/False,
    "template_path": "...",
    "layout_count": 7,
    "layouts": {
        "cover": {"name": "4_标题和内容", "found": True},
        "course_info": {"name": "标题和内容", "found": True},
        # ...
    },
    "errors": []  # 错误信息列表
}
```

### 验证条件

1. 所有 7 种布局都存在
2. 布局名称正确
3. 关键文本框存在
4. 复选框结构完整

## 模板修改注意事项

### 不要修改

1. 布局名称
2. 布局索引顺序
3. 复选框组合结构
4. 占位符文本（如"赵如一"、"于双源"）

### 可以修改

1. 页面背景颜色
2. 文本框位置和大小
3. 字体大小（保持字体名称）
4. 装饰元素位置

### 修改后验证

每次修改模板后，应运行验证：

```python
from src.core.ppt_generator import PPTGenerator

gen = PPTGenerator("templates/课程反馈.pptx")
result = gen.verify_template()

if not result["valid"]:
    for error in result["errors"]:
        print(f"错误: {error}")
```

## 相关文档

- [PPT 生成](PPT_GENERATION.md) - 如何使用模板生成 PPT
- [颜色配置](CONFIG_SYSTEM.md) - 配置文件详解
