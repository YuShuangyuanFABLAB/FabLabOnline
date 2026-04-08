# 法贝实验室管理平台 — 项目状态

**项目路径**: `D:\FABLAB 法贝实验室\13-工具\法贝实验室管理系统`
**当前阶段**: Phase 1 设计完成，等待前置准备 → 进入开发

## 文档位置

| 文件 | 路径 |
|------|------|
| 设计文档 v1.1 | `docs/superpowers/specs/2026-04-03-platform-foundation-design.md` |
| 实现计划 v1.2 | `docs/superpowers/plans/2026-04-03-phase1-implementation.md` |
| 会话记录 | `docs/sessions/2026-04-03-session-01-design-review.md` |

## 设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + JWT + 超管紧急通道
- **权限**: RBAC（4 角色: super_admin/org_admin/campus_admin/teacher）
- **事件**: PostgreSQL 分区表 + 消费者模式 + 预聚合
- **SDK**: Python 包（keyring 存储 Token + 本地 JSONL 持久化 + 熔断器）
- **年成本**: ~1620 元

## 评审记录

经 5 轮 AI 评审（DeepSeek/豆包/千问/ChatGPT/Claude），共修正 18 项问题：
- 🔴 必须修正 6 项（已全部修正并更新到计划文档）
- 🟡 强烈建议 7 项（已全部采纳）
- 🟢 可选优化 5 项（已采纳关键项）

## 下一步

1. 用户完成前置准备（微信开放平台注册、域名备案、云服务器购买）
2. 选择执行方式（子代理驱动 / 内联执行）
3. 从 Task 1（项目骨架）开始实现

## Why: PPT 软件需要授权管控才能分发到多校区
## How to apply: 下次对话先检查前置准备完成情况，再开始实施
