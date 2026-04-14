# 法贝实验室管理平台 — 项目状态

> 最后更新: 2026-04-15
> **GitHub**: `YuShuangyuanFABLAB/FabLabOnline`
> **当前阶段**: Phase 4 全部完成 + RBAC 验证通过，173 tests

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
| Session 06 Phase 4 | `后端/docs/sessions/2026-04-14-session-06-phase4-hardening.md` |
| Session 07 RBAC 验证 | `后端/docs/sessions/2026-04-15-session-07-rbac-testing.md` |
| Agent Teams 审查 | `后端/docs/superpowers/audits/2026-04-13-agent-teams-review.md` — 43 项发现 |

---

## 二、设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + 密码登录(限流) + JWT HttpOnly Cookie 7天过期
- **密码**: PBKDF2-SHA256 480000 次迭代 + 随机盐（`domains/identity/password.py`）
- **权限**: RBAC（3 角色: super_admin/admin/teacher）+ Redis 权限缓存 5min TTL + 真实角色查询
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

### Phase 4 — 安全加固 + 前后端对齐 + 基础设施 ✅（2026-04-14）
| ID | 修复 | 文件 |
|----|------|------|
| C1 | Cookie SameSite strict | auth.py |
| C3 | 删除密码明文输出 | init_db.py |
| C4 | tenant_id SQL 注入白名单校验 | events.py, analytics.py |
| H1 | 删除重复 router | users.py |
| H2 | apps 返回 app_secret | apps.py |
| H3 | analytics 权限校验 | analytics.py |
| H4 | POST/PUT /roles CRUD | roles.py |
| H5 | PUT /apps/{id}/status | apps.py |
| H6 | GET /roles 返回 permissions | roles.py |
| H7 | JWT 密钥生产环境校验 | settings.py |
| H8 | manage.py PBKDF2 | manage.py |
| H9 | 删除 callback token 泄露 | auth.py |
| H10 | Redis AOF 持久化 | docker-compose.yml |
| H11 | SDK 版本号 | client.py |
| M1 | 登录响应 json.dumps | auth.py |
| M2 | 心跳续签去重 | auth.py |
| M9 | Role 默认值对齐 | models/role.py |
| M14 | Redis 连接池 | redis.py |

### RBAC 验证 + 角色名对齐 ✅（2026-04-15）
| 修复 | 文件 |
|------|------|
| 创建 teacher1/admin 测试用户 | Docker 环境验证 |
| 前端角色名 org_admin→admin 对齐 | auth.ts, Layout.vue |

### 未修复（LOW / 生产部署时处理）
| ID | 问题 | 说明 |
|----|------|------|
| M3 | 缺少 HTTPS/TLS | 需 Let's Encrypt / certbot |
| M4 | Cookie Secure 生产环境 | 需 HTTPS 部署后生效 |
| M5 | 多环境配置分离 | pydantic-settings 多环境 |
| M6 | 前端 TypeScript 接口 | 缺响应类型定义 |
| M7 | 前端错误处理 | 不区分 403/404/网络错误 |
| M8 | 前端搜索用后端 | 当前仅过滤已加载页 |
| M10 | TenantModel.tenant_query 未使用 | 安全查询方法 |
| M11 | 缺 OpenAPI 文档自动化 | 前端可用 openapi-typescript |
| M12 | 分区创建改定时任务 | 当前依赖应用启动 |
| M13 | 缺 i18n | 字符串硬编码中文 |
| M15 | 通用速率限制中间件 | 仅登录有限速 |
| M16 | 审计日志 user_role 未填充 | 多数调用方传 None |

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
| 后端 | 173 passed |
| 前端 | 5 passed + 构建成功 |
| **总计** | **178 tests** |

### 后端测试文件清单

| 文件 | 覆盖 |
|------|------|
| tests/api/test_spec_alignment.py | API 规范对齐 |
| tests/test_cookie_auth.py | HttpOnly Cookie 认证 |
| tests/test_password_hash.py | PBKDF2 密码哈希 |
| tests/test_login_rate_limit.py | 登录限流 |
| tests/test_cors.py | CORS 配置 |
| tests/test_real_roles.py | 真实角色查询 |
| tests/test_audit_integration.py | 审计日志集成 |
| tests/test_init_db_refactor.py | init_db 重构 |
| tests/test_roles_delete.py | 系统角色删除保护 |
| tests/test_graceful_shutdown.py | 优雅关闭 |
| tests/test_pydantic_validation.py | Pydantic 请求校验 |
| tests/test_phase4a_fixes.py | Phase 4A 快速修复 |
| tests/test_phase4b_fixes.py | Phase 4B 安全加固 |
| tests/test_phase4c_fixes.py | Phase 4C 前后端对齐 |
| tests/test_phase4d_fixes.py | Phase 4D 安全+基础设施 |

---

## 六、测试用户

| 用户 | 密码 | 角色 | 用途 |
|------|------|------|------|
| `admin` | `admin123` | super_admin | 全权限管理 |
| `orgadmin1` | `orgadmin123` | admin | 中间权限层（当前 0 权限） |
| `teacher1` | `teacher123` | teacher | 最低权限 |

---

## 七、关键代码路径

### 认证流程
```
LoginView.vue → POST /auth/login → auth.py
  → password.py (verify_password PBKDF2)
  → Redis 限流检查
  → response.set_cookie(token, httponly=True)
  → get_user_roles() → 返回真实角色

router/index.ts → heartbeat 守卫 → POST /auth/heartbeat
  → 验证 Cookie JWT → 恢复 authStore.user + roles
```

### 前端菜单过滤
```
Layout.vue → showMenu(resource)
  → authStore.highestRole（优先级: super_admin > admin > teacher）
  → menuVisibility[resource].includes(role)
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

## 八、下一步

1. **给 admin 角色分配权限** — user:read, campus:read, analytics:read, audit:read
2. **生产环境部署** — HTTPS/TLS (Let's Encrypt)、微信 OAuth 配置、JWT_SECRET_KEY 强密钥
3. **M3: HTTPS/TLS 配置** — nginx HTTPS 模板 + certbot
4. **前端 TypeScript 接口定义** — API 响应类型安全
