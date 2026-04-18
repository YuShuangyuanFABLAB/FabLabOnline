# Agent Teams 代码审查报告 — 法贝实验室管理系统

> **审查日期**: 2026-04-13
> **审查方式**: 4 个并行 Agent（后端、前端、安全、架构）
> **对照文档**: `docs/superpowers/audits/2026-04-11-code-audit.md`（21 项已修复）
> **项目状态**（截至 2026-04-13）: Phase 1+2+3 完成，147 tests（当前 178 tests）

---

## 审查总览

| 审查维度 | 审查员 | CRITICAL | HIGH | MEDIUM | LOW | 评分 |
|----------|--------|----------|------|--------|-----|------|
| 后端代码质量 | backend-reviewer | 0 | 3 | 8 | 6 | A- |
| 前端代码质量 | frontend-reviewer | 0 | 3 | 4 | 3 | — |
| 安全与健壮性 | security-reviewer | 3 | 5 | 6 | 5 | B+ |
| 可维护性与可扩展性 | arch-reviewer | 2 | 5 | 6 | 4 | 7.5/10 |

**去重后合计**: CRITICAL 4 项 / HIGH 11 项 / MEDIUM 16 项 / LOW 12 项

---

## 一、CRITICAL — 必须立即修复

### C1. Cookie SameSite 配置为 lax — CSRF 风险
- **文件**: `后端/api/v1/auth.py:105, 231`
- **问题**: `samesite="lax"` 允许跨站 GET 请求携带 Cookie
- **修复**: 改为 `samesite="strict"`
- **工作量**: 5 分钟
- **发现者**: security-reviewer

### C2. .env.example 暴露默认密码和 JWT 密钥
- **文件**: `后端/.env.example`, `后端/config/settings.py:17`
- **问题**: `JWT_SECRET_KEY=change-me-in-production`，部署时可能忘记修改
- **修复**: JWT_SECRET_KEY 改为空值，启动时校验必须设置且 ≥ 32 字符
- **工作量**: 30 分钟
- **发现者**: security-reviewer

### C3. init_db.py 密码明文输出
- **文件**: `后端/init_db.py:173`
- **问题**: `print("Seed data inserted: admin / admin123")`，生产部署日志泄露
- **修复**: 改为 `print("Seed data inserted successfully")`
- **工作量**: 5 分钟
- **发现者**: security-reviewer

### C4. events.py + analytics.py 动态 SQL 拼接注入风险
- **文件**: `后端/api/v1/events.py:38-44`, `后端/api/v1/analytics.py:40-48`
- **问题**: f-string 拼接表名 `events_{tenant_id}`，event_type 来自用户参数未验证
- **修复**: 添加 tenant_id 白名单校验 `re.match(r'^[a-zA-Z0-9_-]+$', tenant_id)`，event_type 使用参数化查询
- **工作量**: 30 分钟
- **发现者**: backend-reviewer, security-reviewer, arch-reviewer（三方交叉确认）

---

## 二、HIGH — 1-2 周内修复

### H1. users.py 重复定义 router
- **文件**: `后端/api/v1/users.py:13, 24`
- **问题**: `router = APIRouter(...)` 定义两次，第二次覆盖第一次
- **修复**: 删除第 24 行重复定义
- **工作量**: 2 分钟
- **发现者**: backend-reviewer

### H2. apps.py 注册应用不返回 app_secret
- **文件**: `后端/api/v1/apps.py:70`
- **问题**: domain 层返回 raw_secret 但 API 层未传递给客户端
- **修复**: API 层完整传递 domain 层返回的 app_secret
- **工作量**: 5 分钟
- **发现者**: backend-reviewer

### H3. analytics.py 无权限校验
- **文件**: `后端/api/v1/analytics.py:51-56`
- **问题**: `user_activity` 端点无权限检查，同租户用户可互相查看
- **修复**: 添加 `check_permission()` 或限制只能查自己
- **工作量**: 10 分钟
- **发现者**: backend-reviewer

