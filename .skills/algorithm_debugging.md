# 算法调试与修复方法论

## 核心原则

> **如果同一个问题反复出现，说明没有找到根本原因。**
>
> **修补症状不如重写算法。**
>
> **用已知答案的测试用例来验证每一步。**

---

## 一、问题反复出现的根本原因

### 1.1 常见误区

| 错误行为 | 为什么会反复出错 |
|----------|-----------------|
| 只修复症状 | 根本原因没解决，换个场景又出问题 |
| 在错误基础上打补丁 | 补丁之上再加补丁，问题更难追踪 |
| 假设理解了问题 | 没有深入分析，只是猜测原因 |
| 跳过中间验证 | 不知道哪一步出错，只能瞎改 |
| 用错误方法验证 | 验证方法本身有问题 |

### 1.2 本次案例：HTML位置映射问题

**问题现象**：标记第5次出现的词汇，结果标记了第4次或第6次

**错误修复历程**：
```
第1次修复：假设是位置偏移问题 → 加了偏移量 → 仍然错误
第2次修复：假设是出现次数计算问题 → 调整计算逻辑 → 仍然错误
第3次修复：假设是HTML解析问题 → 调整正则表达式 → 仍然错误
第4次修复：完整重写算法，从段落结构解析 → ✓ 正确
```

**根本原因**：整个HTML到纯文本的映射方法在概念上就是错误的，没有正确处理Qt的`<p>`段落结构。

---

## 二、正确的调试流程

### 2.1 问题定位四步法

```
Step 1: 复现问题
        └── 创建最小可复现的测试用例
        └── 记录输入、期望输出、实际输出

Step 2: 分解问题
        └── 将复杂问题拆分成独立的小步骤
        └── 每一步都单独验证

Step 3: 打印中间结果
        └── 在每个关键点打印状态
        └── 用已知答案验证中间结果

Step 4: 找到第一个出错的步骤
        └── 二分法定位
        └── 一旦找到，分析为什么错
```

### 2.2 中间结果打印模板

```python
def debug_algorithm(input_data):
    print("=" * 60)
    print("输入数据:")
    print(f"  {input_data}")

    # Step 1
    result1 = step1(input_data)
    print(f"Step 1 结果: {result1}")
    print(f"  期望: {expected_step1}")
    print(f"  正确: {result1 == expected_step1}")

    # Step 2
    result2 = step2(result1)
    print(f"Step 2 结果: {result2}")
    print(f"  期望: {expected_step2}")
    print(f"  正确: {result2 == expected_step2}")

    # ... 更多步骤

    print("=" * 60)
    return final_result
```

### 2.3 测试用例设计原则

**必须包含的测试类型**：

| 类型 | 说明 | 示例 |
|------|------|------|
| 正常情况 | 典型输入 | 文本中出现2-3次的词汇 |
| 边界情况 | 刚好在边界 | 第1次出现、最后1次出现 |
| 极端情况 | 压力测试 | 词汇出现10次以上 |
| 特殊情况 | 可能出错的特殊输入 | 空文本、只有1个字符、全重复 |
| 反向验证 | 验证不应该发生的事 | 确保其他位置没被标记 |

---

## 三、决定重写还是修补

### 3.1 决策标准

```
应该修补：
├── 问题原因明确
├── 只需要调整参数或小范围修改
├── 现有逻辑是正确的
└── 只是个别特殊情况处理不当

应该重写：
├── 同样问题反复出现2次以上
├── 不确定问题根本原因
├── 代码已经有很多补丁
├── 核心思路可能有问题
└── 修复比重写更复杂
```

### 3.2 重写前的准备

1. **理解输入输出**：明确函数应该做什么
2. **收集测试用例**：包括成功和失败的案例
3. **分析根本原因**：为什么之前的方法不行
4. **设计新方法**：从零开始思考正确的解决方案

### 3.3 本次案例的重写思路

**旧方法**（错误）：
```python
# 逐字符遍历HTML，跳过标签，建立位置映射
html_to_plain = {}
for html_pos, char in enumerate(html):
    if char == '<':
        # 跳过标签...
    else:
        html_to_plain[html_pos] = plain_pos
        plain_pos += 1
```

**问题**：
- 没有处理HTML结构（`<p>`段落标签）
- `toPlainText()`的换行处理与直接剥离标签不同
- 位置计算存在系统性偏差

