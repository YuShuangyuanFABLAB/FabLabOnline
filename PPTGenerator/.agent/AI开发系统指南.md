# 课程反馈PPT自动生成器 - AI开发系统指南

## 概述

本系统基于Anthropic的"Effective harnesses for long-running agents"文章设计，旨在让AI Agent能够跨多个上下文窗口持续开发软件项目。

**新增**: 集成多层级记忆系统，让AI能够学习和成长。

## 核心参考

**必须阅读**: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

**记忆系统参考**: https://github.com/danielmiessler/Personal_AI_Infrastructure

**本地实践指南**: `.skills/anthropic_agent_guide.md`

> 核心方法论来自Anthropic原文，补充经验基于本次PPT项目实践。
> 记忆系统理念来自Personal AI Infrastructure项目。

## 系统架构

```
.agent/                      # 增量开发系统
├── feature_list.json        # 功能列表（JSON格式，不易被误修改）
├── agent-progress.txt       # 进度日志（每次会话更新）
├── init.sh                 # 初始化脚本
├── initializer_agent.md     # 初始化Agent Prompt（项目特定）
├── coding_agent.md          # 编码Agent Prompt（项目特定）
├── test_runner.py          # 测试运行工具
└── templates/              # 通用模板

.memory/                     # 多层级记忆系统 (新增)
├── SESSION_START.md        # 会话启动指南
├── MEMORY_P0.md            # P0 热记忆（工作记忆）
├── MEMORY_P1.md            # P1 温记忆（经验教训）
├── P2/                     # P2 冷记忆（历史归档）
│   └── archive_*.md
├── telos/                  # TELOS 系统（身份定义）
│   ├── MISSION.md          # 使命
│   ├── GOALS.md            # 目标
│   ├── PROJECTS.md         # 项目
│   ├── LEARNED.md          # 学到的
│   ├── CHALLENGES.md       # 挑战
│   └── IDEAS.md            # 想法
└── maintenance/            # 维护脚本
    ├── health_check.py     # 健康检查
    └── archive_manager.py  # 归档管理

.skills/                     # 技能库
├── skill_index.json        # Skill索引
└── ppt_color_verification.md  # PPT颜色验证skill
```

## 双系统协同

### .agent 系统 - 流程控制
- 管理开发流程
- 追踪功能状态
- 记录开发进度

### .memory 系统 - 知识积累
- 存储经验教训
- 记录关键决策
- 积累项目知识

**协同方式**: 每次会话两者都会被加载，互相补充

## 两阶段Agent系统

### 阶段一：初始化Agent (Initializer Agent)

**使用时机**: 项目首次开始时

**Prompt文件**: `.agent/initializer_agent.md`

**职责**:
1. 设置项目目录结构
2. 创建基础配置文件
3. 初始化Git仓库
4. 创建依赖文件
5. 确认PPT模板可用
6. 记录初始状态

**启动方式**:
```
请阅读 .agent/initializer_agent.md 并执行其中的任务。
```

### 阶段二：编码Agent (Coding Agent)

**使用时机**: 每次开发会话

**Prompt文件**: `.agent/coding_agent.md`

**职责**:
1. 读取进度文件了解当前状态
2. 从功能列表选择下一个功能
3. 实现该功能
4. 运行测试验证
5. 更新功能状态
6. 提交代码
7. 更新进度文件

**启动方式**:
```
请阅读 .agent/coding_agent.md 并执行其中的任务。
```

## 每次会话的开始流程

### 对于Claude Code用户

**新版本（推荐）** - 集成记忆系统：

```
请阅读 .memory/SESSION_START.md 并执行会话初始化流程。
```

这会自动：
1. 读取 P0 热记忆，了解当前状态
2. 读取 TELOS 系统，了解项目身份
3. 读取开发进度，了解功能状态
4. 准备好开始工作

**原版本（简化）**:

```
我正在开发"课程反馈PPT自动生成器"项目。请执行以下步骤：

1. 读取 .memory/MEMORY_P0.md 了解当前状态
2. 读取 .agent/agent-progress.txt 了解项目状态
3. 读取 .agent/feature_list.json 了解功能列表
4. 运行 git log --oneline -10 查看最近的提交
5. 选择下一个要开发的功能并开始实现

请严格按照 .agent/coding_agent.md 中的流程执行。
```

## 关键文件说明

### feature_list.json

功能列表文件，包含所有待开发功能的详细描述。

**结构**:
```json
{
  "project_name": "课程反馈PPT自动生成器",
  "version": "1.0.0",
  "features": [
    {
      "id": "F001",
      "category": "core",
      "priority": "high",
      "description": "功能描述",
      "steps": ["步骤1", "步骤2"],
      "tests": ["测试1", "测试2"],
      "passes": false,
      "blocked_by": []
    }
  ]
}
```

**重要规则**:
- Agent只能修改 `passes` 字段
- 不能删除或修改其他字段
- 只有测试全部通过才能设置 `passes: true`

### agent-progress.txt

进度日志文件，记录每次会话的工作。

