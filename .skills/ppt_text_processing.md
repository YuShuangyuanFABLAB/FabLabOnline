# PPT文本处理与颜色标记

## 适用场景

- PPT生成后文本颜色显示不正确
- 需要根据用户选择的颜色标记特定文本
- 从富文本编辑器提取着色文本并映射到PPT
- 复选框、特殊符号字体相关的问题

---

## 一、颜色标记的正确流程

### 1.1 完整流程

```
用户操作                    系统处理                      PPT输出
─────────────────────────────────────────────────────────────────
1. 用户在编辑器中           2. 提取HTML和纯文本
   选择文本并着色              ↓
                           3. 从HTML中提取着色文本
                              并计算出现位置
                              ↓
                           4. 转换为(词汇, 出现次数)格式
                              ↓
                           5. 在PPT中找到对应位置
                              ↓
                           6. 应用颜色到指定位置
```

### 1.2 关键点：出现次数计算

**问题**：同一词汇可能出现多次，如何确定用户标记的是第几次？

**解决方案**：
1. 解析HTML结构，按段落重建纯文本
2. 找到着色span在重建文本中的位置
3. 根据位置计算是第几次出现

---

## 二、从HTML提取着色文本

### 2.1 Qt HTML格式特点

```html
<!-- Qt的HTML格式 -->
<p style="...">普通文本<span style=" color:#ed7d31;">着色文本</span>普通文本</p>
<p style="...">第二段落内容</p>
```

**特点**：
- 使用`<p>`标签表示段落
- 段落之间在`toPlainText()`中会产生换行
- 颜色使用`style`属性中的`color:#RRGGBB`

### 2.2 错误的提取方法

```python
# ❌ 错误：逐字符遍历建立位置映射
html_to_plain = {}
plain_pos = 0
for html_pos, char in enumerate(html):
    if char == '<':
        # 跳过标签...
    else:
        html_to_plain[html_pos] = plain_pos
        plain_pos += 1
```

**问题**：没有考虑`<p>`段落标签产生的换行

### 2.3 正确的提取方法

```python
import re

def extract_colored_words(html: str, plain_text: str, target_color):
    """从HTML中提取指定颜色的文字及其出现索引"""

    target_hex = target_color.name().lower()
    colored_spans = []
    rebuilt_text = ""
    current_pos = 0

    # 按段落解析
    p_pattern = r'<p[^>]*>(.*?)</p>'
    span_pattern = r'<span[^>]*color\s*:\s*#([0-9a-fA-F]{6})[^>]*>([^<]+)</span>'

    paragraphs = re.findall(p_pattern, html, re.DOTALL)

    for para_idx, para_content in enumerate(paragraphs):
        # 段落间加换行
        if para_idx > 0:
            rebuilt_text += '\n'
            current_pos += 1

        # 获取段落纯文本
        para_text_only = re.sub(r'<[^>]+>', '', para_content)

        # 找到着色span并记录位置
        for span_match in re.finditer(span_pattern, para_content, re.IGNORECASE):
            color_hex = '#' + span_match.group(1).lower()
            span_text = span_match.group(2)

            # 计算span在段落中的位置
            text_before = re.sub(r'<[^>]+>', '', para_content[:span_match.start()])
            span_start = current_pos + len(text_before)

            if color_hex == target_hex:
                colored_spans.append((span_start, span_start + len(span_text), span_text))

        rebuilt_text += para_text_only
        current_pos += len(para_text_only)

    # 计算每个着色span的出现索引
    markers = []
    for abs_start, abs_end, span_text in colored_spans:
        word = span_text.strip()
        if word:
            occurrence = count_occurrences_up_to(plain_text, word, abs_start)
            markers.append((word, occurrence))

    return markers

def count_occurrences_up_to(text: str, word: str, position: int) -> int:
    """计算在position位置之前，word出现了几次"""
    count = 0
    pos = 0
    while True:
        found = text.find(word, pos)
        if found == -1 or found > position:
            break
        count += 1
        pos = found + len(word)
    return count
```

---

## 三、在PPT中应用颜色

### 3.1 支持出现索引的文本分割

```python
HIGHLIGHT_COLOR = RGBColor(0x00, 0x70, 0xC0)  # 重点-蓝色
DIFFICULTY_COLOR = RGBColor(0xED, 0x7D, 0x31)  # 难点-橙色

def split_text_by_markers(content: str, highlights: List, difficulties: List):
    """
    根据标记分割文本，支持指定出现次数

    Args:
        highlights: [("词汇", 出现次数), ...]
        difficulties: [("词汇", 出现次数), ...]
    """

    def find_nth_occurrence(text: str, word: str, n: int) -> int:
        """找第n次出现的位置（n从1开始）"""
        start = 0
        for i in range(n):
            pos = text.find(word, start)
            if pos == -1:
                return -1
            if i == n - 1:
                return pos
            start = pos + len(word)
        return -1

    markers = []

    for word, occurrence in highlights:
        pos = find_nth_occurrence(content, word, occurrence)
        if pos != -1:
            markers.append((pos, pos + len(word), word, HIGHLIGHT_COLOR))

    for word, occurrence in difficulties:
        pos = find_nth_occurrence(content, word, occurrence)
        if pos != -1:
            markers.append((pos, pos + len(word), word, DIFFICULTY_COLOR))

    # 按位置排序，去除重叠
    markers.sort(key=lambda x: x[0])
    # ... 分割文本并应用颜色
```

### 3.2 颜色应用

```python
def set_colored_text(paragraph, segments: List[tuple]):
    """根据分段设置带颜色的文本"""
    for text, color in segments:
        run = paragraph.add_run()
        run.text = text

        if color:
            run.font.color.rgb = color
        else:
            run.font.color.rgb = DEFAULT_TEXT_COLOR  # #404040
```

