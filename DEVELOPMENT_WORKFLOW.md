# 产品级开发工作流指南

> 基于第一性原理的分级开发策略——按任务复杂度选择最优工具组合，不搞一刀切。
>
> 与 `DEVELOPMENT_GUIDE.md`（架构与技术决策）互补，本文档聚焦**操作层面**。

---

## 0. 核心理念

两个系统各有不可替代的优势：

| 系统                             | 本质       | 不可替代的能力                                         |
| -------------------------------- | ---------- | ------------------------------------------------------ |
| **Superpowers**            | 流程框架   | 设计思考、任务分解、过程纪律、文档持久化               |
| **everything-claude-code** | 专业工具箱 | 跑 mypy/ruff/bandit 实际工具、OWASP 安全检查、构建修复 |

**最优解不是二选一，而是按复杂度分级，各司其职。**

---

## 1. 三级策略总览

```
任务来了 → 判断复杂度 → 选择 Tier
              │
              ├─ Tier 1（70%）─ 直接做 + 工具审查 → 提交
              ├─ Tier 2（20%）─ Plan mode + 双审查 → 提交
              └─ Tier 3（10%）─ Superpowers 全流程 + 专业审查 → 提交
```

| Tier             | 适用场景                                  | 流程                                                | 时间占比 |
| ---------------- | ----------------------------------------- | --------------------------------------------------- | -------- |
| **1 轻量** | Bug 修复、配置调整、1-2 文件改动、UI 微调 | 直接实现 → python-reviewer → 提交                 | 70%      |
| **2 中等** | 新增组件、修改 PPT 逻辑、跨 2-3 文件      | Plan mode → 实现 → python + security 审查 → 提交 | 20%      |
| **3 重型** | 新模块、跨模块重构、架构调整、重复 Bug    | Superpowers 全流程 + 专业审查 → 提交               | 10%      |

### 如何判断 Tier

| 信号                       | Tier |
| -------------------------- | ---- |
| 改 1-2 个文件，逻辑清晰    | 1    |
| 改 3+ 个文件，需要方案设计 | 2    |
| 新模块 / 重构 / 跨多个模块 | 3    |
| Bug 修复，根因明确         | 1    |
| Bug 修复，根因不明         | 2    |
| 同一 Bug 出现 2+ 次        | 3    |
| 配置/数据结构新增字段      | 1    |
| 配置/数据结构重大变更      | 2    |

---

## 2. Tier 1：轻量改动（70%）

**适用：** Bug 修复、配置调整、UI 微调、1-2 行改动、根因明确的修复

### 指令模板

```
[Bug 描述 / 需求描述]
复现步骤（Bug 类）：
1. [步骤1]
2. [步骤2]
期望行为：[正确行为]
实际行为：[错误行为]
```

### 流程

```
直接实现 → python-reviewer 审查 → 提交
```

**不需要** brainstorming、不需要 plan 文件、不需要 TDD。这些流程对小改动是浪费。

### 典型场景

| 场景                 | 指令                                  | 审查                 |
| -------------------- | ------------------------------------- | -------------------- |
| Bug 修复（根因明确） | 描述问题 + 复现步骤                   | python-reviewer      |
| 配置字段新增         | "新增配置项 X，更新 DEFAULT_SETTINGS" | python-reviewer      |
| UI 颜色/间距调整     | "调整 X 的 Y，同时支持双主题"         | python-reviewer      |
| 构建失败             | "修复构建错误"                        | build-error-resolver |
| 文档更新             | "更新文档反映本次改动"                | doc-updater          |

### UI 调整特别注意

```
请调整 [UI 元素] 的 [方面]。
要求：
1. 同时支持日间和夜间主题
2. 使用 ThemeManager.instance().get_colors() 获取颜色
3. 不硬编码颜色值
```

---

## 3. Tier 2：中等改动（20%）

**适用：** 新增 UI 组件/对话框、修改 PPT 生成逻辑、跨 2-3 个文件、需要方案确认

### 指令模板

```
请开发 [功能描述]。要求：
1. 先制定实现方案（进入 plan mode）
2. 新增文件放在 [对应目录]
3. 不修改 [不相关的模块]
4. 实现后同时运行 python-reviewer 和 security-reviewer
```

### 流程

```
Plan mode → 确认方案 → 实现 → python-reviewer + security-reviewer（并行）→ 提交
```

Plan mode 使用 Claude 内置能力（EnterPlanMode），不需要 Superpowers 的完整流程。

### 典型场景

