# Anthropic Long-Running Agents方法论

> **核心参考**: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
>
> 本文档仅包含Anthropic原文的核心方法论。补充经验见其他skill。

---

## 重要：适用范围

**本方法论适用于所有项目开发场景**，包括：

| 场景 | 说明 |
|------|------|
| 新项目 | 从零开始创建项目 |
| **现有项目-新功能** | 在已有项目中添加新功能 |
| **现有项目-调整功能** | 修改/优化已有功能 |
| **现有项目-修复Bug** | 修复问题并验证 |

**核心原则**：无论什么场景，都要遵循增量开发、功能列表管理、测试验证、清晰记录。

---

## 一、两阶段Agent系统

```
阶段一: Initializer Agent（初始化Agent）
  └── 首次运行时设置环境
  └── 创建功能列表（所有功能标记为passing=false）
  └── 创建init.sh脚本
  └── 创建进度文件
  └── 初始Git提交

阶段二: Coding Agent（编码Agent）
  └── 每次会话只做一个功能
  └── 测试通过后标记passing=true
  └── 提交Git并更新进度
  └── 留下清晰记录供下次会话使用
```

---

## 二、功能列表（Feature List）

**为什么用JSON不用Markdown？**
> "We use JSON for this, as the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files."

**结构示例**：
```json
{
  "category": "functional",
  "description": "New chat button creates a fresh conversation",
  "steps": [
    "Navigate to main interface",
    "Click the 'New Chat' button",
    "Verify a new conversation is created"
  ],
  "passes": false
}
```

**关键规则**：
- Agent只能修改`passes`字段
- 不能删除或修改tests字段
- "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality"

---

## 三、增量开发原则

> "We prompted the initializer agent to write a comprehensive file of feature requirements... These features were all initially marked as 'failing' so that later coding agents would have a clear outline of what full functionality looked like."

**核心原则**：
- 每次只做一个功能
- 功能必须测试通过才能标记完成
- 不允许一次性做太多

---

## 四、清晰的记录（Clean State）

> "By 'clean state' we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented."

**每个会话结束时**：
- Git提交（描述性commit message）
- 更新进度文件
- 确保代码可运行

---

## 五、会话开始流程

Anthropic建议的定位步骤：
1. 运行`pwd`确认工作目录
2. 阅读git日志和进度文件
3. 阅读功能列表，选择下一个功能
4. 运行基本测试确认环境正常

> "This approach saves Claude some tokens in every session since it doesn't have to figure out how to test the code."

---

## 六、测试验证（原文）

> "Claude mostly did well at verifying features end-to-end once explicitly prompted to use browser automation tools and do all testing as a human user would."

**关键原则**：
- 像人类用户一样测试
- 使用浏览器自动化（Web应用）
- 端到端验证

**注意**：原文主要针对Web应用。对于Office/桌面应用的测试方法，见 `testing_methodology` skill。

---

## 七、失败模式与解决方案

| 问题 | Initializer Agent行为 | Coding Agent行为 |
|------|----------------------|------------------|
| 过早宣布项目完成 | 设置详细的功能列表文件 | 会话开始时阅读功能列表，选择单个功能 |
| 留下bug或未记录进度 | 创建初始git仓库和进度文件 | 开始时阅读进度文件和git日志，结束时提交并更新 |
| 过早标记功能完成 | 设置功能列表文件 | 自我验证所有功能，仔细测试后才标记passing |
| 不知道如何运行应用 | 编写init.sh脚本 | 会话开始时阅读init.sh |

---

## 八、实施检查清单

### Initializer Agent
- [ ] 创建`.agent/`目录结构
- [ ] 创建`feature_list.json`（所有passes=false）
- [ ] 创建`init.sh`脚本
- [ ] 创建`agent-progress.txt`
- [ ] 初始Git提交

### Coding Agent（每个会话）
- [ ] 运行`pwd`确认目录
- [ ] 阅读git日志和进度文件
- [ ] 阅读功能列表
- [ ] 运行基本测试确认环境
- [ ] 选择一个功能开发
- [ ] 实现功能
- [ ] 测试验证
- [ ] 标记passes=true（仅测试通过后）
- [ ] Git提交
- [ ] 更新进度文件

---

## 九、现有项目的应用

当项目已经存在时，仍需遵循本方法论：

### 添加新功能
1. 在`feature_list.json`中添加新功能条目
2. 设置`passes: false`和正确的依赖关系
3. 按正常流程开发、测试、标记完成

### 调整已有功能
1. 在`feature_list.json`中找到对应功能
2. 将`passes`改为`false`
3. 添加修改说明到`steps`或`tests`
4. 修改代码并测试
5. 测试通过后设置`passes: true`

### 修复Bug
1. 创建新的Bug修复条目（或在相关功能中记录）
2. 描述问题、预期行为、修复方案
3. 修复后进行完整测试（包括回归测试）
4. 更新进度文件记录修复过程

### 现有项目检查清单
- [ ] 确认`.agent/`目录存在
- [ ] 确认`feature_list.json`存在且已更新
- [ ] 确认`agent-progress.txt`存在
- [ ] 新功能/修改已添加到功能列表
- [ ] 遵循增量开发原则（一次一个功能）
- [ ] 测试通过后才标记完成
- [ ] 提交Git并更新进度

---

## 相关Skills

| Skill | 用途 |
|-------|------|
| `testing_methodology` | 测试方法详解（三层验证、目标环境验证） |
| `ppt_color_verification` | PPT颜色问题诊断 |
| `skill_sync_rule` | Skill同步规则 |

---

## 参考

- **原文**: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- **作者**: Justin Young (Anthropic)
