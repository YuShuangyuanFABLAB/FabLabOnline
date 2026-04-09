# 经验总结

本文档记录开发过程中遇到的问题和解决方案。

## python-pptx 常见陷阱

### 1. 删除后添加幻灯片导致 PPT 损坏

**问题**：
python-pptx 在删除幻灯片后添加新幻灯片，会产生重复的 ZIP 条目，导致生成的 PPT 文件损坏。

**错误代码**：
```python
# 错误：先删除后添加
for i in range(10):
    delete_slide(i)  # 删除幻灯片

add_slide(layout)  # 添加新幻灯片 -> PPT 损坏！
```

**解决方案**：
采用"先添加后删除"的顺序。

```python
# 正确：先添加后添加
for i in range(10):
    add_slide(layout)  # 先添加

for i in range(10):
    delete_slide(i)  # 后删除
```

### 2. 幻灯片索引从 0 开始

**注意**：
python-pptx 使用 0-based 索引，第一个幻灯片索引为 0。

```python
slide = prs.slides[0]  # 第一张幻灯片
```

### 3. 形状操作需要操作 XML

某些高级操作（如复制形状）需要直接操作底层 XML：

```python
# 复制形状
el = shape._element
new_el = copy.deepcopy(el)
target_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')
```

### 4. 图片位置单位是 EMU

**换算**：
- 1 英寸 = 914400 EMU
- 1 厘米 = 360000 EMU

```python
from pptx.util import Inches, Emu

# 使用 Inches 更直观
left = Inches(1.5)  # 1.5 英寸

# 或使用 EMU
left = Emu(1371600)  # 等同于 1.5 英寸
```

## 布局计算

### 高度调整顺序

**原则**：先完成所有高度调整，再执行纵向分布。

**错误顺序**：
```python
# 错误：先分布后调整高度
distribute_groups_vertically(path, slide_index)
adjust_shape_height_by_text(path, slide_index)
```

**正确顺序**：
```python
# 正确：先调整高度后分布
adjust_shape_height_by_text(path, slide_index)
adjust_additional_comments_height(path, slide_index)
distribute_groups_vertically(path, slide_index)
```

**原因**：
纵向分布根据形状的当前高度计算位置，如果先分布后调整高度，位置会不准确。

## PyQt5 注意事项

### 1. 信号槽连接时机

**问题**：
在组件初始化完成之前连接信号，可能导致信号被触发多次。

**解决方案**：
使用 `blockSignals` 暂时阻止信号：

```python
self.combo.blockSignals(True)
self.combo.clear()
self.combo.addItems(items)
self.combo.setCurrentIndex(0)
self.combo.blockSignals(False)
```

### 2. 删除布局中的组件

**问题**：
直接从布局中移除组件可能导致内存泄漏或崩溃。

**正确做法**：
```python
# 清除布局中的组件
while layout.count():
    item = layout.takeAt(0)
    if item.widget():
        item.widget().deleteLater()
```

### 3. 线程安全

**问题**：
PyQt5 的 UI 操作必须在主线程中执行。

**解决方案**：
使用 `QMetaObject.invokeMethod` 或信号槽机制：

```python
# 跨线程更新 UI
self.some_signal.emit(data)  # 通过信号

# 或
QMetaObject.invokeMethod(self, "update_ui", Qt.QueuedConnection)
```

## VS Code 缓存问题

### 问题描述

在 VS Code 终端中运行 Python 程序时，修改代码后可能仍运行旧版本。

### 原因

VS Code 的 Python 扩展会缓存 .pyc 文件。

### 解决方案

1. **清除 __pycache__**：
   ```bash
   rm -rf src/__pycache__ src/**/__pycache__
   ```

2. **使用 -B 参数**：
   ```bash
   python -B main.py
   ```

3. **设置环境变量**：
   ```bash
   set PYTHONDONTWRITEBYTECODE=1
   ```

4. **重启 VS Code**

## 路径处理

### 中文路径问题

**问题**：
某些操作在中文路径下可能失败。

**解决方案**：
1. 使用 `pathlib.Path` 而非字符串
2. 确保编码正确

```python
# 正确
path = Path("D:/项目/文件.txt")
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 避免
path = "D:/项目/文件.txt"  # 可能出问题
```

### 相对路径 vs 绝对路径

**原则**：
- 读取资源：使用相对于 `get_base_path()` 的路径
- 写入配置：使用相对于 `get_app_dir()` 的路径

```python
# 读取模板
template = get_base_path() / "templates" / "课程反馈.pptx"

# 写入配置
config_file = get_app_dir() / "config" / "settings.json"
```

## 文本颜色标记

### 问题

在 python-pptx 中设置文字颜色时，需要操作 XML 而非简单地设置属性。

### 解决方案

```python
def set_run_color(run, color_hex: str):
    """设置 run 的颜色"""
    rPr = run._r.get_or_add_rPr()

    # 移除现有填充
    for child in list(rPr):
        if child.tag == qn('a:solidFill'):
            rPr.remove(child)

    # 添加新的填充
    solidFill = etree.SubElement(rPr, qn('a:solidFill'))
    srgbClr = etree.SubElement(solidFill, qn('a:srgbClr'))
    srgbClr.set('val', color_hex)

    # 同时设置 python-pptx 属性
    run.font.color.rgb = RGBColor.from_string(color_hex)
```

## 批量生成优化

### 内存管理

**问题**：
批量生成大量 PPT 时可能占用过多内存。

**解决方案**：
1. 每生成一个 PPT 后释放资源
2. 使用生成器而非列表

```python
def generate_all(self, data_list):
    for data in data_list:
        generator = PPTGenerator(template_path)
        # ... 生成 PPT
        generator = None  # 释放资源
        gc.collect()  # 强制垃圾回收
```

### 进度反馈

使用回调函数提供进度反馈：

```python
def generate_all(self, data_list, progress_callback=None):
    total = len(data_list)
    for i, data in enumerate(data_list):
        if progress_callback:
            progress_callback(i + 1, total, data.student_name)
        # ... 生成
```

## 调试技巧

### 1. 保存中间结果

在调试 PPT 生成时，保存中间结果：

```python
# 保存中间结果
prs.save("debug_step1.pptx")

# 修改后保存
prs.save("debug_step2.pptx")
```

### 2. 打印 XML

```python
from lxml import etree

# 打印形状的 XML
print(etree.tostring(shape._element, pretty_print=True).decode())
```

### 3. 检查幻灯片数量

```python
print(f"幻灯片数量: {len(prs.slides)}")
for i, slide in enumerate(prs.slides):
    print(f"  [{i}] {slide.slide_layout.name}")
```

## 性能优化

### 图片处理

1. 使用缩略图预览，而非加载原图
2. 批量处理时复用 ImageProcessor 实例
3. 使用 BytesIO 而非临时文件

```python
# 使用 BytesIO
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)
slide.shapes.add_picture(img_bytes, left, top, width, height)
```

### 配置文件

1. 避免频繁读写配置文件
2. 使用内存缓存 + 定期保存

```python
class ConfigManager:
    def __init__(self):
        self._settings = {}
        self._dirty = False

    def set(self, key, value):
        self._settings[key] = value
        self._dirty = True

    def save_if_dirty(self):
        if self._dirty:
            self.save_settings()
            self._dirty = False
```

## 相关文档

- [PPT 生成](PPT_GENERATION.md) - 生成逻辑详解
- [打包部署](BUILD_DEPLOY.md) - 打包注意事项