---

## 四、复选框颜色问题

### 4.1 问题描述

复选框使用Wingdings字体（\uf052或\uf0a3），颜色设置可能无效。

### 4.2 原因

XML元素顺序影响渲染，`solidFill`必须在`sym`之前：

```xml
<!-- ❌ 错误顺序 -->
<a:rPr>
  <a:sym typeface="Wingdings"/>
  <a:solidFill><a:srgbClr val="ED7D31"/></a:solidFill>
</a:rPr>

<!-- ✓ 正确顺序 -->
<a:rPr>
  <a:solidFill><a:srgbClr val="ED7D31"/></a:solidFill>
  <a:sym typeface="Wingdings"/>
</a:rPr>
```

### 4.3 修复代码

```python
from lxml import etree
from pptx.oxml.ns import qn

def set_checkbox_color(run, color_rgb):
    """设置复选框颜色（确保元素顺序正确）"""
    rPr = run._r.get_or_add_rPr()

    # 创建solidFill
    solidFill = etree.SubElement(rPr, f'{qn("a:")}solidFill')
    srgbClr = etree.SubElement(solidFill, f'{qn("a:")}srgbClr')
    srgbClr.set('val', color_rgb)

    # 确保sym在solidFill之后
    sym = rPr.find(qn('a:sym'))
    if sym is not None:
        sym_index = list(rPr).index(sym)
        solidFill_index = list(rPr).index(solidFill)
        if sym_index < solidFill_index:
            # 交换位置
            rPr.remove(solidFill)
            rPr.insert(sym_index, solidFill)
```

---

## 五、验证方法

### 5.1 使用COM读取实际颜色

```python
import win32com.client

def verify_colors(ppt_path):
    """验证PPT中的实际颜色"""
    ppt = win32com.client.Dispatch('PowerPoint.Application')
    pres = ppt.Presentations.Open(ppt_path)

    for slide in pres.Slides:
        for shape in slide.Shapes:
            check_shape_colors(shape)

    pres.Close()

def check_shape_colors(shape):
    """递归检查形状颜色"""
    if shape.Type == 6:  # msoGroup
        for i in range(1, shape.GroupItems.Count + 1):
            check_shape_colors(shape.GroupItems(i))
    elif shape.HasTextFrame:
        tr = shape.TextFrame.TextRange
        for i in range(1, tr.Length + 1):
            char = tr.Characters(i, 1)
            rgb = char.Font.Color.RGB
            r, g, b = rgb & 0xFF, (rgb >> 8) & 0xFF, (rgb >> 16) & 0xFF
            print(f'"{char.Text}" = RGB({r},{g},{b})')
```

### 5.2 测试用例设计

```python
def test_occurrence_detection():
    """测试出现次数检测"""

    # 测试文本（包含重复词汇）
    text = """dksjf拉开圣诞节分厘卡圣水电费水电费
dksjf拉开圣诞节分厘卡圣水电费水电费
dksjf拉开圣诞节分厘卡圣水电费水电费"""

    # 测试用例
    test_cases = [
        ("dksjf", 1, "第1次出现"),
        ("dksjf", 2, "第2次出现"),
        ("dksjf", 3, "第3次出现"),
        ("拉开圣诞节分厘卡圣", 1, "第1次出现"),
        ("拉开圣诞节分厘卡圣", 3, "第3次出现"),
    ]

    for word, expected_occ, desc in test_cases:
        actual_pos = find_nth_occurrence(text, word, expected_occ)
        print(f"{desc}: 位置={actual_pos}")

        # 验证位置正确
        assert text[actual_pos:actual_pos+len(word)] == word
```

---

## 六、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 所有出现都被着色 | 没有使用出现索引 | 使用`(词汇, 出现次数)`格式 |
| 标记位置错误 | 位置映射算法错误 | 按段落重建文本 |
| 颜色不生效 | XML元素顺序错误 | solidFill在sym之前 |
| 复选框显示默认色 | sym元素被覆盖 | 检查XML结构 |
| 出现次数计算错误 | 位置计算偏差 | 打印中间结果验证 |

---

## 七、调试技巧

### 7.1 打印位置映射

```python
def debug_position_mapping(html, plain_text):
    """调试位置映射"""
    print("HTML长度:", len(html))
    print("纯文本长度:", len(plain_text))

    # 打印每个段落
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    for i, para in enumerate(paragraphs):
        text = re.sub(r'<[^>]+>', '', para)
        print(f"段落{i}: '{text}' (长度{len(text)})")

    # 打印所有词汇出现位置
    for word in ["dksjf", "其他词汇"]:
        pos = 0
        occ = 0
        while True:
            found = plain_text.find(word, pos)
            if found == -1:
                break
            occ += 1
            print(f"'{word}' 第{occ}次: 位置{found}")
            pos = found + len(word)
```

### 7.2 可视化标记结果

```python
def visualize_markers(content, markers):
    """可视化标记结果"""
    print("内容:", content)
    print("位置:", end="")
    for i, char in enumerate(content):
        marked = any(start <= i < end for start, end, _, _ in markers)
        print("^" if marked else " ", end="")
    print()

    for start, end, word, color in markers:
        color_name = "蓝色" if color == HIGHLIGHT_COLOR else "橙色"
        print(f"  {word} ({color_name}): 位置{start}-{end}")
```

---

## 参考

- **算法调试方法**: `algorithm_debugging.md` - 调试方法论
- **测试方法论**: `testing_methodology.md` - 三层验证体系
- **Office渲染计算**: `office_render_calculation.md` - 获取实际渲染信息
