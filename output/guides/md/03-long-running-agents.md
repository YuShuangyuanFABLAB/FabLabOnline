# 长期运行Agent

> 来源：https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
> 发布日期：2025-11-26

---

## 一、核心问题

Agent跨多个上下文窗口工作的挑战：
- **无记忆**：每个新会话开始时没有之前记忆
- **上下文有限**：单个会话能处理的内容有限
- **复杂性**：复杂项目无法在单个窗口内完成

**关键洞察**：让Agent一次只处理一个功能，通过结构化记录实现跨会话连续性。

---

## 二、两阶段解决方案

### 2.1 初始化Agent（第一个会话）

**职责**：
- 理解项目需求
- 设计系统架构
- 创建功能列表
- 设置初始环境

**产出**：
- `init.sh` 启动脚本
- `claude-progress.txt` 进度日志
- `features.json` 功能列表
- 初始git提交

### 2.2 编码Agent（后续会话）

**职责**：
- 读取进度文件了解状态
- 选择一个功能实现
- 做出增量进度
- 留下结构化更新

**每个会话流程**：
```
1. 运行 pwd 确认工作目录
2. 读取 git logs 和 progress files
3. 读取 features list，选择最高优先级未完成功能
4. 运行 init.sh 启动开发服务器
5. 运行基本端到端测试
6. 开始实现新功能
7. 提交进度
8. 更新进度文件
```

---

## 三、功能列表设计

### 3.1 结构定义

```json
{
  "project": "Project Name",
  "version": "1.0.0",
  "features": [
    {
      "id": "F001",
      "category": "functional",
      "priority": "high",
      "description": "New chat button creates a fresh conversation",
      "steps": [
        "Navigate to main interface",
        "Click the 'New Chat' button",
        "Verify a new conversation is created"
      ],
      "acceptance_criteria": [
        "Conversation list shows new entry",
        "Previous conversation is preserved"
      ],
      "passes": false,
      "notes": ""
    }
  ]
}
```

### 3.2 字段说明

| 字段 | 说明 |
|------|------|
| id | 唯一标识符，如F001 |
| category | functional/ui/performance/security |
| priority | high/medium/low |
| description | 功能描述 |
| steps | 实现步骤 |
| acceptance_criteria | 验收标准 |
| passes | 是否通过（只能从false改为true） |
| notes | 备注 |

### 3.3 设计原则

1. **原子性**：每个功能独立可测试
2. **可验证**：有明确的验收标准
3. **优先级**：有清晰的实现顺序
4. **增量性**：每会话只处理一个

---

## 四、增量进度机制

### 4.1 进度文件格式

```
# claude-progress.txt

## 2025-01-15 Session 1 (Initialization)
- Created project structure
- Implemented F001: User authentication
- Status: F001 passed
- Next: F002 Dashboard layout

## 2025-01-16 Session 2
- Working on F002: Dashboard layout
- Completed sidebar component
- Issue: Mobile responsiveness needs work
- Status: F002 in progress
- Next: Continue F002, fix mobile layout

## 2025-01-17 Session 3
- Fixed mobile layout issues
- Completed F002
- Status: F002 passed
- Next: F003 Data visualization
```

### 4.2 提交策略

**每个会话结束时**：
1. 用描述性提交消息提交进度到git
2. 在进度文件中写摘要
3. 更新功能列表状态

**提交消息格式**：
```
feat(F003): Add data visualization charts

- Implement line chart component
- Add data filtering options
- Include responsive design
- Tests: 85% coverage

Progress: F003 passed, moving to F004
```

---

## 五、实战案例

### 案例1：电商平台开发

**场景**：使用长期运行Agent开发一个完整的电商平台

**初始化Agent输出**：

```json
{
  "project": "E-Commerce Platform",
  "features": [
    {
      "id": "F001",
      "category": "auth",
      "priority": "high",
      "description": "User registration and login",
      "steps": [
        "Create registration form UI",
        "Implement email validation",
        "Set up JWT authentication",
        "Add password hashing",
        "Create login form UI"
      ],
      "acceptance_criteria": [
        "User can register with email",
        "Password is securely stored",
        "JWT token is issued on login",
        "Protected routes work"
      ],
      "passes": false
    },
    {
      "id": "F002",
      "category": "functional",
      "priority": "high",
      "description": "Product catalog display",
      "steps": [
        "Create product card component",
        "Implement product listing page",
        "Add category filtering",
        "Implement search functionality"
      ],
      "acceptance_criteria": [
        "Products display correctly",
        "Filtering works by category",
        "Search returns relevant results"
      ],
      "passes": false
    },
    {
      "id": "F003",
      "category": "functional",
      "priority": "high",
      "description": "Shopping cart functionality",
      "steps": [
        "Create cart state management",
        "Implement add to cart",
        "Implement remove from cart",
        "Add quantity adjustment",
        "Calculate cart total"
      ],
      "acceptance_criteria": [
        "Cart persists across sessions",
        "Quantities update correctly",
        "Total calculation is accurate"
      ],
      "passes": false
    }
  ]
}
```

