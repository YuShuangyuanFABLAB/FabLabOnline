# 法贝实验室管理平台 — 项目状态

**项目路径**: `D:\FABLAB 法贝实验室\13-工具\法贝实验室管理系统`
**当前阶段**: Phase 1 实现计划 v1.4 已就绪，等待前置准备 → 开始实施

## 文档位置

| 文件 | 路径 |
|------|------|
| 设计文档 v1.1 | `后端/docs/superpowers/specs/2026-04-03-platform-foundation-design.md` |
| 实现计划 v1.4 | `后端/docs/superpowers/plans/2026-04-03-phase1-implementation.md` |
| 会话记录 01 | `后端/docs/sessions/2026-04-03-session-01-design-review.md` |
| 会话记录 02 | `后端/docs/sessions/2026-04-03-session-02-plan-review.md` |

## 设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + JWT + 超管紧急通道
- **权限**: RBAC（4 角色: super_admin/org_admin/campus_admin/teacher）+ Redis 权限缓存
- **事件**: PostgreSQL 分区表 + asyncio.Queue 批量写入 + consumer 模式 + 预聚合
- **多租户**: TenantModel 防呆基类（强制 tenant_id 注入 + assert_tenant_owned）
- **SDK**: Python 包（keyring 存储 Token + 本地 JSONL 持久化 + 熔断器）
- **年成本**: ~1620 元

## v1.4 关键改进（vs v1.2）

| 改进 | 说明 |
|------|------|
| 事件写入缓冲 | asyncio.Queue + 100条/批 INSERT（毫秒级返回） |
| Redis 权限缓存 | user_permissions:{user_id} TTL 5min，角色变更主动失效 |
| 多租户防呆 | TenantModel.tenant_query() 强制带 tenant_id，空值报错 |
| 种子数据 | seed migration（角色+权限+默认租户）+ manage.py CLI |
| httpOnly Cookie | 管理后台 token 不再存 localStorage |
| 完整回调流程 | 微信回调 → find_or_create → JWT → session |

## 评审记录

7 轮 AI 评审（DeepSeek/豆包/千问/ChatGPT×2/Claude×2），共修正 38 项，全部已合并到 v1.4。

## 8 个 Task

```
Task 1: 项目骨架 + 基础设施层          ✅ 含 pyproject.toml + asyncio_mode
Task 2: 数据模型 + Alembic 迁移         ✅ 含 TenantModel + seed data + manage.py
Task 3: 认证系统                        ✅ 含完整回调流程
Task 4: 组织与权限                      ✅ 含 Redis 权限缓存 + 完整代码
Task 5: 事件系统                        ✅ 含 Queue 缓冲批量写 + 预聚合
Task 6: Web 管理后台                    ✅ 含 httpOnly Cookie
Task 7: 客户端 SDK                      ✅ 含正确 build_meta
Task 8: PPT 集成 + Docker 部署          ✅
```

## Phase 2 增强清单

1. Refresh Token 分离（P1）
2. Redis Stream 替代内存队列（P1）
3. 审计日志链式 hash 防篡改（P2）
4. 事件冷热分离 / ClickHouse（P2）
5. SDK 断网感知（P2）
6. PostgreSQL RLS 数据库层双保险（P1）
7. JWT RS256 密钥轮换（P1）

## 战略定位

教育 SaaS 平台底座 — 核心架构已具备多应用接入能力（apps 注册中心 + SDK + Event System）

## 下一步

1. 用户完成前置准备（微信注册、域名备案、买服务器）
2. 从 Task 1 开始实施