### H4. 前端调用不存在的后端 API — roles
- **文件**: `admin-web/src/api/roles.ts:7-11`, `admin-web/src/views/RolesView.vue:113-127`
- **问题**: 前端调 `create()` / `update()` 但后端无 `POST /roles` 和 `PUT /roles/{id}`
- **修复**: 后端添加接口，或前端移除该功能
- **工作量**: 2-3 小时
- **发现者**: frontend-reviewer

### H5. 前端调用不存在的后端 API — apps status
- **文件**: `admin-web/src/api/apps.ts:10-12`, `admin-web/src/views/AppsView.vue:62-71`
- **问题**: 前端调 `toggleStatus()` 但后端无 `PUT /apps/{id}/status`
- **修复**: 后端添加接口，或前端移除该功能
- **工作量**: 1-2 小时
- **发现者**: frontend-reviewer

### H6. 后端角色列表不返回 permissions 字段
- **文件**: `后端/api/v1/roles.py:23-26`, `admin-web/src/views/RolesView.vue:18-28`
- **问题**: 前端期望 `permissions` 数组，后端只返回 `id/name/display_name/level`
- **修复**: 后端 `GET /roles` 联查返回 permissions，或前端并发调用权限接口
- **工作量**: 1 小时
- **发现者**: frontend-reviewer

### H7. JWT 密钥启动时未校验强度
- **文件**: `后端/config/settings.py:17`
- **问题**: 允许弱密钥如 "change-me-in-production"
- **修复**: 添加启动时校验，生产环境必须 ≥ 32 字符
- **工作量**: 30 分钟
- **发现者**: security-reviewer

### H8. manage.py 使用 SHA-256 而非 PBKDF2
- **文件**: `后端/manage.py:15-19`
- **问题**: 管理员密码哈希弱于普通用户（SHA-256 vs PBKDF2-SHA256 480000 次）
- **修复**: 统一使用 `domains/identity/password.py` 的 `hash_password()`
- **工作量**: 10 分钟
- **发现者**: backend-reviewer

### H9. auth.py callback 端点在 response body 中泄露 token
- **文件**: `后端/api/v1/auth.py:169`
- **问题**: 微信 OAuth 回调同时通过 Cookie 和 response body 返回 token
- **修复**: 删除 response body 中的 token 字段
- **工作量**: 5 分钟
- **发现者**: security-reviewer

### H10. Docker 部署存在单点故障
- **文件**: `docker-compose.yml`
- **问题**: Redis 无持久化、数据库单容器、Nginx 单实例
- **修复**: Redis 启用 AOF，生产用托管 PG，外部负载均衡
- **工作量**: 2-4 小时
- **发现者**: arch-reviewer

### H11. SDK 缺少版本控制和兼容性保证
- **文件**: `sdk/fablab_sdk/client.py`, `sdk/pyproject.toml`
- **问题**: 无 API 版本控制、无向后兼容策略、无弃用通知
- **修复**: 添加 API 版本参数、SemVer 规则、deprecated 警告
- **工作量**: 3-4 小时
- **发现者**: arch-reviewer

---

## 三、MEDIUM — 下个迭代修复

### M1. auth.py 登录响应格式不一致
- **文件**: `后端/api/v1/auth.py:92-108`
- **问题**: 用字符串拼接构造 JSON，非 Pythonic
- **修复**: 使用 `json.dumps()` 或 JSONResponse
- **工作量**: 5 分钟
- **发现者**: backend-reviewer

### M2. auth.py 心跳重复代码
- **文件**: `后端/api/v1/auth.py:195-212`
- **问题**: Bearer token 和 Cookie 续签逻辑几乎完全重复
- **修复**: 提取公共函数 `_maybe_renew_token()`
- **工作量**: 10 分钟
- **发现者**: backend-reviewer

### M3. 登录限流键名可预测
- **文件**: `后端/api/v1/auth.py:35-36`
- **问题**: 仅基于 user_id，无 IP 级限流
- **修复**: 统一小写规范化 + 添加 IP 级限流
- **工作量**: 2 小时
- **发现者**: security-reviewer

### M4. 缺少 HTTPS/TLS 配置
- **文件**: `nginx.conf:17`, `后端/api/v1/auth.py:104`
- **问题**: 仅 HTTP 80，Cookie Secure 在 DEBUG 模式下为 false
- **修复**: 添加 Let's Encrypt 配置模板，生产强制 HTTPS
- **工作量**: 2 小时
- **发现者**: security-reviewer