**格式**:
```markdown
### [Session X] YYYY-MM-DD - 开发
**状态**: 完成/进行中

**完成的功能**:
- [x] F001: 功能名称

**完成的工作**:
- 具体实现内容

**遇到的问题**:
- 问题和解决方案

**下一步**:
- 下一个要做的功能
```

### init.sh

初始化脚本，用于设置开发环境。

**使用**:
```bash
bash .agent/init.sh
```

## 测试运行器

test_runner.py 提供了以下命令：

```bash
# 查看项目状态
python .agent/test_runner.py status

# 获取下一个待开发功能
python .agent/test_runner.py next

# 运行指定功能的测试
python .agent/test_runner.py test F001

# 标记功能为完成
python .agent/test_runner.py complete F001

# 验证目标环境（如Office COM是否可用）
python .agent/test_runner.py verify

# 查找相关skill
python .agent/test_runner.py skill 颜色

# 查看帮助
python .agent/test_runner.py help
```

## 失败模式与解决方案

| 问题 | 解决方案 |
|------|----------|
| Agent一次性做太多 | Prompt明确要求每次只做一个功能 |
| 过早宣布完成 | 必须运行测试通过后才能标记完成 |
| 代码有bug | 会话开始时运行基本测试验证环境 |
| 不知道如何运行 | init.sh提供启动指令 |
| **测试通过但实际不正确** | 使用目标环境API验证（见下方） |
| **不知道如何诊断问题** | 查阅.skills/目录下的相关skill |

## 验证层级（重要！）

### 层级1：代码层验证
- 单元测试通过
- 集成测试通过
- **注意**：这只是代码层面正确，不等同于实际效果正确

### 层级2：目标环境验证（必须）
使用目标环境的原生API验证实际效果：

| 项目类型 | 验证方法 | 示例 |
|----------|----------|------|
| PPT生成 | PowerPoint COM API | `win32com.client.Dispatch('PowerPoint.Application')` |
| Excel生成 | Excel COM API | 逐单元格读取实际值 |
| Web应用 | 浏览器自动化 | Puppeteer/Selenium测试 |
| GUI应用 | 手动+截图验证 | 启动应用手动操作 |

### 层级3：用户视角验证
- 生成的文件在目标软件中打开检查
- 实际操作验证功能
- 视觉检查是否正确

**关键原则**：
> 代码API读取的值 ≠ 实际渲染结果
> 必须用目标环境API验证用户所见

## Skills系统

`.skills/`目录存放针对特定问题类型的解决方案：

```
.skills/
├── ppt_color_verification.md   # PPT颜色验证方法
├── (future skills...)
```

当遇到问题时：
1. 先查阅.skills/目录是否有相关skill
2. 按skill中的方法进行诊断
3. 解决后如有新经验，创建新skill

## 最佳实践

### 对于AI Agent

1. **每次只做一个功能** - 这是核心原则
2. **先测试再标记完成** - 测试不通过不能标记passes=true
3. **保持代码干净** - 每次提交的代码都应该是可运行状态
4. **详细记录进度** - 进度文件帮助下一个会话快速了解状态

### 对于人类用户

1. **监控进度** - 定期检查agent-progress.txt
2. **验证功能** - 重要功能建议手动验证
3. **提供反馈** - 如果Agent走偏，及时纠正
4. **保存会话** - 重要进展可以保存对话历史

## 常见问题

### Q: 如何继续之前中断的开发？

A: 开始新会话时使用标准启动prompt，Agent会自动读取进度文件并继续。

### Q: 如何添加新功能？

A: 在feature_list.json中添加新的功能条目，设置正确的依赖关系。

### Q: 如何修复已完成的但有bug的功能？

A: 可以将功能的passes设为false，Agent会重新处理。

### Q: 如何跳过某个功能？

A: 可以将功能标记为passes=true，或者降低优先级。

## 项目完成标准

当所有功能都标记为passes=true时，项目完成。此时应该：
1. 运行完整的测试套件
2. 进行端到端测试
3. 打包发布版本
4. 更新文档

---

## 记忆系统使用指南

### 三层记忆架构

| 层级 | 名称 | 用途 | 更新频率 |
|------|------|------|----------|
| P0 | 热记忆 | 当前任务、核心规则、最近决策 | 每次会话 |
| P1 | 温记忆 | 经验教训、最佳实践、完成的功能 | 有新经验时 |
| P2 | 冷记忆 | 历史归档、详细日志 | 自动归档 |

### 记忆写入原则

1. **记教训，不只记事件** - "为什么失败"比"失败了"更重要
2. **记模式，不只记结果** - 发现规律比记录结果更有价值
3. **记原因，不只记决定** - 决策依据比决定本身更重要

### 记忆维护命令

```bash
# 健康检查
python .memory/maintenance/health_check.py

# 查看归档状态
python .memory/maintenance/archive_manager.py status

# 执行归档
python .memory/maintenance/archive_manager.py archive
```

---

**文档版本**: 2.0
**创建日期**: 2026-02-16
**更新日期**: 2026-02-21
**参考**:
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Personal AI Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure)
