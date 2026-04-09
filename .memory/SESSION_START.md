# 会话启动指南

> 每次新会话开始时，请按以下流程操作

---

## 快速启动

```
请阅读 .memory/SESSION_START.md 并执行会话初始化流程。
```

---

## 初始化流程

### 第一步：读取记忆

按顺序读取以下文件，了解项目当前状态：

1. **P0 热记忆** (必读)
   ```
   .memory/MEMORY_P0.md
   ```
   - 当前任务
   - 核心规则
   - 最近决策
   - 项目上下文

2. **TELOS 系统** (首次会话必读)
   ```
   .memory/telos/MISSION.md    # 使命
   .memory/telos/GOALS.md      # 目标
   .memory/telos/PROJECTS.md   # 项目
   ```

### 第二步：检查开发系统

读取增量开发系统文件：

```
.agent/agent-progress.txt    # 开发进度
.agent/feature_list.json     # 功能列表
```

### 第三步：确认环境

```bash
pwd                          # 确认工作目录
git status                   # 检查 Git 状态
git log --oneline -5         # 查看最近提交
```

---

## 根据任务类型选择流程

### 类型 A：继续开发任务

如果继续之前的功能开发：

1. 读取 `.agent/coding_agent.md`
2. 按照其中的流程执行

### 类型 B：修复问题

如果需要修复问题：

1. 查阅 `.memory/MEMORY_P1.md` 中的经验教训
2. 参考 `.skills/` 目录中的相关 skill
3. 按修复流程执行

### 类型 C：新功能请求

如果是新功能请求：

1. 评估是否符合 `.memory/telos/GOALS.md` 中的目标
2. 更新 `.agent/feature_list.json` 添加新功能
3. 按增量开发流程执行

---

## 会话结束时

### 记录进度

1. 更新 `.agent/agent-progress.txt`
2. 如有重要决策，更新 `.memory/MEMORY_P0.md`
3. 如有新经验，添加到 `.memory/MEMORY_P1.md`

### 提交代码

```bash
git add .
git commit -m "描述性的提交信息"
```

---

## 记忆维护

### 定期执行（每周一次）

```bash
python .memory/maintenance/health_check.py
```

### 归档检查（每月一次）

```bash
python .memory/maintenance/archive_manager.py status
```

---

## 常用命令速查

```bash
# 启动程序
python main.py

# 运行测试
python test_all.py

# 打包
python build.py

# 记忆健康检查
python .memory/maintenance/health_check.py

# 记忆归档状态
python .memory/maintenance/archive_manager.py status
```

---

*记住：有记忆的 AI 才能成长*