| 场景            | 指令                                                   |
| --------------- | ------------------------------------------------------ |
| 新增 UI 组件    | "在 widgets/ 下新增 [组件]，先规划方案"                |
| 新增对话框      | "在 dialogs/ 下新增 [对话框]，支持双主题，先规划"      |
| 修改 PPT 生成   | "修改 content_filler.py 的 [逻辑]，先读现有代码再规划" |
| 跨 2-3 文件改动 | "实现 [功能]，涉及 [文件A] 和 [文件B]，先规划影响面"   |
| 根因不明的 Bug  | "分析 [问题]，先定位根因再修复"                        |
| 性能优化        | "[模块] 性能差，先定位瓶颈，不要猜测"                  |

### 审查策略

实现后同时派发两个审查 Agent（并行）：

```
请同时运行：
1. python-reviewer 审查代码质量
2. security-reviewer 检查安全性
```

**审查结果处理：**

- CRITICAL / HIGH → 必须修复
- MEDIUM → 根据实际情况决定
- LOW → 一般忽略

---

## 4. Tier 3：重型改动（10%）

**适用：** 新模块、跨模块重构、架构调整、同一 Bug 出现 2+ 次

### 完整 Superpowers 流程

```
/brainstorming → /writing-plans → /using-git-worktrees → /executing-plans
  → /requesting-code-review + python-reviewer + security-reviewer
  → /verification-before-completion
  → /finishing-a-development-branch → 提交
```

### 第 1 步：设计（`/brainstorming`）

```
/brainstorming
[你的功能需求]
```

**产出：** `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

Claude 通过问答逐步澄清需求，生成结构化设计文档。你必须确认后才进入下一步。

**设计阶段只读不改。**

### 第 2 步：计划（`/writing-plans`）

```
/writing-plans
```

**产出：** `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`

包含任务列表（每个 2-5 分钟）、文件改动范围、依赖关系、验证检查点。

### 第 3 步：隔离（`/using-git-worktrees`）

大功能建议在隔离分支开发：

```
/using-git-worktrees
```

| 场景                | 是否使用 |
| ------------------- | -------- |
| 新增独立文件        | 可选     |
| 修改 main_window.py | 建议     |
| 多功能并行开发      | 必须     |
| 紧急 Bug 修复       | 不需要   |

### 第 4 步：执行

**大型计划：**

```
/executing-plans docs/superpowers/plans/YYYY-MM-DD-<feature>.md
```

**超大型计划（每个任务派发独立子 Agent）：**

```
/subagent-driven-development
```

带两阶段审查：规格审查 + 代码质量审查。

**多功能并行：**

```
/dispatching-parallel-agents
我有 N 个独立任务：
1. [任务A - 涉及文件X]
2. [任务B - 涉及文件Y]
```

### 第 5 步：审查

Superpowers 审查 + everything-claude-code 专业审查并用：

```
/requesting-code-review

[同时]

