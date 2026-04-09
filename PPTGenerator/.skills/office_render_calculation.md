# Office文档渲染计算 - 获取实际渲染信息与正确计算

## 核心问题

> **python-docx、python-pptx等库只能操作XML，无法获取实际渲染结果。**
>
> **要获取实际渲染信息（行数、换行位置、实际尺寸），必须使用Office COM API。**

---

## 一、两种API的区别

| 方面 | python-pptx / python-docx | Office COM API |
|------|---------------------------|----------------|
| 操作对象 | XML结构 | 实际渲染对象 |
| 能获取的信息 | XML中设置的值 | 实际渲染结果 |
| 行数/换行 | 无法获取 | 可以获取 `TextRange.Lines().Count` |
| 文本实际高度 | 无法获取 | 可以获取 `TextRange.BoundHeight` |
| 适用场景 | 创建/修改文档 | 获取渲染信息、精确调整 |

---

## 二、单位转换

### 基本单位关系

```
1 inch = 914400 EMU = 72 points = 2.54 cm
1 point = 12700 EMU
1 cm = 914400/2.54 ≈ 360000 EMU
```

### 转换公式

```python
# EMU ↔ cm
emu_to_cm = emu / 914400 * 2.54
cm_to_emu = cm * 914400 / 2.54

# EMU ↔ points
emu_to_pt = emu / 12700
pt_to_emu = pt * 12700

# cm ↔ points (COM API常用)
cm_to_pt = cm / 2.54 * 72
pt_to_cm = pt / 72 * 2.54
```

### COM API使用points

```python
import win32com.client

# COM API的高度/边距等使用points单位
MARGIN_PT = 0.2 / 2.54 * 72  # 0.2cm → points

rect.Height = height_pt
rect.TextFrame.MarginTop = margin_pt
```

---

## 三、获取实际渲染信息

### 获取文本行数

```python
import win32com.client

ppt_app = win32com.client.Dispatch("PowerPoint.Application")
pres = ppt_app.ActivePresentation  # 或 ppt_app.Presentations.Open(file)
slide = pres.Slides(slide_index)

# 对于普通形状
shape = slide.Shapes(shape_index)
lines_count = shape.TextFrame.TextRange.Lines().Count

# 对于组合内的形状
group = slide.Shapes(group_index)
item = group.GroupItems.Item(item_index)
lines_count = item.TextFrame.TextRange.Lines().Count
```

### 获取每行内容

```python
tr = shape.TextFrame.TextRange
for i in range(1, tr.Lines().Count + 1):
    line = tr.Lines(i)
    print(f"行{i}: {line.Text} (长度: {len(line.Text)})")
```

### 获取文本边界

```python
tr = shape.TextFrame.TextRange
print(f"BoundHeight: {tr.BoundHeight}")  # 文本实际高度
print(f"BoundWidth: {tr.BoundWidth}")    # 文本实际宽度
print(f"BoundTop: {tr.BoundTop}")        # 文本顶部位置
print(f"BoundLeft: {tr.BoundLeft}")      # 文本左侧位置
```

---

## 四、正确的尺寸计算公式

### 文本高度计算

**错误公式**：
```
文本高度 = 每行高度 × 行数  ❌
```

**正确公式**：
```
文本高度 = 文字高度 × 行数 + 行间距 × (行数 - 1)  ✓
```

### 参数确定方法

1. **文字高度**：由字体大小决定（如11pt = 0.388cm）
2. **行间距**：通过用户提供的数据反推

**反推示例**：
```
已知：15行文字高度为6.85cm，字体11pt
公式：6.85 = 0.388 × 15 + 行间距 × 14
计算：6.85 = 5.82 + 行间距 × 14
      行间距 = (6.85 - 5.82) / 14 = 0.0735cm
```

### 完整计算代码

