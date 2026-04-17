# 会话记录 — 2026-04-03 Session 02

> **会话主题**: 实现计划 v1.2 → v1.4 评审修正（Claude Code + ChatGPT 双轮评审）
> **日期**: 2026-04-03
> **项目路径**: `<项目根目录>`
> **状态**: 实现计划已更新至 v1.4，等待开始实施

---

## 1. 上文衔接

Session 01 完成了设计文档 v1.1（5轮AI评审后冻结）和实现计划 v1.2（8 Task, 44 步骤）。
本轮对实现计划进行两轮代码级评审，修正所有发现的问题。

## 2. 本轮完成的工作

### 2.1 Claude Code 评审修正（第六轮）

发现并修正 13 个问题：

**4 个运行即崩溃 bug:**

| # | 问题 | 修正 |
|---|------|------|
| 1 | `pyjwt` vs `from jose import jwt` 依赖冲突 | requirements.txt 改为 `python-jose[cryptography]` |
| 2 | auth.py 路由缺 `await` | 所有 async 调用加 `await` |
| 3 | WechatOAuth 引用未导入的 `redis_client` | 顶部加 `from infrastructure.redis import redis_client` |
| 4 | 分区表主键不含分区键 `timestamp` | `PRIMARY KEY (event_seq, timestamp)` + raw SQL 建表 |

**5 个隐患:**

| # | 问题 | 修正 |
|---|------|------|
| 5 | pytest-asyncio 无 asyncio_mode 配置 | 增加 pyproject.toml `[tool.pytest.ini_options]` |
| 6 | SDK pyproject.toml build backend 路径错误 | 改为 `setuptools.build_meta` |
| 7 | 微信回调后未创建/查找用户 | 完整实现 find_or_create + JWT 签发 + session 写入 |
| 8 | Alembic 对 JSONB/分区表生成错误迁移 | 详细修正说明 + raw SQL 迁移 |
| 9 | 缺少种子数据（角色/权限/租户） | 新增 Step 8 seed migration + Step 9 manage.py CLI |

**4 个改进:**

| # | 问题 | 修正 |
|---|------|------|
| 10 | httpx 重复 | 合并为一条 |
| 11 | main.py anti-pattern | 导入移至顶部 + `async with` |
| 12 | 管理后台 token 存 localStorage | 改为 httpOnly Cookie |
| 13 | Task 4-8 只有骨架 | 补齐到与 Task 1-3 同等粒度（含完整代码+测试） |

### 2.2 ChatGPT 评审修正（第七轮）

发现并修正 3 个关键性能/安全问题：

**3 个必改项:**

| # | 问题 | 修正 |
|---|------|------|
| 14 | 事件逐条写 DB，高峰必炸 | **asyncio.Queue 缓冲 + 批量 INSERT**（100条/批，1秒超时），API 毫秒级返回 |
| 15 | 每次请求查 DB 获取权限 | **Redis 缓存 `user_permissions:{user_id}`**，TTL 5min，角色变更时主动失效 |
| 16 | 多租户隔离靠人自觉 | **TenantModel 基类**：`tenant_query()` 强制带 tenant_id + `assert_tenant_owned()` 写前校验 |

**5 个 Phase 2 增强项（已记录，不阻塞 Phase 1）:**

1. Refresh Token 分离（access 2h + refresh 7d）
2. Redis Stream 替代内存队列
3. 审计日志链式 hash 防篡改
4. 事件冷热分离 / ClickHouse
5. SDK 断网感知

**战略定位升级:**

明确系统定位为**教育 SaaS 平台底座**（非 PPT 工具后端），已具备多应用接入能力：
- `apps` 表 → 应用注册中心
- SDK → 通用客户端接入层
- Event System → 跨应用事件追踪

### 2.3 文件变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `docs/superpowers/plans/2026-04-03-phase1-implementation.md` | 更新 v1.2→v1.4 | 全部 21 个修正项已合并 |
| `docs/sessions/2026-04-03-session-02-plan-review.md` | 新建 | 本文件 |
| `.claude/memory/MEMORY.md` | 更新 | 新增 Session 02 引用 |
| `.claude/memory/platform-project-context.md` | 更新 | 版本号+评审记录+下一步 |

## 3. 当前计划状态

**实现计划 v1.4**，8 个 Task 全部具备可直接执行的代码级步骤：

```
Task 1: 项目骨架 + 基础设施层          ✅ 含 pyproject.toml + asyncio_mode
Task 2: 数据模型 + Alembic 迁移         ✅ 含 TenantModel 防呆 + seed data + manage.py
Task 3: 认证系统                        ✅ 含完整回调流程（用户创建+JWT+session）
Task 4: 组织与权限                      ✅ 含 Redis 权限缓存 + 失效机制 + 完整测试
Task 5: 事件系统                        ✅ 含 Queue 缓冲批量写 + consumer + 预聚合
Task 6: Web 管理后台                    ✅ 含 httpOnly Cookie
Task 7: 客户端 SDK                      ✅ 含正确 build_meta
Task 8: PPT 集成 + Docker 部署          ✅
```

## 4. 关键设计变更（vs v1.1 设计文档）

| 变更 | 设计文档 v1.1 | 实现计划 v1.4 | 原因 |
|------|-------------|-------------|------|
| 事件写入 | 直接 INSERT | asyncio.Queue + 批量 INSERT | 性能：高峰期从逐条变批量 |
| 权限检查 | 每次查 DB | Redis 缓存 + DB fallback | 性能：减少 DB 查询 |
| 多租户 | 靠 Code Review | TenantModel 强制注入 | 安全：防呆机制 |
| Token 存储 | localStorage | httpOnly Cookie | 安全：XSS 防护 |
| 种子数据 | 无 | seed migration + CLI | 可用性：首次启动即可用 |
| JWT 库 | pyjwt | python-jose | 兼容性：代码用 jose API |

## 5. 下一步行动

1. **用户完成前置准备**（微信开放平台注册、域名备案、买服务器）
2. **选择执行方式**（子代理驱动 / 内联执行）
3. **从 Task 1 开始实施**（项目骨架 + 基础设施层）
4. **每完成一个 Task → 运行测试 → 提交**

## 6. 评审总结

| 评审方 | 轮次 | 修正项数 | 状态 |
|--------|------|---------|------|
| DeepSeek | 第1轮 | 6 | ✅ 已合并 |
| 豆包 | 第2轮 | 3 | ✅ 已合并 |
| 千问 | 第3轮 | 3 | ✅ 已合并 |
| ChatGPT | 第4轮 | 2 | ✅ 已合并 |
| Claude | 第5轮 | 3 | ✅ 已合并 |
| Claude Code | 第6轮 | 13 | ✅ 已合并 |
| ChatGPT | 第7轮 | 8 | ✅ 已合并 |
| **合计** | **7轮** | **38项** | **全部修正** |
