# P1 温记忆 (Warm Memory)

> 需要的时候能想起来 - 已完成任务、踩过的坑、学到的教训

---

## 经验教训

### E004: 批量生成与单独生成流程不一致
**日期**: 2026-02-24
**类别**: 批量功能
**问题**:
批量生成的PPT缺失功能（图片展示页、系列名称、后处理效果），但单独生成正确。

**根因**:
`BatchGenerator.generate_all()` 没有复用单独生成的逻辑，缺少：
- 图片数量参数传递
- 系列信息传递
- 后处理步骤（高度调整、布局分布）

**解决方案**:
修改 `BatchTask` 添加 series_name/series_level 字段，generate_all() 完整传递参数并执行后处理。

**修改文件**:
- `src/core/batch_generator.py`
- `src/ui/dialogs/batch_progress_dialog.py`
- `src/ui/main_window.py`

**提交**: `c096a6f`

**教训**:
- 批量处理应该与单独处理使用相同的底层逻辑
- 如果必须分开实现，应逐一对比参数和处理步骤
- 测试时必须对比两种路径的输出

---

### E001: PPT 颜色验证陷阱
**日期**: 2026-02-16
**类别**: PPT 开发
**问题**:
使用 `run.font.color.rgb` 读取的颜色值与 PowerPoint 实际渲染颜色不一致。

**发现过程**:
测试代码显示颜色正确，但用 PowerPoint 打开发现颜色不对。

**解决方案**:
使用 PowerPoint COM API 进行验证：
```python
import win32com.client
ppt = win32com.client.Dispatch('PowerPoint.Application')
# 用 COM API 读取实际颜色
```

**教训**:
- 代码 API 读取的值 ≠ 实际渲染结果
- 必须用目标环境的原生 API 验证
- PPT 相关功能都需要最终打开文件确认

---

### E002: 组合形状文本处理
**日期**: 2026-02-16
**类别**: PPT 开发
**问题**:
PPT 中的组合形状内的文本无法通过简单遍历访问。

**解决方案**:
实现递归查找算法：
```python
def find_text_in_shape(shape):
    if shape.has_text_frame:
        return shape.text_frame
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for child in shape.group_items:
            result = find_text_in_shape(child)
            if result:
                return result
    return None
```

**教训**:
- PPT 结构比想象的更复杂
- 需要处理各种嵌套情况
- 永远不要假设形状是扁平的

---

### E003: python-pptx 的局限性
**日期**: 2026-02-16
**类别**: PPT 开发
**问题**:
python-pptx 无法处理某些 PPT 特性，如：
- 复杂的动画
- 某些形状属性
- 原生 SmartArt

**解决方案**:
- 对于简单操作使用 python-pptx
- 对于复杂操作使用 COM API
- 混合使用两者

**教训**:
- 了解工具的边界
- 准备备选方案
- 不强行用不合适的工具

---

## 完成的关键功能

### F001-F004: 核心框架
- 项目结构设计
- 配置管理
- 数据模型
- PPT 模板管理

### F005-F012: PPT 功能
- 课程信息填充
- 重点/难点标记
- 评价复选框
- 区域分布
- 图片处理
- 图片嵌入
- 新页面添加
- PPT 保存

### F013-F019: UI 组件
- PyQt5 主窗口
- 母版选择
- 课程信息输入
- 富文本编辑器
- 评价选择
- 图片上传
- 图片裁剪

### F020-F023: 数据导入
- Excel 模板
- Excel 读取
- 导入对话框
- 表单序列化

### F024-F027: 高级功能
- PPT 预览
- 批量生成
- 集成测试
- 打包发布

---

## 最佳实践

### BP001: 测试驱动修复
当发现 bug 时：
1. 先写一个能复现问题的测试
2. 运行测试确认复现
3. 修复代码
4. 确认测试通过
5. 手动验证实际效果

### BP002: 三层验证法
1. **代码层**: pytest 单元测试
2. **环境层**: COM API 或实际软件验证
3. **用户层**: 打开文件手动检查

### BP003: 增量提交
- 每完成一个小功能就提交
- 提交信息清晰描述改动
- 保持代码处于可运行状态

---

## 常见问题解决

### Q: 如何验证 PPT 颜色是否正确？
A: 用 PowerPoint COM API 或直接打开文件查看

### Q: 如何处理组合形状中的文本？
A: 使用递归算法遍历所有子形状

### Q: 如何调试 PPT 生成问题？
A:
1. 生成 PPT 文件
2. 用 PowerPoint 打开
3. 逐项检查
4. 对比模板找差异

---

*最后更新: 2026-02-21*
*条目数: 3 个经验教训*