**新方法**（正确）：
```python
# 解析HTML结构，按段落重建纯文本
paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
for para_content in paragraphs:
    # 去除标签，得到段落纯文本
    para_text = re.sub(r'<[^>]+>', '', para_content)
    rebuilt_text += para_text + '\n'  # 段落间加换行

    # 在段落内查找着色span
    for span in re.finditer(span_pattern, para_content):
        # 记录span在重建文本中的位置
```

---

## 四、位置映射类问题的通用方法

### 4.1 常见的位置映射场景

| 场景 | 源格式 | 目标格式 | 注意事项 |
|------|--------|----------|----------|
| HTML到纯文本 | HTML | 纯文本 | 处理标签、实体、换行 |
| 富文本到Markdown | RTF/HTML | Markdown | 处理格式转换 |
| 代码到AST位置 | 源代码 | AST节点 | 处理空白、注释 |
| 编辑器选区到数据 | 可视化位置 | 数据索引 | 处理软换行、折叠 |

### 4.2 位置映射的正确做法

1. **不要逐字符映射**：太复杂，容易出错
2. **理解格式结构**：了解源格式的组织方式
3. **重建目标格式**：用与目标相同的方法生成文本
4. **记录关键位置**：在重建过程中记录需要的位置

### 4.3 验证位置映射正确性

```python
def verify_position_mapping(source, target, mapping_func):
    """验证位置映射是否正确"""
    # 1. 选取源中的关键位置
    test_positions = [0, len(source)//4, len(source)//2, len(source)-1]

    for src_pos in test_positions:
        # 2. 获取该位置的字符
        src_char = source[src_pos]

        # 3. 映射到目标位置
        tgt_pos = mapping_func(src_pos)

        # 4. 验证目标位置字符是否一致
        tgt_char = target[tgt_pos]

        if src_char != tgt_char:
            print(f"错误: 源位置{src_pos}的'{src_char}' 映射到 目标位置{tgt_pos}的'{tgt_char}'")
            return False

    return True
```

---

## 五、调试输出最佳实践

### 5.1 分级调试

```python
DEBUG_LEVEL = 0  # 0=关闭, 1=关键, 2=详细, 3=全部

def debug_print(level, message):
    if level <= DEBUG_LEVEL:
        print(message)

# 使用
debug_print(1, "关键步骤完成")  # 只在需要时显示
debug_print(2, f"中间变量: {var}")  # 详细调试时显示
debug_print(3, f"循环第{i}次: {state}")  # 极端调试时显示
```

### 5.2 可视化输出

对于位置相关的问题，可视化输出特别有效：

```python
def visualize_positions(text, positions):
    """可视化位置标记"""
    print("文本内容:")
    print(text)
    print("\n位置标记:")
    for i, char in enumerate(text):
        if i in positions:
            print("^", end="")  # 标记位置
        else:
            print(" ", end="")
    print()

# 示例输出：
# 文本内容:
# dksjf拉开圣诞节分厘卡圣水电费水电费
#
# 位置标记:
#     ^                    ^
```

---

## 六、案例库

### 6.1 本次案例：Qt HTML位置映射

**问题**：从QTextEdit的HTML中提取着色文字的位置

**错误方法**：逐字符遍历，跳过标签

**正确方法**：解析段落结构，重建纯文本

**教训**：
- 理解格式结构比逐字符处理更可靠
- `toPlainText()`可能有特殊处理（如段落换行）
- 用重建而非映射的方式更直观

### 6.2 案例2：PPT组合内形状高度

**问题**：修改组合内形状高度后，组合高度不更新

**根本原因**：组合高度是创建时固定的，不会自动更新

**解决方案**：解组→修改→重组，让PowerPoint重新计算

**教训**：了解数据结构的约束和限制

### 6.3 案例3：PPT边距反复变回0.5cm

**问题**：设置的0.2cm边距反复变回0.5cm（或随行数变化）

**根本原因分析**：

第一次分析（错误）：
- 认为是多个地方设置边距导致冲突

实际根本原因（第二次分析）：
- **形状高度计算公式不准确**
- python-pptx无法获取PowerPoint实际渲染的文本高度
- 用公式估算的文本高度与实际渲染高度不一致
- 结果：形状高度 = 错误的文本高度 + 2*边距 → 边距实际值偏离

