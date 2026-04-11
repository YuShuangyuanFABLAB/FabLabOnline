# 法贝实验室管理系统 — 项目记忆

## 项目概述

法贝实验室统一管理平台 — 教育 SaaS 平台底座，管理 PPT 软件授权、用户、校区、使用追踪

## 关键文档

- [项目状态与上下文](platform-project-context.md) — 当前阶段、v1.4 改进、下一步行动
- [设计文档 v1.1](../docs/superpowers/specs/2026-04-03-platform-foundation-design.md) — 5轮AI评审后冻结
- [实现计划 v1.4](../docs/superpowers/plans/2026-04-03-phase1-implementation.md) — 8 Task, 7轮评审38项修正
- [会话记录 01](../docs/sessions/2026-04-03-session-01-design-review.md) — 设计评审全记录
- [会话记录 02](../docs/sessions/2026-04-03-session-02-plan-review.md) — 计划评审修正（Claude Code + ChatGPT）

## 技术栈

FastAPI + PostgreSQL 15 + Redis 7 + Vue 3 + Element Plus + PyQt5 + Docker Compose

## 评审历史

7 轮 AI 评审，38 项修正，全部已合并到实现计划 v1.4：
- 第1-5轮（Session 01）: DeepSeek/豆包/千问/ChatGPT/Claude — 设计文档评审
- 第6轮（Session 02）: Claude Code — 运行崩溃bug + 隐患 + Task 4-5 详细化
- 第7轮（Session 02）: ChatGPT — 性能瓶颈（Queue缓冲/权限缓存/租户防呆）+ 战略定位

## 关联项目

- PPTGenerator (`D:\FABLAB 法贝实验室\13-工具\PPTGenerator`) — 被管理的桌面软件
