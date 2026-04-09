# PPT布局计算完全指南

## 核心原则

> **不要用公式估算PowerPoint的渲染结果，要用COM API获取实际值。**
>
> **边距 = (形状高度 - 文本高度) / 2**

---

## 一、为什么公式估算不可靠

### 1.1 PowerPoint渲染的复杂性

PowerPoint在渲染文本时考虑的因素：

| 因素 | 说明 | 影响 |
|------|------|------|
| 字体类型 | 不同字体高度不同 | 西文字体vs中文字体 |
| 字号 | 磅值转换 | 11pt ≈ 0.388cm |
| 行间距 | 行与行之间的距离 | 公式难以准确计算 |
| 段落间距 | 段落之间的距离 | 与行间距不同 |
| 文本框内边距 | 上下左右边距 | tIns/bIns/lIns/rIns |
| 垂直对齐 | top/ctr/btm | 影响文本位置但不影响边距 |

### 1.2 实测数据：公式vs实际

**测试条件**：11pt字体，设置边距0.2cm

| 行数 | 公式计算高度 | 实际文本高度 | 差异 |
|------|------------|------------|------|
| 3 | 1.65cm | 1.40cm | +0.25cm |
| 5 | 2.52cm | 2.33cm | +0.19cm |
| 8 | 3.82cm | 3.73cm | +0.09cm |
| 10 | 4.69cm | 4.66cm | +0.03cm |
| 13 | 5.98cm | 6.05cm | -0.07cm |
| 15 | 6.85cm | 6.99cm | -0.14cm |

**结论**：公式与实际渲染不一致，误差随行数变化。

---

## 二、正确的计算方法：使用COM API

### 2.1 获取实际文本高度

```python
import win32com.client

ppt_app = win32com.client.Dispatch("PowerPoint.Application")
pres = ppt_app.Presentations.Open(file_path)
slide = pres.Slides(slide_index)

shape = slide.Shapes(shape_index)

# 获取实际文本高度（这是关键！）
text_height_pt = shape.TextFrame.TextRange.BoundHeight

# 转换为cm
text_height_cm = text_height_pt / 72 * 2.54
```

### 2.2 设置正确的形状高度

```python
# 目标边距
MARGIN_CM = 0.2

# 转换为points
margin_pt = MARGIN_CM / 2.54 * 72  # ≈ 5.67pt

# 计算形状高度 = 文本高度 + 2 * 边距
new_height_pt = text_height_pt + 2 * margin_pt

# 设置边距和高度
shape.TextFrame.MarginTop = margin_pt
shape.TextFrame.MarginBottom = margin_pt
shape.Height = new_height_pt
```

### 2.3 验证实际边距

```python
# 验证：边距 = (形状高度 - 文本高度) / 2
actual_margin_cm = (shape.Height / 72 * 2.54 - text_height_cm) / 2
print(f"实际边距: {actual_margin_cm:.2f} cm")  # 应该是0.20cm
```

---

## 三、关键属性说明

### 3.1 文本框边距属性

| 属性 | XML名称 | 说明 | 单位 |
|------|---------|------|------|
| MarginTop | tIns | 上边距 | points/EMU |
| MarginBottom | bIns | 下边距 | points/EMU |
| MarginLeft | lIns | 左边距 | points/EMU |
| MarginRight | rIns | 右边距 | points/EMU |

**python-pptx设置方式**：
```python
from pptx.util import Emu

margin = Emu(int(0.2 * 914400 / 2.54))  # 0.2cm → EMU
bodyPr = text_frame._bodyPr
bodyPr.set('tIns', str(int(margin)))
bodyPr.set('bIns', str(int(margin)))
```

**COM API设置方式**：
```python
margin_pt = 0.2 / 2.54 * 72  # 0.2cm → points
shape.TextFrame.MarginTop = margin_pt
shape.TextFrame.MarginBottom = margin_pt
```

### 3.2 文本高度属性

| 属性 | 说明 | 单位 |
|------|------|------|
| TextRange.BoundHeight | 文本实际占用高度 | points |
| TextRange.BoundWidth | 文本实际占用宽度 | points |
| TextRange.Lines().Count | 文本行数 | 行 |

### 3.3 形状高度属性

| 属性 | python-pptx | COM API |
|------|-------------|---------|
| 高度 | shape.height (EMU) | shape.Height (points) |
| 宽度 | shape.width (EMU) | shape.Width (points) |

---

## 四、组合形状的特殊处理

### 4.1 组合形状的高度问题

修改组合内形状的高度后，组合的高度不会自动更新。

**解决方案**：同时更新组合的边界框

```python
def _update_group_bounds(child_shape, original_height_emu, new_height_emu):
    """更新包含子形状的组合的边界框"""
    height_diff = new_height_emu - original_height_emu

    if height_diff == 0:
        return

    child_element = child_shape._element
    current = child_element

    while current is not None:
        parent = current.getparent()
        if parent is None:
            break

        if parent.tag == qn('p:grpSp'):
            grpSpPr = parent.find(qn('p:grpSpPr'))
            if grpSpPr is not None:
                xfrm = grpSpPr.find(qn('a:xfrm'))
                if xfrm is not None:
                    # 更新视觉大小 (ext)
                    ext = xfrm.find(qn('a:ext'))
                    if ext is not None:
                        old_cy = int(ext.get('cy', 0))
                        ext.set('cy', str(old_cy + height_diff))

                    # 更新子形状坐标系 (chExt)
                    chExt = xfrm.find(qn('a:chExt'))
                    if chExt is not None:
                        old_cy = int(chExt.get('cy', 0))
                        chExt.set('cy', str(old_cy + height_diff))
            break

        current = parent
```