### M5. 配置管理缺乏多环境支持
- **文件**: `后端/config/settings.py`
- **问题**: 单一 Settings 类，无 dev/staging/prod 分离
- **修复**: 使用 pydantic-settings 多环境支持
- **工作量**: 2-3 小时
- **发现者**: arch-reviewer

### M6. 前端缺少响应数据类型定义
- **文件**: `admin-web/src/api/*.ts`
- **问题**: 所有 API 调用使用隐式 axios 类型，无 TypeScript 接口
- **修复**: 定义 `ListResponse<T>` 等泛型接口
- **工作量**: 3-4 小时
- **发现者**: frontend-reviewer

### M7. 前端错误处理不够细致
- **文件**: `admin-web/src/views/UsersView.vue`, `CampusesView.vue` 等
- **问题**: 空 catch 块或仅通用错误消息，不区分 403/404/网络错误
- **修复**: 添加错误分类处理
- **工作量**: 2 小时
- **发现者**: frontend-reviewer

### M8. 前端搜索是前端过滤而非后端搜索
- **文件**: `admin-web/src/views/UsersView.vue:102-105`
- **问题**: 只能搜索当前页已加载用户
- **修复**: 后端添加 name 参数搜索，前端传参
- **工作量**: 1 小时
- **发现者**: frontend-reviewer

### M9. _INIT_DEFAULTS 与 server_default 不一致
- **文件**: `后端/models/role.py:17`, `后端/models/app.py:18`
- **问题**: 部分模型用 `_INIT_DEFAULTS`，部分用 `server_default`，模式不统一
- **修复**: 统一使用 Alembic 迁移的 `server_default`
- **工作量**: 20 分钟
- **发现者**: backend-reviewer

### M10. TenantModel.tenant_query() 方法未使用
- **文件**: `后端/models/base.py:31-39`
- **问题**: 定义了安全查询方法但实际代码中未调用
- **修复**: 在所有 API 路由中使用 `tenant_query()` 替代手动构造查询
- **工作量**: 30 分钟
- **发现者**: backend-reviewer

### M11. 缺少 API 文档自动化
- **问题**: 无 OpenAPI spec 导出、无变更日志、无契约版本控制
- **修复**: 配置 OpenAPI 元数据，前端用 openapi-typescript 生成 SDK
- **工作量**: 2-3 小时
- **发现者**: arch-reviewer

### M12. 分区表创建依赖应用启动
- **文件**: `后端/main.py:32-37`
- **问题**: 长时间未启动后新月份分区缺失
- **修复**: 改为定时任务（APScheduler）自动创建
- **工作量**: 2 小时
- **发现者**: arch-reviewer

### M13. 缺少国际化（i18n）支持
- **文件**: `admin-web/src/views/*.vue`
- **问题**: 所有字符串硬编码中文
- **修复**: 使用 vue-i18n，提取字符串到 locale 文件
- **工作量**: 4-6 小时
- **发现者**: arch-reviewer

### M14. 数据库/Redis 连接池配置固定
- **文件**: `后端/infrastructure/database.py:6-13`, `后端/infrastructure/redis.py:4`
- **问题**: DB 连接池固定，Redis 无连接池
- **修复**: 配置移至 settings.py，Redis 使用 ConnectionPool
- **工作量**: 1 小时
- **发现者**: arch-reviewer

### M15. 缺少通用速率限制中间件
- **问题**: 仅登录端点有限速，其他 API 无限制
- **修复**: 添加基于 IP/token 的通用速率限制
- **工作量**: 3 小时
- **发现者**: security-reviewer, backend-reviewer

### M16. 审计日志 user_role 字段未填充
- **文件**: `后端/domains/access/audit.py:12-22`
- **问题**: 多数调用方传 `None`
- **修复**: 从 RBAC 系统获取用户角色后传入
- **工作量**: 2 小时
- **发现者**: security-reviewer

---

## 四、LOW — 记录备忘

