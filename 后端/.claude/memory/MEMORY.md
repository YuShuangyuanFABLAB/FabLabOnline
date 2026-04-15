# 法贝实验室管理系统 — 项目记忆

> 最后更新: 2026-04-16

## 项目概述

法贝实验室统一管理平台 — 教育 SaaS 平台底座，管理 PPT 软件授权、用户、校区、使用追踪。

**当前状态**: 生产部署进行中，178 tests，阿里云 ECS 已搭建，ICP 备案审核中。

## 关键文档

- [项目状态与上下文](platform-project-context.md) — 部署进度、审计状态、下一步行动
- [部署指南](../docs/deployment-guide.md) — 手把手部署文档（方案A: 云服务器 / 方案B: Cloudflare Tunnel）
- [设计文档 v1.1](../docs/superpowers/specs/2026-04-03-platform-foundation-design.md) — 5轮AI评审后冻结
- [实现计划 v1.4](../docs/superpowers/plans/2026-04-03-phase1-implementation.md) — 8 Task, 7轮评审38项修正
- [代码审计报告](../docs/superpowers/audits/2026-04-11-code-audit.md) — 21 项发现，Phase 1+2+3+4 全部修复

## Session 记录

| Session | 日期 | 内容 |
|---------|------|------|
| [01](../docs/sessions/2026-04-03-session-01-design-review.md) | 04-03 | 设计评审全记录 |
| [02](../docs/sessions/2026-04-03-session-02-plan-review.md) | 04-03 | 计划评审修正 |
| [03](../docs/sessions/2026-04-11-session-03-code-audit.md) | 04-11 | UI 重设计 + Docker 修复 + 代码审计 |
| [04](../docs/sessions/2026-04-12-session-04-phase2-security.md) | 04-12 | Phase 2 安全修复（H4+H2+H3） |
| [05](../docs/sessions/2026-04-12-session-05-phase3-quality.md) | 04-12 | Phase 3 工程质量（M5+M6+M7+M8+M4） |
| 06 | 04-14 | Phase 4 安全加固 + 前后端对齐 + 基础设施 |
| 07 | 04-15 | RBAC 验证 + 角色名对齐修复 |
| [08](../docs/sessions/2026-04-16-session-08-deployment.md) | 04-16 | **生产环境部署**（阿里云 ECS） |

## 生产部署信息

| 项目 | 值 |
|------|-----|
| 服务器 | 阿里云 ECS 华东 1（杭州）2C4G (ecs.u1-c1m2.large) |
| 公网 IP | 8.136.122.38 |
| 域名 | fablab.net.cn（ICP 备案中） |
| 代码路径 | /opt/fablab |

## 技术栈

FastAPI + PostgreSQL 15 + Redis 7 + Vue 3 + Element Plus + PyQt5 + Docker Compose

## 开发历程

### Phase 1 开发（2026-04-03 ~ 04-09）
8 个 Task 全部完成（105+4+16+13=138 tests），v1.0.0 发布

### Phase 1 安全加固（2026-04-12）
- C1: Token → HttpOnly Cookie
- C2: SHA-256 → PBKDF2-SHA256 480000 次
- C3: 登录限流 5 次/15分钟
- H5: CORS 配置
- H1: Cookie + heartbeat 路由守卫
- 后端 124 + 前端 5 = 129 tests

### Phase 2 安全修复（2026-04-12）
- H4: 登录和心跳返回真实角色（get_user_roles）
- H2: 审计日志全覆盖（ip_address/user_agent）
- H3: Alembic 迁移 + init_db fallback
- 后端 134 + 前端 5 = 139 tests

### Phase 3 工程质量（2026-04-12）
- M5: 消除 tenant_id 重复声明
- M6: 禁止删除系统角色
- M7: 优雅关闭（drain_queue + shutdown_event）
- M8: Pydantic 请求校验（4 个文件）
- M4: 前端 API 模块封装 + 后端审计端点
- 后端 142 + 前端 5 = 147 tests

### Phase 4 安全加固+前后端对齐+基础设施（2026-04-14）
- 19 项修复（C1/H1/M14 等），173 tests
- Docker 5 容器全流程验证通过

### RBAC 验证（2026-04-15）
- 创建 teacher1/orgadmin1 测试用户
- 修复前端角色名不一致（org_admin→admin）
- 浏览器验证通过

### 生产部署准备（2026-04-16）
- CORS/文档保护/HTTPS 模板/安全加固代码修改
- 阿里云 ECS 购买 + Docker 安装 + 代码部署
- 后端容器启动 Bug 待修复（服务器代码同步问题）
- ICP 备案提交中

## 评审历史

7 轮 AI 评审，38 项修正，全部已合并到实现计划 v1.4：
- 第1-5轮（Session 01）: DeepSeek/豆包/千问/ChatGPT/Claude — 设计文档评审
- 第6轮（Session 02）: Claude Code — 运行崩溃bug + 隐患 + Task 4-5 详细化
- 第7轮（Session 02）: ChatGPT — 性能瓶颈（Queue缓冲/权限缓存/租户防呆）+ 战略定位

## 关联项目

- PPTGenerator (`D:\FABLAB 法贝实验室\13-工具\PPTGenerator`) — 被管理的桌面软件