### 4.2 COM API处理组合

```python
# 如果需要修改组合内形状
group = slide.Shapes(group_index)

# 方法1：解组→修改→重组
ungrouped = group.Ungroup()
for i in range(1, ungrouped.Count + 1):
    item = ungrouped.Item(i)
    # 修改item...
ungrouped.Regroup()

# 方法2：直接访问组合内形状
for i in range(1, group.GroupItems.Count + 1):
    item = group.GroupItems.Item(i)
    # 修改item...
```

---

## 五、完整工作流程

### 5.1 使用python-pptx创建内容

```python
from pptx import Presentation
from pptx.util import Emu

# 1. 加载模板
prs = Presentation('template.pptx')
slide = prs.slides[1]

# 2. 找到内容形状并设置文本
shape = find_content_shape(slide)
tf = shape.text_frame

# 3. 设置边距（python-pptx）
margin = Emu(int(0.2 * 914400 / 2.54))
bodyPr = tf._bodyPr
bodyPr.set('tIns', str(int(margin)))
bodyPr.set('bIns', str(int(margin)))

# 4. 填充文本内容
for line in lines:
    p = tf.add_paragraph()
    p.text = line

# 5. 保存
prs.save('output.pptx')
```

### 5.2 使用COM API后处理

```python
import win32com.client

# 1. 打开文件
ppt_app = win32com.client.Dispatch("PowerPoint.Application")
ppt_app.Visible = True
pres = ppt_app.Presentations.Open('output.pptx')

# 2. 找到内容形状
slide = pres.Slides(2)
shape = find_content_shape_com(slide)

# 3. 获取实际文本高度
text_height_pt = shape.TextFrame.TextRange.BoundHeight

# 4. 计算并设置正确的高度
margin_pt = 0.2 / 2.54 * 72
new_height_pt = text_height_pt + 2 * margin_pt

shape.TextFrame.MarginTop = margin_pt
shape.TextFrame.MarginBottom = margin_pt
shape.Height = new_height_pt

# 5. 保存
pres.Save()
pres.Close()
```

---

## 六、常见问题与解决方案

### 6.1 边距随行数变化

**问题**：设置边距0.2cm，实际显示0.3-0.7cm不等

**原因**：形状高度使用公式估算，与实际文本高度不匹配

**解决**：使用COM API获取实际文本高度后重新计算形状高度

### 6.2 组合高度不更新

**问题**：修改组合内形状后，组合边界不正确

**原因**：组合高度在创建时固定，不会自动更新

**解决**：同时更新 `a:ext` 和 `a:chExt` 属性

### 6.3 文本垂直居中问题

**问题**：设置anchor='ctr'后边距计算异常

**说明**：anchor只影响文本在形状内的对齐方式，不影响边距

**计算**：无论anchor是什么，边距 = (形状高度 - 文本高度) / 2

### 6.4 多段落文本

**问题**：多个段落的高度如何计算？

**说明**：`TextRange.BoundHeight` 返回所有段落的总高度，包括段落间距

**处理**：直接使用BoundHeight，无需单独处理段落

---

## 七、单位转换参考

| 单位 | 转换公式 |
|------|---------|
| cm → pt | pt = cm / 2.54 * 72 |
| pt → cm | cm = pt / 72 * 2.54 |
| cm → EMU | EMU = cm / 2.54 * 914400 |
| EMU → cm | cm = EMU / 914400 * 2.54 |
| pt → EMU | EMU = pt * 12700 |
| EMU → pt | pt = EMU / 12700 |

---

## 八、调试技巧

### 8.1 打印所有相关值

```python
def debug_shape_dimensions(shape):
    """调试形状尺寸"""
    tf = shape.TextFrame

    print(f"形状高度: {shape.Height / 72 * 2.54:.2f} cm")
    print(f"文本高度: {tf.TextRange.BoundHeight / 72 * 2.54:.2f} cm")
    print(f"上边距: {tf.MarginTop / 72 * 2.54:.2f} cm")
    print(f"下边距: {tf.MarginBottom / 72 * 2.54:.2f} cm")
    print(f"实际边距: {(shape.Height - tf.TextRange.BoundHeight) / 2 / 72 * 2.54:.2f} cm")
    print(f"行数: {tf.TextRange.Lines().Count}")
```

### 8.2 验证公式

```python
# 边距公式验证
expected_margin = 0.2  # cm
actual_margin = (shape.Height - tf.TextRange.BoundHeight) / 2 / 72 * 2.54
error = abs(actual_margin - expected_margin)

if error < 0.05:  # 允许0.05cm误差
    print(f"✓ 边距正确: {actual_margin:.2f} cm")
else:
    print(f"✗ 边距错误: 期望{expected_margin}cm, 实际{actual_margin:.2f}cm")
```

---

## 九、变更记录

- 2026-02-20: 创建文档，记录边距计算的正确方法
- 2026-02-20: 添加组合形状处理、单位转换等内容

---

## 参考

- **代码变更追溯**: `code_change_tracking.md`
- **算法调试方法**: `algorithm_debugging.md`
- **测试方法论**: `testing_methodology.md`
