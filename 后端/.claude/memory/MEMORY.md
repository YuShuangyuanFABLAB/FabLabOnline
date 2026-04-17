# 法贝实验室管理系统 — 项目记忆

> 最后更新: 2026-04-17

## 项目概述

法贝实验室统一管理平台 — 教育 SaaS 平台底座，管理 PPT 软件授权、用户、校区、使用追踪。

**当前状态**: 生产部署已上线（IP 直连 http://8.136.122.38），ICP 备案审核中。

## 关键文档

- [项目状态与上下文](platform-project-context.md) — 部署进度、审计状态、下一步行动
- [部署指南](../docs/deployment-guide.md) — 手把手部署文档（方案A: 云服务器 / 方案B: Cloudflare Tunnel）
- [Session 08 部署记录](../docs/sessions/2026-04-16-session-08-deployment.md) — 完整部署过程与踩坑记录
- [设计文档 v1.1](../docs/superpowers/specs/2026-04-03-platform-foundation-design.md) — 5轮AI评审后冻结
- [实现计划 v1.4](../docs/superpowers/plans/2026-04-03-phase1-implementation.md) — 8 Task, 7轮评审38项修正
- [代码审计报告](../docs/superpowers/audits/2026-04-11-code-audit.md) — 21 项发现，Phase 1-4 全部修复

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
| [08](../docs/sessions/2026-04-16-session-08-deployment.md) | 04-16~17 | **生产环境部署**（阿里云 ECS）✅ |

## 生产部署信息

| 项目 | 值 |
|------|-----|
| 服务器 | 阿里云 ECS 华东 1（杭州）2C4G |
| 公网 IP | 8.136.122.38 |
| 域名 | fablab.net.cn（ICP 备案中） |
| 访问地址 | http://8.136.122.38 |
| 代码路径 | /opt/fablab |
| 当前分支 | master |

## 部署关键经验

1. **docker compose restart ≠ up -d** — 修改 .env 后必须 `up -d`
2. **Secure Cookie + HTTP = 静默失败** — 浏览器不存储 Secure Cookie 但不报错
3. **安全组默认不开放 80/443** — 阿里云需手动添加
4. **国内三件套镜像** — Docker CE 清华源、pip 清华源、npm 淘宝源

## 技术栈

FastAPI + PostgreSQL 15 + Redis 7 + Vue 3 + Element Plus + PyQt5 + Docker Compose

## 开发历程

### Phase 1 开发（2026-04-03 ~ 04-09）— 138 tests
8 个 Task 全部完成，v1.0.0 发布

### Phase 1~4 + 审计修复（2026-04-12 ~ 04-14）— 173 tests
21 项审计全部修复，Docker 5 容器验证通过

### RBAC 验证（2026-04-15）— 178 tests
角色名对齐修复

### 生产部署（2026-04-16 ~ 04-17）
阿里云 ECS 部署成功，IP 直连上线

## 评审历史

7 轮 AI 评审，38 项修正，全部已合并到实现计划 v1.4

## 关联项目

- PPTGenerator (`D:\FABLAB 法贝实验室\13-工具\PPTGenerator`) — 被管理的桌面软件