python-reviewer → PEP 8、类型提示、实际跑 linter
security-reviewer → OWASP Top 10、输入验证
```

### 第 6 步：验证（`/verification-before-completion`）

```
/verification-before-completion
```

强制验证所有测试通过、无类型错误、功能符合设计。

### 第 7 步：完成（`/finishing-a-development-branch`）

```
/finishing-a-development-branch
```

检查未提交文件、确认测试、提供合并/PR 选项。

### TDD 模式

Tier 3 的核心逻辑实现推荐用 TDD：

```
/test-driven-development
```

RED（写失败测试）→ GREEN（最小实现通过）→ REFACTOR（重构）

**铁律：没有测试，不写代码。**

### 系统化调试

同一 Bug 出现 2+ 次时：

```
/systematic-debugging
这个 Bug 已经出现了 [N] 次：[Bug 描述]
```

四阶段：根因调查 → 模式分析 → 假设测试 → 实施

**铁律：没有根因，不修复。**

---

## 5. 工具速查

### Superpowers Skills

| Skill                          | 命令                                | Tier | 说明                         |
| ------------------------------ | ----------------------------------- | ---- | ---------------------------- |
| brainstorming                  | `/brainstorming`                  | 3    | 问答式需求澄清，输出设计文档 |
| writing-plans                  | `/writing-plans`                  | 3    | 设计文档 → 详细任务列表     |
| using-git-worktrees            | `/using-git-worktrees`            | 3    | 创建隔离工作区               |
| executing-plans                | `/executing-plans`                | 3    | 批量执行计划，带检查点       |
| subagent-driven-development    | `/subagent-driven-development`    | 3    | 子 Agent 两阶段审查          |
| test-driven-development        | `/test-driven-development`        | 3    | RED-GREEN-REFACTOR           |
| requesting-code-review         | `/requesting-code-review`         | 3    | 通用代码审查                 |
| verification-before-completion | `/verification-before-completion` | 3    | 完成前强制验证               |
| systematic-debugging           | `/systematic-debugging`           | 3    | 四阶段调试                   |
| dispatching-parallel-agents    | `/dispatching-parallel-agents`    | 3    | 并行独立任务                 |
| finishing-a-development-branch | `/finishing-a-development-branch` | 3    | 合并/PR/清理                 |

### everything-claude-code Agents

| Agent                    | Tier  | 说明                                                |
| ------------------------ | ----- | --------------------------------------------------- |
| `python-reviewer`      | 1/2/3 | 跑 mypy/ruff/bandit，PEP 8、类型提示、Pythonic 写法 |
| `security-reviewer`    | 2/3   | OWASP Top 10、输入验证、敏感数据                    |
| `build-error-resolver` | 1     | 最小改动快速修复构建错误                            |
| `refactor-cleaner`     | 2/3   | 自动检测清理无用代码                                |
| `doc-updater`          | 1     | 文档同步、README 更新                               |
| `architect`            | 2/3   | 系统设计、可扩展性分析                              |
| `planner`              | 2     | 实现方案规划                                        |
| `tdd-guide`            | 3     | TDD 引导，80%+ 覆盖率                               |

### 工具选择决策树

```
任务来了
│
├─ 改 1-2 文件 / 根因明确？
│   └─ Tier 1: 直接做 → python-reviewer → 提交
│
├─ 改 3+ 文件 / 需要方案？
│   └─ Tier 2: Plan mode → 实现 → python-reviewer + security-reviewer → 提交
│
├─ 新模块 / 重构 / 跨模块 / 重复 Bug？
│   └─ Tier 3: Superpowers 全流程 + 专业审查 → 提交
│
└─ 构建失败？
    └─ Tier 1: build-error-resolver
```

---

## 6. 质量保障体系

### 6.1 回归防护（所有 Tier 通用）

| 防护措施              | Tier 1 | Tier 2 | Tier 3 |
| --------------------- | ------ | ------ | ------ |
| 修改前必读            | ✅     | ✅     | ✅     |
| 最小变更              | ✅     | ✅     | ✅     |
| python-reviewer       | ✅     | ✅     | ✅     |
| security-reviewer     | —     | ✅     | ✅     |
| Plan mode 方案确认    | —     | ✅     | ✅     |
| Worktree 隔离         | —     | —     | 建议   |
| Pre-commit Hook       | ✅     | ✅     | ✅     |
| 主题双验证（UI 改动） | ✅     | ✅     | ✅     |
| Superpowers 验证流程  | —     | —     | ✅     |
| 设计文档持久化        | —     | —     | ✅     |

### 6.2 PPT 渲染验证三层体系

| 层级      | 方法                          | 可靠性                       |
| --------- | ----------------------------- | ---------------------------- |
| L1 代码层 | 单元测试、参数验证            | 验证逻辑正确                 |
| L2 API 层 | python-pptx API 输出检查      | 验证结构正确                 |
| L3 用户层 | **你手动打开 PPT 确认** | **唯一可靠的最终验证** |

**原则：** PPT 渲染问题只能通过用户实际打开验证。Claude 生成的 PPT 必须由你确认后才算通过。

### 6.3 代码质量标准

python-reviewer 的核心检查项：

| 类别   | 标准                                     |
| ------ | ---------------------------------------- |
| 格式   | PEP 8 合规                               |
| 类型   | 关键函数有类型提示                       |
| 安全   | 无硬编码密钥/路径、输入有验证            |
| 性能   | 无明显 N+1 查询、无不必要的拷贝          |
| 可读   | 函数 < 50 行、文件 < 800 行、嵌套 < 4 层 |
| 不可变 | 修改数据创建新对象，不直接修改现有对象   |

### 6.4 安全检查清单

以下场景**必须**触发 security-reviewer（Tier 2+）：

- [ ] 处理用户输入（文本框、文件选择、导入数据）
- [ ] 文件 I/O 操作（读写配置、PPT 生成）
- [ ] 子进程调用（COM 接口、PowerPoint 操作）
- [ ] 敏感数据（学员信息、配置数据）
- [ ] 外部数据导入（Excel 导入、配置导入）

---

## 7. 架构与独立性原则

### 7.1 模块边界

```
core/ ←── ui/ ←── utils/
  │         │         │
  │         │         └─ 纯工具函数，无业务逻辑
  │         └─ 界面逻辑，可调用 core
  └─ 业务逻辑，不依赖 ui