```python
# 参数（基于用户验证数据）
FONT_SIZE_CM = 11 * 2.54 / 72  # 0.388cm
LINE_SPACING_CM = 0.0735  # 通过反推获得
MARGIN_CM = 0.2

# 获取行数
lines_count = text_range.Lines().Count

# 计算文本高度（正确公式）
text_height_cm = FONT_SIZE_CM * lines_count + LINE_SPACING_CM * (lines_count - 1)

# 计算容器高度
container_height_cm = text_height_cm + 2 * MARGIN_CM

# 转换为points设置
FONT_SIZE_PT = FONT_SIZE_CM / 2.54 * 72
LINE_SPACING_PT = LINE_SPACING_CM / 2.54 * 72
MARGIN_PT = MARGIN_CM / 2.54 * 72

text_height_pt = FONT_SIZE_PT * lines_count + LINE_SPACING_PT * (lines_count - 1)
container_height_pt = text_height_pt + 2 * MARGIN_PT
```

---

## 五、组合内形状的修改

### 问题

组合（Group）内的形状无法直接修改尺寸。

### 解决方案

```python
# 1. 解组
ungrouped = group_shape.Ungroup()

# 2. 修改
for i in range(1, ungrouped.Count + 1):
    item = ungrouped.Item(i)
    if "目标形状名" in item.Name:
        item.Height = new_height
        item.TextFrame.MarginTop = margin
        break

# 3. 重新组合
ungrouped.Regroup()
```

---

## 六、开发流程

### 推荐流程

```
Step 1: 用python-pptx设置内容和格式
        └── 填充文本、设置边距、设置对齐方式

Step 2: 保存文件

Step 3: 用COM API获取渲染信息
        └── 获取实际行数
        └── 计算正确尺寸

Step 4: 用COM API调整尺寸
        └── 解组（如需要）
        └── 设置高度/边距
        └── 重新组合（如需要）

Step 5: 用户确认
        └── 打开文件让用户检查实际效果
        └── 根据反馈调整参数
```

### 参数校准流程

```
1. 用户提供实测数据（如：N行文字高度为X cm）
2. 用正确公式反推参数
3. 用反推参数计算并测试
4. 用户确认效果
5. 确定最终参数
```

---

## 七、常见错误

| 错误 | 正确做法 |
|------|----------|
| 用python-pptx估算行数 | 用COM API获取实际行数 |
| 文本高度 = 行高×行数 | 文本高度 = 字高×行数 + 行间距×(行数-1) |
| 假设1cm=914400EMU | 1cm=914400/2.54≈360000EMU |
| COM API使用EMU单位 | COM API使用points单位 |
| 直接修改组合内形状 | 先解组，修改后重新组合 |
| 用自己估算的参数 | 用用户提供的数据反推参数 |
| 在python-pptx中调用COM调整 | 保存后单独调用COM后处理 |
| 用python-pptx名称匹配COM形状 | 注意名称差异：中文"矩形" vs 英文"Rectangle" |

---

## 八、组合高度问题

### 问题现象

修改组合内形状的尺寸后，组合的高度不会自动更新，导致组合高度与内部形状实际范围不一致。

**示例**：
- 组合高度：8.36cm
- 内部形状实际范围：4.43cm
- 差异：3.93cm

### 原因

组合的高度是在创建时固定的，修改内部形状不会自动更新组合高度。只有解组再重组时，PowerPoint才会重新计算组合的边界框。

### 解决方案

使用解组→修改→重组的方式，PowerPoint会自动重新计算组合高度：

```python
# 解组
ungrouped = group.Ungroup()

# 修改内部形状
for i in range(1, ungrouped.Count + 1):
    item = ungrouped.Item(i)
    if "目标形状" in item.Name:
        item.Height = new_height
        break

# 重新组合（自动计算新的组合边界）
ungrouped.Regroup()
```

### 形状名称差异

python-pptx和COM API中的形状名称可能不同：

| python-pptx | COM API |
|-------------|---------|
| 矩形 224 | Rectangle 224 |
| 文本框 223 | TextBox 224 |
| 组合 7 | Group 7 |

**匹配代码**：
```python
# 名称转换
shape_name_com = shape.name.replace("矩形", "Rectangle").replace("文本框", "TextBox")
```

---

## 九、本Skill的适用场景

- PPT/Word文档需要根据内容自动调整容器尺寸
- 需要获取文本实际渲染的行数或换行位置
- 需要精确计算文本占用的空间
- Office文档的精确布局控制

---

## 参考

- **测试方法论**: `testing_methodology.md` - 三层验证体系
- **PPT颜色验证**: `ppt_color_verification.md` - PPT渲染相关问题