**init.sh脚本**：
```bash
#!/bin/bash
echo "Starting E-Commerce Platform development..."

# 安装依赖
npm install

# 设置环境变量
cp .env.example .env

# 初始化数据库
npm run db:migrate
npm run db:seed

# 启动开发服务器
npm run dev &

# 等待服务器启动
sleep 5

# 运行基本测试
npm run test:e2e:smoke

echo "Environment ready!"
```

**进度追踪示例**：
```
## Session 5 (2025-01-20)
Feature: F003 - Shopping cart

Completed:
- [x] Cart state with Zustand
- [x] Add to cart button on product cards
- [x] Cart sidebar component
- [x] Quantity controls

Tests run: 12/12 passed
Coverage: 92%

Issues: None
Status: F003 PASSED ✓

Next session: F004 - Checkout flow
```

**效果**：
- 10个功能按计划完成
- 每个功能都有测试覆盖
- 代码可追溯，易于调试

---

### 案例2：SaaS后台管理系统

**场景**：开发一个多租户SaaS后台

**功能列表设计**：
```json
{
  "features": [
    {
      "id": "F001",
      "category": "auth",
      "description": "Multi-tenant authentication",
      "priority": "high",
      "dependencies": [],
      "passes": false
    },
    {
      "id": "F002",
      "category": "functional",
      "description": "Tenant isolation middleware",
      "priority": "high",
      "dependencies": ["F001"],
      "passes": false
    },
    {
      "id": "F003",
      "category": "functional",
      "description": "User management within tenant",
      "priority": "high",
      "dependencies": ["F001", "F002"],
      "passes": false
    },
    {
      "id": "F004",
      "category": "ui",
      "description": "Admin dashboard",
      "priority": "medium",
      "dependencies": ["F003"],
      "passes": false
    }
  ]
}
```

**会话启动流程**：
```python
# 编码Agent的会话启动

def start_session():
    # 1. 确认工作目录
    assert os.getcwd() == "/project/saas-admin"

    # 2. 读取git历史
    recent_commits = git.log("-5", "--oneline")
    print(f"Recent commits:\n{recent_commits}")

    # 3. 读取进度文件
    progress = read_file("claude-progress.txt")
    print(f"Last session summary:\n{progress[-500:]}")

    # 4. 读取功能列表
    features = json.load(open("features.json"))
    incomplete = [f for f in features if not f["passes"]]
    current = incomplete[0]  # 最高优先级未完成

    print(f"Current feature: {current['id']} - {current['description']}")

    # 5. 检查依赖
    deps = current.get("dependencies", [])
    unmet = [d for d in deps if not is_completed(d)]
    if unmet:
        raise Exception(f"Unmet dependencies: {unmet}")

    # 6. 启动开发环境
    run("./init.sh")

    # 7. 运行冒烟测试
    run("npm run test:smoke")

    return current
```

**依赖管理**：
- Agent自动检查依赖是否满足
- 不满足时跳过或报告
- 确保功能按正确顺序实现

**效果**：
- 依赖关系清晰
- 不会遗漏前置条件
- 实现顺序合理

---

### 案例3：移动App后端API

**场景**：开发RESTful API服务

**功能列表**：
```json
{
  "features": [
    {
      "id": "API001",
      "category": "api",
      "description": "User endpoints (CRUD)",
      "endpoints": ["GET /users", "POST /users", "PUT /users/:id", "DELETE /users/:id"],
      "passes": false
    },
    {
      "id": "API002",
      "category": "api",
      "description": "Authentication endpoints",
      "endpoints": ["POST /auth/login", "POST /auth/register", "POST /auth/refresh"],
      "passes": false
    },
    {
      "id": "API003",
      "category": "api",
      "description": "File upload endpoint",
      "endpoints": ["POST /upload", "GET /files/:id"],
      "passes": false
    }
  ]
}
```

**API测试集成**：
```bash
# init.sh 包含API测试

# 启动服务器
npm run dev &
SERVER_PID=$!

# 等待启动
sleep 5

# 运行API测试
newman run tests/api-collection.json

# 健康检查
curl -f http://localhost:3000/health || exit 1

echo "API ready for development"
```