**测试数据揭示问题**：

| 行数 | 预期边距 | 实际边距（公式） | 实际边距（COM） |
|------|---------|----------------|----------------|
| 5 | 0.20cm | 0.31cm | 0.20cm |
| 8 | 0.20cm | 0.41cm | 0.20cm |
| 13 | 0.20cm | 0.60cm | 0.20cm |
| 15 | 0.20cm | 0.67cm | 0.20cm |

**正确解决方案**：

使用COM API获取实际文本高度，然后计算形状高度：

```python
def adjust_shape_height_by_text(file_path: str) -> bool:
    """根据实际文本高度调整形状高度"""
    MARGIN_CM = 0.2

    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    pres = ppt_app.Presentations.Open(file_path)
    slide = pres.Slides(2)

    # 找到知识内容矩形
    for shape in slide.Shapes:
        # ... 找到Rectangle ...

        # 获取实际文本高度（COM API）
        text_height_pt = rect.TextFrame.TextRange.BoundHeight

        # 计算正确的形状高度
        margin_pt = MARGIN_CM / 2.54 * 72
        new_height_pt = text_height_pt + 2 * margin_pt

        # 设置边距和高度
        rect.TextFrame.MarginTop = margin_pt
        rect.TextFrame.MarginBottom = margin_pt
        rect.Height = new_height_pt
        break

    pres.Save()
    pres.Close()
```

**教训**：
1. **公式估算不可靠**：PowerPoint渲染行为复杂，公式估算容易出错
2. **用实际值验证**：不要假设公式正确，用COM API获取实际值验证
3. **分步测试**：测试多个不同输入（3行、5行、8行、13行等）验证边界情况
4. **理解数据关系**：边距 = (形状高度 - 文本高度) / 2，三者相互关联

---

## 七、代码维护防错原则

### 7.1 避免问题反复出现的原则

| 原则 | 说明 | 示例 |
|------|------|------|
| 单一设置点 | 每个属性只在一个地方设置 | 边距只在`_fill_knowledge_content`设置 |
| 清理死代码 | 移除不再使用的函数 | 删除`adjust_knowledge_content_height` |
| 明确注释 | 标记每个函数的职责 | `"""唯一设置边距的地方"""` |
| 测试覆盖 | 确保实际执行的代码被测试 | 用COM验证生成的PPT |

### 7.2 代码变更检查清单

```
新增/修改功能时：
□ 是否有其他地方也在设置同一属性？
  □ 如果有，是否需要统一？
  □ 是否有废弃的代码需要清理？

□ 新代码是否与现有代码冲突？
  □ 是否会覆盖其他地方的设置？

□ 是否更新了相关注释？
  □ 标记哪些函数已废弃
  □ 说明正确的调用方式

□ 是否验证了完整流程？
  □ 不是只测函数，而是测整个流程
  □ 用实际生成的文件验证
```

### 7.3 问题反复出现时的诊断步骤

```
1. 列出所有设置该属性的代码位置
   grep -rn "属性名" src/

2. 确认哪些代码实际被调用
   - 添加print/log
   - 或用调试器

3. 移除未使用的代码
   - 不要"保留备用"
   - 如果需要可以从git恢复

4. 统一到一个设置点
   - 选择最合适的位置
   - 其他地方调用这个函数

5. 添加注释说明
   - 为什么在这里设置
   - 其他已废弃的函数
```

---

## 八、检查清单

当问题反复出现时，使用此清单：

```
□ 是否理解了问题的根本原因？
  □ 是否用测试用例验证了根本原因？
  □ 是否打印了中间结果来确认？

□ 现有算法是否 fundamentally 正确？
  □ 如果不确定，考虑重写
  □ 如果已有很多补丁，考虑重写

□ 测试用例是否足够？
  □ 包含边界情况？
  □ 包含极端情况？
  □ 包含反向验证？

□ 验证方法是否正确？
  □ 不是用同样的错误逻辑验证自己
  □ 有独立的"正确答案"来源
```

---

## 参考

- **测试方法论**: `testing_methodology.md` - 三层验证体系
- **PPT颜色验证**: `ppt_color_verification.md` - PPT颜色问题调试
- **Office渲染计算**: `office_render_calculation.md` - 获取实际渲染信息
