# 法贝实验室管理平台 — 项目状态

**项目路径**: `D:\FABLAB 法贝实验室\13-工具\法贝实验室管理系统`
**GitHub**: `YuShuangyuanFABLAB/FabLabOnline`
**当前阶段**: Phase 1 开发完成 + 安全加固完成（Phase 1+2），139 tests，Phase 3 待执行

## 文档位置

| 文件 | 路径 |
|------|------|
| 设计文档 v1.1 | `后端/docs/superpowers/specs/2026-04-03-platform-foundation-design.md` |
| 实现计划 v1.4 | `后端/docs/superpowers/plans/2026-04-03-phase1-implementation.md` |
| 代码审计报告 | `后端/docs/superpowers/audits/2026-04-11-code-audit.md` |
| Session 01 设计评审 | `后端/docs/sessions/2026-04-03-session-01-design-review.md` |
| Session 02 计划评审 | `后端/docs/sessions/2026-04-03-session-02-plan-review.md` |
| Session 03 审计+UI | `后端/docs/sessions/2026-04-11-session-03-code-audit.md` |
| Session 04 Phase 2 | `后端/docs/sessions/2026-04-12-session-04-phase2-security.md` |

## 设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + JWT HttpOnly Cookie + 超管紧急通道（限流保护）
- **权限**: RBAC（4 角色: super_admin/org_admin/campus_admin/teacher）+ Redis 权限缓存
- **事件**: PostgreSQL 分区表 + asyncio.Queue 批量写入 + consumer 模式 + 预聚合
- **多租户**: TenantModel 防呆基类（强制 tenant_id 注入 + assert_tenant_owned）
- **SDK**: Python 包（keyring 存储 Token + 本地 JSONL 持久化 + 熔断器）
- **年成本**: ~1620 元

## 安全加固状态

### Phase 1 — 安全加固 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| C1 | Token → HttpOnly Cookie | auth.py, client.ts, LoginView.vue, router/index.ts |
| C2 | SHA-256 → PBKDF2-SHA256 480000 次 | password.py, auth.py, init_db.py |
| C3 | 登录限流 5 次/15 分钟 | auth.py (Redis INCR + EXPIRE) |
| H5 | CORSMiddleware | main.py |

### Phase 2 — 数据完整性 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| H4 | 真实角色查询 | auth.py (get_user_roles) |
| H2 | 审计日志全覆盖 | config.py, apps.py, users.py, campuses.py |
| H3 | Alembic + init_db fallback | init_db.py, Dockerfile |

### Phase 3 — 工程质量（待执行）
- M5: tenant_id 重复声明
- M6: 禁止删除系统角色
- M7: shutdown 事件处理
- M8: Pydantic 请求校验
- M4: 前端 API 模块封装

## 8 个 Task 完成状态

```
Task 1: 项目骨架 + 基础设施层          ✅
Task 2: 数据模型 + Alembic 迁移         ✅ 含 TenantModel + seed data + manage.py
Task 3: 认证系统                        ✅ 含完整回调流程 + PBKDF2 + 限流
Task 4: 组织与权限                      ✅ 含 Redis 权限缓存 + 审计日志全覆盖
Task 5: 事件系统                        ✅ 含 Queue 缓冲批量写 + 预聚合
Task 6: Web 管理后台                    ✅ 含 HttpOnly Cookie + 真实角色 + 暗色模式
Task 7: 客户端 SDK                      ✅ 含正确 build_meta
Task 8: PPT 集成 + Docker 部署          ✅ 含 Alembic 迁移
```

## 测试状态

- 后端：134 passed（含 29 个安全测试）
- 前端：5 passed
- 总计：139 tests

## 下一步

1. Phase 3 工程质量提升（M5-M8）
2. Docker 重新构建验证
3. 创建非 super_admin 测试用户验证角色过滤