```

- `core/` 不 `import ui/`
- `ui/` 可以 `import core/`
- `utils/` 不依赖 `core/` 或 `ui/`
- 跨模块通过明确接口（函数签名、信号槽）

### 7.2 新功能添加模式

**优先级：**

1. **新增独立文件** — 最好，零侵入
2. **扩展现有文件** — 可接受
3. **修改大文件（main_window.py）** — 最后选择

```
新 UI 组件 → src/ui/widgets/new_widget.py
新对话框   → src/ui/dialogs/new_dialog.py
新核心功能 → src/core/new_module.py
新工具     → src/utils/new_util.py
```

### 7.3 main_window.py 瘦身策略

~2800 行，新增功能时：

- UI 组件 → `widgets/` 下新建，main_window 引用
- 对话框 → `dialogs/` 下新建
- 面板逻辑 → 抽取为独立 widget

**不在 main_window.py 中新增超过 50 行逻辑代码。**

### 7.4 数据流设计原则

- **单向数据流：** UI → CourseUnitData → PPTGenerator → 文件
- **避免循环依赖：** A 调用 B，B 不应再调 A
- **信号槽解耦：** 组件间通过 Qt 信号槽通信
- **数据缓存：** `_student_data_cache` 是唯一的数据中转站

### 7.5 功能独立性检查清单

每个新功能完成后验证：

- [ ] 新文件已创建（优先独立文件）
- [ ] 无硬编码依赖（不依赖其他模块内部实现）
- [ ] 接口清晰（对外暴露的函数/类有明确签名）
- [ ] 可独立测试（不需要启动整个应用）
- [ ] 可独立移除（删除新文件不会导致崩溃）
- [ ] 配置兼容（DEFAULT_SETTINGS 有默认值，旧配置自动升级）
- [ ] 主题兼容（日间/夜间模式，UI 功能）
- [ ] 导入/导出兼容（不丢失新功能数据）

---

## 8. 跨会话开发

### 8.1 会话恢复

每次新会话自动加载：

| 来源                          | 内容                    |
| ----------------------------- | ----------------------- |
| `CLAUDE.md`                 | 全局规则                |
| `memory/MEMORY.md`          | 项目记忆索引            |
| `.claude/plans/*.md`        | 未完成的 plan 文件      |
| `docs/superpowers/`         | Tier 3 的设计文档和计划 |
| `docs/DEVELOPMENT_GUIDE.md` | 架构上下文              |

**恢复指令：**

```
请读取 docs/DEVELOPMENT_WORKFLOW.md、memory/MEMORY.md、
和 docs/superpowers/ 下的相关文档，
继续 [功能] 的 [当前步骤] 开发
```

### 8.2 增量开发

**核心原则：每次只做一步，验证后继续。**

```
会话 1: /brainstorming → 设计文档 → 确认
会话 2: /writing-plans → 实施计划 → 确认
会话 3: /executing-plans（任务 1-3）→ 提交
会话 4: /executing-plans（任务 4-6）→ 提交
会话 5: /verification-before-completion → 完成
```

Tier 3 的计划文件天然支持跨会话恢复。

### 8.3 上下文溢出

1. Claude 自动 `/compact` 压缩历史
2. 关键信息保存到 memory 系统
3. 压缩后仍不够，新开会话：

```
请读取以下文件恢复上下文：
- docs/DEVELOPMENT_WORKFLOW.md
- docs/superpowers/plans/[当前计划].md
- memory/MEMORY.md
继续 [功能] 的 [当前步骤] 开发
```

### 8.4 中断恢复

| 状态          | 处理                             |
| ------------- | -------------------------------- |
| 已提交        | 安全，下次直接继续               |
| 未提交        | `git stash` 或 WIP commit      |
| 设计文档/计划 | `docs/superpowers/` 自动持久化 |

**恢复指令：**

```
检查 git status 和 docs/superpowers/，继续 [功能] 的开发
```

---

## 9. 多 Agent 协作

### 9.1 并行条件

**必须同时满足：**

- 任务之间无数据依赖
- 修改的文件不重叠
- 无共享可变状态

### 9.2 并行模式

**Tier 2/3 的审查阶段（最常用）：**

```
请同时运行：
1. python-reviewer 审查 [文件]
2. security-reviewer 检查安全性
```

**Tier 3 多任务并行：**

```
/dispatching-parallel-agents
我有 N 个独立任务：...
```

### 9.3 互不干扰原则

| 原则            | 做法                              |
| --------------- | --------------------------------- |
| 文件隔离        | 不同 Agent 不修改同一文件         |
| Worktree 隔离   | 大功能用 `/using-git-worktrees` |
| 顺序提交        | 并行完成后按顺序提交              |
| 审查不改        | 审查 Agent 只读不写               |
| 子 Agent 无状态 | 每个子 Agent 独立上下文           |

---

## 10. 异常处理

| 异常                 | 处理                                           | Tier |
| -------------------- | ---------------------------------------------- | ---- |
| 构建失败             | `build-error-resolver`                       | 1    |
| 简单 Bug             | 直接修复 +`python-reviewer`                  | 1    |
| 根因不明 Bug         | Plan mode 定位根因 → 修复                     | 2    |
| 重复 Bug（2+次）     | `/systematic-debugging`                      | 3    |
| 回归发现             | 分析原因 → 简单修/复杂 revert + 重规划        | 1-3  |
| Pre-commit Hook 警告 | 按提示补充暂存/修复语法                        | 1    |
| 上下文溢出           | `/compact` → 不够则新开会话恢复             | —   |
| 审查结果不理想       | 指出遗漏点重新审查，或补充 `python-reviewer` | —   |

### 回归处理流程

```
发现回归
  │
  ├─ 原因明确、修复简单 → Tier 1 修复
  └─ 原因复杂、影响面大 → revert + 重规划（回到对应 Tier）
```

---

## 11. 提交规范

### 提交流程（所有 Tier 通用）

```
1. git status          → 检查遗漏
2. git diff            → 确认暂存内容
3. git add [文件]      → 暂存（自动）
4. git commit          → 提交（触发 pre-commit hook）
5. 询问你是否 push     → 确认后推送
```

### Pre-commit Hook 自动检查

1. 未暂存文件警告（所有文件类型）
2. pyflakes Python 语法检查
3. 调用链完整性（`self.xxx()`、`config_manager.xxx()`）

### Commit 消息格式

```
<type>: <描述>

type: feat | fix | refactor | docs | style | perf | chore
```

### Push 前自动规则

- **README.md 必须 push 前更新**（反映本次改动）
- **全局配置变更自动同步**（`~/.claude/` → git push）

---

## 12. 文件结构

```
docs/
├── superpowers/                  # Tier 3 产物
│   ├── specs/                    # 设计文档
│   │   └── YYYY-MM-DD-<topic>-design.md
│   └── plans/                    # 实施计划
│       └── YYYY-MM-DD-<feature>.md
├── DEVELOPMENT_GUIDE.md          # 架构与技术决策
├── DEVELOPMENT_WORKFLOW.md       # 本文档
├── CHANGELOG.md                  # 变更日志
└── ...
```

---

## 13. 场景速查表

| 我想做...            | Tier | 指令                                                             |
| -------------------- | ---- | ---------------------------------------------------------------- |
| Bug 修复（根因明确） | 1    | 描述问题 → 修复 → python-reviewer                              |
| 配置字段新增         | 1    | "新增 X，更新 DEFAULT_SETTINGS" → python-reviewer               |
| UI 颜色/间距调整     | 1    | "调整 X，支持双主题" → python-reviewer                          |
| 构建失败             | 1    | "修复构建错误" → build-error-resolver                           |
| 新增 UI 组件         | 2    | "在 widgets/ 下新增 X，先规划" → python + security 审查         |
| 修改 PPT 生成逻辑    | 2    | "修改 content_filler.py，先读再规划" → python + security 审查   |
| 跨 2-3 文件改动      | 2    | "实现 X，涉及 A 和 B，先规划" → python + security 审查          |
| 性能优化             | 2    | "X 性能差，先定位瓶颈" → architect → python-reviewer           |
| 重构 main_window.py  | 3    | `/brainstorming` → `/writing-plans` → `/executing-plans` |
| 新模块               | 3    | Superpowers 全流程                                               |
| 跨模块重构           | 3    | Superpowers 全流程                                               |
| 重复 Bug（2+次）     | 3    | `/systematic-debugging`                                        |
| 多功能并行           | 3    | `/dispatching-parallel-agents`                                 |
| 更新文档             | 1    | "更新文档反映本次改动" → doc-updater                            |
| 提交推送             | —   | "提交并推送"                                                     |

---

*最后更新: 2026-04-02*
