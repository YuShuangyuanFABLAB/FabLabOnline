# 会话记录 — 2026-04-03 Session 01

> **会话主题**: 法贝实验室管理平台 Phase 1 设计 + 实现计划
> **日期**: 2026-04-03
> **项目路径**: `D:\FABLAB 法贝实验室\13-工具\法贝实验室管理系统`
> **状态**: 设计文档冻结，实现计划已更新，等待前置准备完成后进入开发

---

## 1. 项目背景

法贝实验室课程反馈助手（PPT 生成软件）已完成核心功能，需要分发给不同校区老师使用。面临问题：
- 软件被拷贝导致竞品获取能力
- 无法控制使用者
- 离职老师仍可使用
- 缺乏使用数据洞察

## 2. 本轮完成的工作

### 2.1 设计文档（已冻结 v1.1）

**文件**: `docs/superpowers/specs/2026-04-03-platform-foundation-design.md`

经过 5 轮 AI 架构评审（DeepSeek / 豆包 / 千问 / ChatGPT / Claude），设计文档包含：

- **系统架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **数据模型**: 12 张表（多租户+RBAC+事件+审计+配置中心）
- **认证**: 微信扫码登录 + JWT + 超管紧急通道（用户名+密码+TOTP）
- **权限**: RBAC 策略接口（deny-by-default，未来可升级 ABAC）
- **事件系统**: 统一格式 + payload 校验 + 消费者模式 + 按月分区
- **SDK**: 认证+可靠事件上报+熔断器+本地持久化
- **年成本**: ~1620 元（2核4G服务器+PG+Redis+域名+微信认证）

### 2.2 实现计划（v1.2，已更新 5 轮修正）

**文件**: `docs/superpowers/plans/2026-04-03-phase1-implementation.md`

8 个 Task，按依赖顺序执行：

```
Task 1: 项目骨架 + 基础设施层 → Task 2: 数据模型 + Alembic
  → Task 3: 认证系统 → Task 4: 组织与权限
  → Task 5: 事件系统 → Task 6: Web 管理后台
  → Task 7: 客户端 SDK → Task 8: PPT集成 + Docker部署
```

## 3. 关键设计决策

| 决策 | 选型 | 理由 |
|------|------|------|
| 登录方式 | 微信扫码 | 用户体验最好，老师都有微信 |
| 管理后台 | Web (Vue 3) | 管理员可在任何地方操作 |
| 事件存储 | PostgreSQL 分区表 | Phase 1 事件量小，无需 Kafka |
| 会话状态 | Redis | Token 管理、心跳、限流 |
| 客户端 SDK | Python 包 | 与 PPT 软件同语言，直接引入 |
| 多租户 | 共享表+tenant_id | Phase 1 最简方案，Phase 2 可升级 RLS |

## 4. 评审修正记录

### DeepSeek 修正项（6 个必须修正）

1. **wechat_oauth 内存 dict → Redis** — 多实例部署时状态不丢失
2. **事件分区自动创建** — 捕获 InternalError 自动创建当月分区
3. **session_manager DB fallback** — Redis 重启后缓存未命中回源数据库
4. **SDK _mark_local_sent 原子性** — 临时文件 + os.replace 避免数据损坏
5. **PPT 离线模式** — 本地授权缓存 7 天，网络恢复后上报
6. **X-App-ID 安全校验** — JWT 中 app_id 与请求头匹配验证

### ChatGPT 修正项

7. **ACTIVE_SESSIONS Counter → Gauge** — 反映实时活跃数（可增可减）
8. **SDK 本地事件 pending/sent 标记** — crash-safe，不直接清空文件
9. **Redis 用户状态写时失效** — 禁用用户时立即 `redis.delete()`，无越权窗口
10. **daily_usage_stats 预聚合表** — 看板查询毫秒级响应
11. **权限系统 deny-by-default** — 明确无权限时返回 False

### Claude 修正项

12. **user_roles 联合主键 NULL bug** — scope_id 改为 `NOT NULL DEFAULT '*'`
13. **ack_events 乐观锁** — UPDATE WHERE version = current_version
14. **超管紧急登录** — CLI 工具 `python manage.py create-superuser`
15. **Alembic 迁移审查** — 人工检查生成的 SQL（防止删表）

### 千问修正项

16. **SDK 版本兼容性检查** — API 版本协商 + 升级提示
17. **PgBouncer** — Phase 2 前引入连接池
18. **JWT RS256 密钥轮换** — Phase 2 前从 HS256 升级

## 5. 架构约束（写入设计文档第 9 章）

- 禁止直接查 events 表做业务处理 → 必须走 consumer 模式
- 禁止直接判断角色字符串 → 必须走 PermissionPolicy 接口
- tenant_id 必须从 JWT 解析，不信任请求头
- 所有写操作必须异步写入审计日志
- 权限系统 deny-by-default
- 代码审查清单（6 项必查）

## 6. 前置准备工作（开发前必须完成）

| # | 事项 | 说明 | 预计时间 |
|---|------|------|---------|
| 1 | 微信开放平台注册 | 企业/个体工商户资质 | 1-3 天 |
| 2 | 网站应用创建 | 获取 AppID + AppSecret | 1 天 |
| 3 | 购买域名 | .com 域名 | 即时 |
| 4 | ICP 备案 | 域名备案 | 1-2 周 |
| 5 | 购买云服务器 | 2核4G（阿里云/腾讯云） | 即时 |
| 6 | Docker 安装 | 服务器环境 | 1 小时 |

**年成本**: ~1620 元（服务器 600 + PG 480 + Redis 180 + 域名 60 + 微信认证 300）

## 7. 项目文件结构

```
D:\FABLAB 法贝实验室\13-工具\法贝实验室管理系统\
├── .git/
├── docs/
│   ├── superpowers/
│   │   ├── specs/
│   │   │   └── 2026-04-03-platform-foundation-design.md   ← 设计文档 v1.1
│   │   └── plans/
│   │       └── 2026-04-03-phase1-implementation.md         ← 实现计划 v1.2
│   └── sessions/
│       └── 2026-04-03-session-01-design-review.md           ← 本文件
└── desktop.ini
```

## 8. 下一步行动

1. **用户完成前置准备**（微信注册、域名备案、买服务器）
2. **选择执行方式**:
   - 子代理驱动（推荐）— 每个 Task 独立 agent
   - 内联执行 — 当前会话逐步执行
3. **从 Task 1 开始**（项目骨架 + 基础设施层）

## 9. Git 提交历史

```
45ce3b0 fix: 修正实现计划第五轮评审问题
3a71205 docs: Phase 1 实现计划（8 Task，44 步骤）
f825a12 docs: 添加平台地基设计文档 (Phase 1)
```

## 10. 对话中的用户信息

- 用户是法贝实验室负责人
- 项目需要分发给多校区使用
- 需要多级管理员（自己管理全局 + 各校区负责人管理本校区）
- 用户对后端开发经验较少
- 未来愿景：1000 校区规模的教育管理平台
- Phase 3 视频监控 + Phase 4 AI 分析是长期目标
