# Session 04 — Phase 2 安全修复

> 日期：2026-04-12
> 类型：安全加固
> 关联审计：`docs/superpowers/audits/2026-04-11-code-audit.md`

---

## 目标

修复代码审计中 Phase 2 的 HIGH 级别问题：

| # | 问题 | 状态 |
|---|------|------|
| H1 | 用户信息刷新恢复 | **已在 Phase 1 完成**（Cookie + heartbeat 路由守卫） |
| H4 | 登录返回真实角色（非硬编码） | **已完成** — auth.py login+heartbeat 调用 get_user_roles() |
| H2 | 审计日志补全（config/apps 写操作） | **已完成** — config.py+apps.py 补全，所有写操作传递 ip/user_agent |
| H3 | init_db 仅做种子数据 + Alembic 迁移 | **已完成** — init() 检查 alembic_version fallback，Dockerfile 加 alembic |

## Phase 1 已完成回顾

- C1: Token → HttpOnly Cookie
- C2: SHA-256 → PBKDF2-SHA256 480000 次
- C3: 登录限流 5 次/15分钟
- H5: CORS 配置
- 后端 124 tests passed，前端 5 tests passed
- Docker 5 容器健康

## 执行计划

### Step 1: H4 — 真实角色
- `auth.py` login + heartbeat 调用 `get_user_roles()`
- TDD: 4 个测试

### Step 2: H2 — 审计日志补全
- `config.py` update_config + `apps.py` register_app 添加审计日志
- 所有写操作传递 ip_address/user_agent
- TDD: 3 个测试

### Step 3: H3 — Alembic + init_db 重构
- 创建 migrations/env.py + 初始迁移
- init_db.py 删除 create_tables()
- Dockerfile CMD 加入 alembic upgrade head
- TDD: 3 个测试

## 变更记录

### H4 — 真实角色
- `api/v1/auth.py` — 新增 `from domains.access.roles import get_user_roles`，login 和 heartbeat 调用后提取 role_id 列表
- 新增 `tests/test_real_roles.py` — 4 个测试

### H2 — 审计日志补全
- `api/v1/config.py` — update_config 添加 `write_audit_log` + ip_address/user_agent
- `api/v1/apps.py` — register_app 添加 `write_audit_log` + ip_address/user_agent
- `api/v1/users.py` — 2 处现有调用增加 ip_address/user_agent
- `api/v1/campuses.py` — 3 处现有调用增加 ip_address/user_agent
- 新增 `tests/test_audit_integration.py` — 3 个测试

### H3 — Alembic + init_db
- `init_db.py` — 新增 `_has_alembic_version()` 检查，init() 条件调用 create_tables()
- `Dockerfile` — CMD 加入 `alembic upgrade head`
- 新增 `tests/test_init_db_refactor.py` — 3 个测试

## 测试结果

- 后端：134 passed（+10 新增）
- 前端：5 passed
- 总计：139 tests passed
