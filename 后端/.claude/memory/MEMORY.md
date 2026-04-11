# 法贝实验室管理系统 — 项目记忆

## 项目概述

法贝实验室统一管理平台 — 教育 SaaS 平台底座，管理 PPT 软件授权、用户、校区、使用追踪

## 关键文档

- [项目状态与上下文](platform-project-context.md) — 当前阶段、v1.4 改进、下一步行动
- [设计文档 v1.1](../docs/superpowers/specs/2026-04-03-platform-foundation-design.md) — 5轮AI评审后冻结
- [实现计划 v1.4](../docs/superpowers/plans/2026-04-03-phase1-implementation.md) — 8 Task, 7轮评审38项修正
- [代码审计报告](../docs/superpowers/audits/2026-04-11-code-audit.md) — 21 项发现，Phase 1+2 已修复
- [Session 01](../docs/sessions/2026-04-03-session-01-design-review.md) — 设计评审全记录
- [Session 02](../docs/sessions/2026-04-03-session-02-plan-review.md) — 计划评审修正
- [Session 03](../docs/sessions/2026-04-11-session-03-code-audit.md) — UI 重设计 + Docker 修复 + 代码审计
- [Session 04](../docs/sessions/2026-04-12-session-04-phase2-security.md) — Phase 2 安全修复

## 技术栈

FastAPI + PostgreSQL 15 + Redis 7 + Vue 3 + Element Plus + PyQt5 + Docker Compose

## 开发历程

### Phase 1 开发（2026-04-03 ~ 04-09）
8 个 Task 全部完成（105+4+16+13=138 tests），v1.0.0 发布

### Phase 1 安全加固（2026-04-12 Session 03→04 前半）
- C1: Token → HttpOnly Cookie
- C2: SHA-256 → PBKDF2-SHA256 480000 次
- C3: 登录限流 5 次/15分钟
- H5: CORS 配置
- 后端 124 + 前端 5 = 129 tests

### Phase 2 安全修复（2026-04-12 Session 04）
- H4: 登录和心跳返回真实角色（调用 get_user_roles）
- H2: 审计日志全覆盖（config/apps 补全 + ip_address/user_agent）
- H3: init_db 检查 alembic_version fallback + Dockerfile 加入 alembic
- 后端 134 + 前端 5 = 139 tests

### Phase 3 待执行（MEDIUM）
- M5: tenant_id 重复声明
- M6: 禁止删除系统角色
- M7: shutdown 事件处理
- M8: Pydantic 请求校验
- M4: 前端 API 模块封装

## 评审历史

7 轮 AI 评审，38 项修正，全部已合并到实现计划 v1.4：
- 第1-5轮（Session 01）: DeepSeek/豆包/千问/ChatGPT/Claude — 设计文档评审
- 第6轮（Session 02）: Claude Code — 运行崩溃bug + 隐患 + Task 4-5 详细化
- 第7轮（Session 02）: ChatGPT — 性能瓶颈（Queue缓冲/权限缓存/租户防呆）+ 战略定位

## 关联项目

- PPTGenerator (`D:\FABLAB 法贝实验室\13-工具\PPTGenerator`) — 被管理的桌面软件
