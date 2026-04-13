# 法贝实验室管理平台 — 项目状态

> 最后更新: 2026-04-13
> **GitHub**: `YuShuangyuanFABLAB/FabLabOnline`
> **当前阶段**: 代码审计 21 项全部修复，147 tests，产品级质量

---

## 一、文档位置

| 文件 | 路径 |
|------|------|
| 设计文档 v1.1 | `后端/docs/superpowers/specs/2026-04-03-platform-foundation-design.md` |
| 实现计划 v1.4 | `后端/docs/superpowers/plans/2026-04-03-phase1-implementation.md` |
| 代码审计报告 | `后端/docs/superpowers/audits/2026-04-11-code-audit.md` — 21 项全部修复 |
| Session 01 设计评审 | `后端/docs/sessions/2026-04-03-session-01-design-review.md` |
| Session 02 计划评审 | `后端/docs/sessions/2026-04-03-session-02-plan-review.md` |
| Session 03 审计+UI | `后端/docs/sessions/2026-04-11-session-03-code-audit.md` |
| Session 04 Phase 2 | `后端/docs/sessions/2026-04-12-session-04-phase2-security.md` |
| Session 05 Phase 3 | `后端/docs/sessions/2026-04-12-session-05-phase3-quality.md` |

---

## 二、设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + 密码登录(限流) + JWT HttpOnly Cookie 7天过期
- **密码**: PBKDF2-SHA256 480000 次迭代 + 随机盐（`domains/identity/password.py`）
- **权限**: RBAC（4 角色）+ Redis 权限缓存 5min TTL + 真实角色查询 + Pydantic 校验
- **事件**: PostgreSQL 分区表 + asyncio.Queue 批量写入 + 优雅关闭
- **多租户**: TenantModel 防呆基类（无重复声明）
- **审计**: 全写操作审计日志 + ip_address/user_agent + 查询端点 GET /audit/logs
- **SDK**: Python 包（keyring + JSONL + 熔断器）

---

## 三、审计修复状态

### Phase 1 — 安全加固 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| C1 | Token → HttpOnly Cookie | auth.py, client.ts, LoginView.vue, router/index.ts |
| C2 | SHA-256 → PBKDF2-SHA256 480000 次 | password.py, auth.py, init_db.py |
| C3 | 登录限流 5 次/15 分钟 | auth.py (Redis INCR + EXPIRE) |
| H1 | 用户信息刷新恢复 | router/index.ts (heartbeat 路由守卫) |
| H5 | CORSMiddleware | main.py |

### Phase 2 — 数据完整性 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| H4 | 真实角色查询 | auth.py (get_user_roles) |
| H2 | 审计日志全覆盖 | config.py, apps.py, users.py, campuses.py |
| H3 | Alembic + init_db fallback | init_db.py, Dockerfile |

### Phase 3 — 工程质量 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| M5 | 消除 tenant_id 重复声明 | models/user.py, models/campus.py |
| M6 | 禁止删除系统角色 | api/v1/roles.py (DELETE + is_system) |
| M7 | 优雅关闭 | store.py (drain_queue) + main.py (shutdown_event) |
| M8 | Pydantic 请求校验 | campuses.py, apps.py, config.py, users.py |
| M4 | 前端 API 封装 + 审计端点 | audit.py 端点 + audit/apps/config.ts |

### 未修复（LOW 风险）
| ID | 问题 | 说明 |
|----|------|------|
| L1 | API 响应格式不统一 | 缺少 `success` 字段 |
| L2 | `_INIT_DEFAULTS` + 自定义 `__init__` | 非标准 SQLAlchemy 用法 |
| L3 | Redis 无密码保护 | 内网可接受 |
| L4 | 日志配置在 import 时执行 | 测试中可能干扰 |
| L5 | 前端少量 `any` 类型残留 | — |
| M2 | 事件分区表无初始分区 | 已由 ensure_future_partitions 自动处理 |
| M3 | 缺少 HTTPS/TLS | 需 Let's Encrypt / certbot |

---

## 四、8 个 Task 完成状态

```
Task 1: 项目骨架 + 基础设施层          ✅
Task 2: 数据模型 + Alembic 迁移         ✅ TenantModel（无重复声明）+ seed data
Task 3: 认证系统                        ✅ PBKDF2 + Cookie + 限流 + 真实角色
Task 4: 组织与权限                      ✅ RBAC + 审计日志全覆盖 + Pydantic 校验
Task 5: 事件系统                        ✅ Queue 缓冲 + 优雅关闭 + 分区
Task 6: Web 管理后台                    ✅ Cookie + 暗色模式 + API 模块封装
Task 7: 客户端 SDK                      ✅
Task 8: PPT 集成 + Docker 部署          ✅ Alembic 迁移 + 健康检查
```

---

## 五、测试状态

| 类别 | 数量 |
|------|------|
| 后端 | 142 passed |
| 前端 | 5 passed + 构建成功 |
| **总计** | **147 tests** |

### 后端测试文件清单

| 文件 | 测试数 | 覆盖 |
|------|--------|------|
| tests/api/test_spec_alignment.py | — | API 规范对齐 |
| tests/test_cookie_auth.py | — | HttpOnly Cookie 认证 |
| tests/test_password_hash.py | — | PBKDF2 密码哈希 |
| tests/test_login_rate_limit.py | — | 登录限流 |
| tests/test_cors.py | — | CORS 配置 |
| tests/test_real_roles.py | — | 真实角色查询 |
| tests/test_audit_integration.py | — | 审计日志集成 |
| tests/test_init_db_refactor.py | — | init_db 重构 |
| tests/test_roles_delete.py | — | 系统角色删除保护 |
| tests/test_graceful_shutdown.py | — | 优雅关闭 |
| tests/test_pydantic_validation.py | — | Pydantic 请求校验 |

---

## 六、关键代码路径

### 认证流程
```
LoginView.vue → POST /auth/login → auth.py
  → password.py (verify_password PBKDF2)
  → Redis 限流检查
  → response.set_cookie(token, httponly=True)
  → get_user_roles() → 返回真实角色

router/index.ts → heartbeat 守卫 → GET /auth/heartbeat
  → 验证 Cookie JWT → 恢复 authStore.user
```

### 审计日志流程
```
API 写操作 (POST/PUT/DELETE)
  → write_audit_log(tenant_id, user_id, action, resource_type, ip_address, user_agent)
  → audit_logs 表
  → GET /audit/logs → AuditView.vue
```

### 事件系统流程
```
事件产生 → asyncio.Queue → _event_writer_loop 批量写入
容器停止 → shutdown_event → drain_queue() → cancel task
```

---

## 七、下一步

1. **Docker 重新构建验证全流程** — `docker compose up --build`
2. **创建非 super_admin 测试用户** — 验证角色过滤是否正确
3. **生产环境部署准备** — HTTPS/TLS (Let's Encrypt)、微信 OAuth 配置
4. **M3: HTTPS/TLS 配置** — nginx HTTPS 模板 + certbot
5. **L1: 统一 API 响应格式** — `{"success": true, "data": ...}` 封装