| ID | 问题 | 说明 |
|----|------|------|
| L1 | 日志配置在 import 时执行 | `main.py:13`，测试可能干扰 |
| L2 | 健康检查无超时保护 | DB/Redis 卡死导致响应慢 |
| L3 | Redis 无密码保护 | docker-compose 无 requirepass |
| L4 | CORS 允许所有 methods/headers | 应限制为实际需要的 |
| L5 | 审计日志失败时降级 | DB 写入失败只记日志，可能丢记录 |
| L6 | 依赖版本未锁定 | requirements.txt 使用 `>=` 范围 |
| L7 | App Secret 种子数据明文 | init_db.py 中硬编码 |
| L8 | 前端路由守卫每次导航调 heartbeat | 可能产生额外请求 |
| L9 | 前端硬编码权限列表 | RolesView.vue availablePermissions |
| L10 | 前端测试覆盖不足 | 仅 2 个测试文件 |
| L11 | 缺少 pytest-cov 覆盖率报告 | 无法确认实际覆盖率 |
| L12 | SDK 使用 sha256 生成 app_secret | 可直接用 secrets.token_urlsafe |

---

## 五、与上次审计对比

| 维度 | 2026-04-11 审计 | 2026-04-13 审查 | 变化 |
|------|----------------|----------------|------|
| CRITICAL | 3（C1-C3） | 4 | 旧的全部修复，发现新的 |
| HIGH | 5（H1-H5） | 11 | 旧的全部修复，发现新的（主要是前后端对齐） |
| 整体安全 | D → B+ | B+ | 核心安全机制到位 |
| 前后端对齐 | — | 3 个 HIGH | 上次未覆盖，本次新发现 |
| 架构评估 | — | 7.5/10 | 首次架构评估 |

**关键变化**:
- 上次审计的 21 项问题全部修复 ✅
- 新问题主要来自更深层次的代码审查（上次按文档审计，本次按实际代码审查）
- 前后端 API 对齐是主要的新问题类别
- 安全评分从 D 提升到 B+

---

## 六、修复优先级建议

### Phase 4A — 快速修复（30 分钟内，可一次性完成）

| # | 问题 | 文件 | 工作量 |
|---|------|------|--------|
| 1 | C1: SameSite → strict | auth.py | 5 分钟 |
| 2 | C3: 删除密码明文输出 | init_db.py | 5 分钟 |
| 3 | H1: 删除重复 router | users.py | 2 分钟 |
| 4 | H9: 删除 callback 中 token | auth.py | 5 分钟 |
| 5 | H8: manage.py 用 PBKDF2 | manage.py | 10 分钟 |

### Phase 4B — 安全加固（2-3 小时）

| # | 问题 | 文件 | 工作量 |
|---|------|------|--------|
| 6 | C2: JWT 密钥启动校验 | settings.py | 30 分钟 |
| 7 | C4: SQL 拼接白名单校验 | events.py, analytics.py | 30 分钟 |
| 8 | H7: JWT 密钥强度校验 | settings.py | 30 分钟 |
| 9 | H3: analytics 权限校验 | analytics.py | 10 分钟 |
| 10 | H2: apps 返回 app_secret | apps.py | 5 分钟 |

### Phase 4C — 前后端对齐（4-6 小时）

| # | 问题 | 文件 | 工作量 |
|---|------|------|--------|
| 11 | H4: 后端添加 roles CRUD | roles.py | 2-3 小时 |
| 12 | H5: 后端添加 apps status | apps.py | 1-2 小时 |
| 13 | H6: roles 返回 permissions | roles.py | 1 小时 |

---

## 七、各维度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 后端代码质量 | A- | 分层清晰，mock 合理，少量代码重复 |
| 前端代码质量 | B+ | 架构现代，类型安全待加强，API 对齐需修复 |
| 安全 | B+ | 核心机制到位，配置层面需加固 |
| 可维护性 | 7/10 | 分层清晰，缺多环境配置和 API 文档自动化 |
| 可扩展性 | 8/10 | 领域划分合理，事件流设计优秀 |
| **综合** | **B+** | **产品级基础，按优先级修复后可进入生产** |

---

*报告生成时间: 2026-04-13*
*审查工具: Claude Code Agent Teams（4 并行审查员）*