**进度记录模板**：
```
## Session X - API003: File upload

### Completed
- [x] Multer middleware setup
- [x] S3 integration
- [x] File validation (type, size)
- [x] Progress tracking

### API Tests
POST /upload: ✓ 200
POST /upload (large file): ✓ 413
GET /files/:id: ✓ 200
GET /files/invalid: ✓ 404

### Coverage: 88%

Status: API003 PASSED
```

---

### 案例4：数据迁移工具

**场景**：开发数据库迁移工具

**挑战**：
- 迁移逻辑复杂
- 需要可恢复性
- 需要进度追踪

**解决方案**：

```json
{
  "features": [
    {
      "id": "M001",
      "category": "core",
      "description": "Source database connector",
      "passes": false
    },
    {
      "id": "M002",
      "category": "core",
      "description": "Target database connector",
      "passes": false
    },
    {
      "id": "M003",
      "category": "core",
      "description": "Data transformation engine",
      "passes": false
    },
    {
      "id": "M004",
      "category": "feature",
      "description": "Checkpoint/resume functionality",
      "passes": false
    },
    {
      "id": "M005",
      "category": "feature",
      "description": "Progress reporting",
      "passes": false
    }
  ]
}
```

**检查点设计**：
```python
# 检查点文件
{
  "migration_id": "mig_001",
  "started_at": "2025-01-15T10:00:00Z",
  "last_checkpoint": "2025-01-15T14:30:00Z",
  "progress": {
    "total_records": 1000000,
    "processed": 450000,
    "failed": 23,
    "last_id": "user_450000"
  },
  "status": "in_progress"
}

# Agent可以从中断点恢复
def resume_migration(checkpoint):
    last_id = checkpoint["progress"]["last_id"]
    return migrate_from(last_id)
```

**效果**：
- 迁移可恢复
- 进度可见
- 失败可追踪

---

### 案例5：AI聊天机器人

**场景**：开发一个多功能AI聊天机器人

**功能模块化**：
```json
{
  "features": [
    {
      "id": "BOT001",
      "category": "nlp",
      "description": "Intent recognition",
      "passes": false
    },
    {
      "id": "BOT002",
      "category": "nlp",
      "description": "Entity extraction",
      "passes": false
    },
    {
      "id": "BOT003",
      "category": "dialogue",
      "description": "Conversation state management",
      "passes": false
    },
    {
      "id": "BOT004",
      "category": "integration",
      "description": "Slack integration",
      "passes": false
    },
    {
      "id": "BOT005",
      "category": "integration",
      "description": "Discord integration",
      "passes": false
    }
  ]
}
```

**增量测试策略**：
```
# 每个功能完成后运行相关测试

BOT001完成后：
- 运行意图分类准确率测试
- 验证支持5种核心意图
- 准确率 > 85%

BOT003完成后：
- 运行对话流程测试
- 验证状态转换
- 测试上下文保持
```

**跨会话一致性**：
```
## Session 8 - BOT004: Slack integration

Context from previous sessions:
- BOT001-003: Core NLP complete
- Using GPT-4 for intent recognition
- State stored in Redis

This session:
- Implemented Slack Bolt framework
- Added message event handlers
- Connected to NLP pipeline

Testing:
- Sent test messages from Slack
- Verified intent recognition works
- State persists correctly

Status: BOT004 PASSED
```

---

## 六、失败模式与解决方案

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| **过早宣布胜利** | 功能标记完成但有bug | 设置严格的验收标准 |
| **环境遗留bug** | 新会话环境不一致 | init.sh自动清理和重置 |
| **进度未记录** | 不知道之前做了什么 | 强制每个会话更新进度文件 |
| **不知道如何运行** | 花时间配置环境 | init.sh脚本自动化 |
| **功能太复杂** | 单会话无法完成 | 拆分为更小的功能 |

---

## 七、最佳实践

### 7.1 功能列表设计

1. **功能粒度**：每个功能1-2个会话可完成
2. **可测试性**：有明确的验收标准
3. **独立性**：尽量减少依赖
4. **优先级**：高风险功能优先

### 7.2 进度记录

1. **结构化**：使用一致的格式
2. **关键信息**：记录决策和原因
3. **问题追踪**：记录遇到的问题和解决方案
4. **下一步**：明确下次要做什么

### 7.3 环境管理

1. **幂等性**：init.sh可以重复运行
2. **自包含**：所有依赖自动安装
3. **验证**：启动后自动运行冒烟测试

---

## 八、总结

长期运行Agent的核心：

1. **功能列表**：清晰的需求追踪
2. **增量进度**：每次只做一个功能
3. **结构化记录**：跨会话记忆
4. **自动化环境**：init.sh脚本
5. **严格验证**：不自验证不标记完成

> **关键原则**：让Agent一次只处理一个功能，通过结构化记录实现跨会话连续性。
