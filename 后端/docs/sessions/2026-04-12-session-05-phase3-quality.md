# Session 05 — Phase 3 工程质量提升

> 日期：2026-04-12
> 类型：工程质量
> 关联审计：`docs/superpowers/audits/2026-04-11-code-audit.md`

---

## 目标

修复代码审计中 Phase 3 的 MEDIUM 级别问题：

| # | 问题 | 状态 |
|---|------|------|
| M5 | tenant_id 列重复声明 | **已完成** — 删除 User/Campus 重复声明 |
| M6 | 禁止删除系统角色 | **已完成** — roles.py DELETE 端点 + is_system 检查 |
| M7 | 后端无优雅关闭 | **已完成** — drain_queue + shutdown_event |
| M8 | API 缺少 Pydantic 请求校验 | **已完成** — 4 个文件添加 Pydantic BaseModel |
| M4 | 前端缺 API 模块 + 审计端点 | **已完成** — 后端 audit.py + 前端 3 个 API 模块 |

## Phase 2 已完成回顾

- H4: 真实角色查询（get_user_roles）
- H2: 审计日志全覆盖（config/apps 补全 + ip_address/user_agent）
- H3: Alembic + init_db fallback
- 后端 134 + 前端 5 = 139 tests

## 执行计划

### Step 1: M5 — 消除 tenant_id 重复
- 删除 User/Campus 中重复的 tenant_id 列声明
- 无新测试（模型行为不变）

### Step 2: M6 — 系统角色删除保护
- roles.py 添加 DELETE 端点，is_system=True 返回 403
- TDD: 2 个测试

### Step 3: M7 — 优雅关闭
- store.py 添加 drain 逻辑，main.py 添加 shutdown 处理器
- TDD: 2 个测试

### Step 4: M8 — Pydantic 请求校验
- campuses/apps/config/users 添加 Pydantic BaseModel
- 前端 API 调用同步更新（query params → request body）
- TDD: 4 个测试

### Step 5: M4 — 前端 API 封装 + 审计端点
- 后端新增 audit.py 查询端点
- 前端新增 audit.ts/apps.ts/config.ts API 模块
- 3 个 View 改用 API 模块

## 变更记录

### M5 — 消除 tenant_id 重复
- `models/user.py` — 删除重复 tenant_id 列
- `models/campus.py` — 删除重复 tenant_id 列

### M6 — 系统角色删除保护
- `api/v1/roles.py` — 新增 DELETE /{role_id} 端点，is_system=True 返回 403
- 新增 `tests/test_roles_delete.py` — 2 个测试

### M7 — 优雅关闭
- `domains/events/store.py` — 新增 start_writer_loop() + drain_queue()
- `main.py` — 新增 shutdown_event 处理器，drain + cancel
- 新增 `tests/test_graceful_shutdown.py` — 2 个测试

### M8 — Pydantic 请求校验
- `api/v1/campuses.py` — CreateCampusRequest + UpdateCampusRequest
- `api/v1/apps.py` — RegisterAppRequest
- `api/v1/config.py` — UpdateConfigRequest
- `api/v1/users.py` — UpdateUserStatusRequest + AssignRoleRequest
- 前端 campuses.ts/users.ts 同步更新（query params → request body）
- 新增 `tests/test_pydantic_validation.py` — 4 个测试

### M4 — 前端 API 封装 + 审计端点
- `api/v1/audit.py` — 新增 GET /audit/logs 分页查询
- `api/v1/router.py` — 注册 audit_router
- 前端新增 `api/audit.ts`、`api/apps.ts`、`api/config.ts`
- `views/AuditView.vue`、`AppsView.vue`、`ConfigView.vue` 改用 API 模块

## 测试结果

- 后端：142 passed（+8 新增）
- 前端：5 passed
- 前端构建：成功
- 总计：147 tests
