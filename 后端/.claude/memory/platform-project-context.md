# 法贝实验室管理平台 — 项目状态

> 最后更新: 2026-04-16
> **GitHub**: `YuShuangyuanFABLAB/FabLabOnline`
> **当前阶段**: 生产部署进行中，178 tests

---

## 一、文档位置

| 文件 | 路径 |
|------|------|
| 设计文档 v1.1 | `后端/docs/superpowers/specs/2026-04-03-platform-foundation-design.md` |
| 实现计划 v1.4 | `后端/docs/superpowers/plans/2026-04-03-phase1-implementation.md` |
| 代码审计报告 | `后端/docs/superpowers/audits/2026-04-11-code-audit.md` — 21 项全部修复 |
| Session 01 设计评审 | `后端/docs/sessions/2026-04-03-session-01-design-review.md` |
| Session 02 计划评审 | `后端/docs/sessions/2026-04-03-session-02-plan-review.md` |
| Session 03 审计+UI | `后端/docs/sessions/2026-04-11-session-03-code-audit.md` |
| Session 04 Phase 2 | `后端/docs/sessions/2026-04-12-session-04-phase2-security.md` |
| Session 05 Phase 3 | `后端/docs/sessions/2026-04-12-session-05-phase3-quality.md` |
| Session 06 Phase 4 | `后端/docs/sessions/2026-04-14-session-06-phase4-hardening.md` |
| Session 07 RBAC 验证 | `后端/docs/sessions/2026-04-15-session-07-rbac-testing.md` |
| Session 08 生产部署 | `后端/docs/sessions/2026-04-16-session-08-deployment.md` |
| 部署指南 | `后端/docs/deployment-guide.md` |
| Agent Teams 审查 | `后端/docs/superpowers/audits/2026-04-13-agent-teams-review.md` — 43 项发现 |

---

## 二、生产部署状态

### 部署环境

| 项目 | 值 |
|------|-----|
| 云服务商 | 阿里云 ECS（华东 1 杭州） |
| 实例规格 | ecs.u1-c1m2.large（2 vCPU / 4 GiB） |
| 操作系统 | Ubuntu 22.04 64位 |
| 系统盘 | ESSD Entry 80 GiB |
| 公网带宽 | 5 Mbps（按固定带宽） |
| 公网 IP | 8.136.122.38 |
| 主私网 IP | 172.16.115.24 |
| 域名 | fablab.net.cn（ICP 备案中） |
| 代码路径 | /opt/fablab |
| 付费类型 | 包年包月（到期 2027-04-15） |

### 部署进度

| 步骤 | 状态 |
|------|------|
| Docker 安装 | ✅ 清华镜像源 |
| 代码 Clone | ✅ 仓库已设为 public |
| .env 配置 | ✅ 强密码已配置 |
| Docker Build | ✅ 清华 pip 镜像 |
| 后端容器 | ⚠️ 待修复（服务器代码版本同步） |
| ICP 备案 | ⏳ 管局审核中 |
| DNS 配置 | ⏳ 备案通过后 |
| HTTPS | ⏳ Let's Encrypt |
| CORS 域名 | ⏳ 备案通过后配置 |
| API 文档关闭 | ⏳ DOCS_ENABLED=false |
| 微信 OAuth | ⏳ 备案后配置 |

### 生产环境 .env 配置项

| 变量 | 说明 | 状态 |
|------|------|------|
| DB_PASSWORD | 随机强密码 | ✅ 已配置 |
| JWT_SECRET_KEY | 64 字符 hex | ✅ 已配置 |
| ADMIN_PASSWORD | 随机强密码 | ✅ 已配置 |
| CORS_ORIGINS | 域名白名单 | ⏳ 备案后填 |
| DOCS_ENABLED | false | ⏳ 备案后改 |
| WECHAT_APP_ID | 微信开放平台 | ⏳ 备案后申请 |

---

## 三、设计概要

- **架构**: FastAPI + PostgreSQL + Redis + Vue 3 + Nginx + Docker
- **认证**: 微信扫码登录 + 密码登录(限流) + JWT HttpOnly Cookie 7天过期
- **密码**: PBKDF2-SHA256 480000 次迭代 + 随机盐（`domains/identity/password.py`）
- **权限**: RBAC（3 角色: super_admin/admin/teacher）+ Redis 权限缓存 5min TTL + 真实角色查询
- **事件**: PostgreSQL 分区表 + asyncio.Queue 批量写入 + 优雅关闭
- **多租户**: TenantModel 防呆基类（无重复声明）
- **审计**: 全写操作审计日志 + ip_address/user_agent + 查询端点 GET /audit/logs
- **SDK**: Python 包（keyring + JSONL + 熔断器）

---

## 四、审计修复状态

### Phase 1 — 安全加固 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| C1 | Token → HttpOnly Cookie | auth.py, client.ts, LoginView.vue, router/index.ts |
| C2 | SHA-256 → PBKDF2-SHA256 480000 次 | password.py, auth.py, init_db.py |
| C3 | 登录限流 5 次/15 分钟 | auth.py (Redis INCR + EXPIRE) |
| H1 | 用户信息刷新恢复 | router/index.ts (heartbeat 路由守卫) |
| H5 | CORSMiddleware | main.py |

### Phase 2 — 数据完整性 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| H4 | 真实角色查询 | auth.py (get_user_roles) |
| H2 | 审计日志全覆盖 | config.py, apps.py, users.py, campuses.py |
| H3 | Alembic + init_db fallback | init_db.py, Dockerfile |

### Phase 3 — 工程质量 ✅（2026-04-12）
| ID | 修复 | 文件 |
|----|------|------|
| M5 | 消除 tenant_id 重复声明 | models/user.py, models/campus.py |
| M6 | 禁止删除系统角色 | api/v1/roles.py (DELETE + is_system) |
| M7 | 优雅关闭 | store.py (drain_queue) + main.py (shutdown_event) |
| M8 | Pydantic 请求校验 | campuses.py, apps.py, config.py, users.py |
| M4 | 前端 API 封装 + 审计端点 | audit.py 端点 + audit/apps/config.ts |

### Phase 4 — 安全加固 + 前后端对齐 + 基础设施 ✅（2026-04-14）
| ID | 修复 | 文件 |
|----|------|------|
| C1 | Cookie SameSite strict | auth.py |
| C3 | 删除密码明文输出 | init_db.py |
| C4 | tenant_id SQL 注入白名单校验 | events.py, analytics.py |
| H1 | 删除重复 router | users.py |
| H2 | apps 返回 app_secret | apps.py |
| H3 | analytics 权限校验 | analytics.py |
| H4 | POST/PUT /roles CRUD | roles.py |
| H5 | PUT /apps/{id}/status | apps.py |
| H6 | GET /roles 返回 permissions | roles.py |
| H7 | JWT 密钥生产环境校验 | settings.py |
| H8 | manage.py PBKDF2 | manage.py |
| H9 | 删除 callback token 泄露 | auth.py |
| H10 | Redis AOF 持久化 | docker-compose.yml |
| H11 | SDK 版本号 | client.py |
| M1 | 登录响应 json.dumps | auth.py |
| M2 | 心跳续签去重 | auth.py |
| M9 | Role 默认值对齐 | models/role.py |
| M14 | Redis 连接池 | redis.py |

### RBAC 验证 + 角色名对齐 ✅（2026-04-15）
| 修复 | 文件 |
|------|------|
| 创建 teacher1/admin 测试用户 | Docker 环境验证 |
| 前端角色名 org_admin→admin 对齐 | auth.ts, Layout.vue |

### 生产部署准备 ✅（2026-04-16）
| 修复 | 文件 |
|------|------|
| CORS 动态配置 | settings.py, main.py |
| API 文档生产关闭 | settings.py, main.py |
| 管理员密码环境变量 | init_db.py |
| Dockerfile pip 清华镜像 | Dockerfile |
| Nginx 安全头 | nginx.conf, nginx-frontend.conf |
| HTTPS 配置模板 | nginx-ssl.conf |
| 部署指南文档 | docs/deployment-guide.md |
| 生产就绪测试 | tests/test_production_readiness.py |

### 未修复（LOW / 后续迭代）
| ID | 问题 | 说明 |
|----|------|------|
| M4 | Cookie Secure 生产环境 | 需 HTTPS 部署后生效 |
| M5 | 多环境配置分离 | pydantic-settings 多环境 |
| M6 | 前端 TypeScript 接口 | 缺响应类型定义 |
| M7 | 前端错误处理 | 不区分 403/404/网络错误 |
| M8 | 前端搜索用后端 | 当前仅过滤已加载页 |
| M10 | TenantModel.tenant_query 未使用 | 安全查询方法 |
| M11 | 缺 OpenAPI 文档自动化 | 前端可用 openapi-typescript |
| M12 | 分区创建改定时任务 | 当前依赖应用启动 |
| M13 | 缺 i18n | 字符串硬编码中文 |
| M15 | 通用速率限制中间件 | 仅登录有限速 |
| M16 | 审计日志 user_role 未填充 | 多数调用方传 None |

---

## 五、测试状态

| 类别 | 数量 |
|------|------|
| 后端 | 173 passed |
| 前端 | 5 passed + 构建成功 |
| 生产就绪 | 5 passed |
| **总计** | **178 tests（本地）** |

---

## 六、测试用户

| 用户 | 密码 | 角色 | 用途 |
|------|------|------|------|
| `admin` | `admin123`（本地）/ 环境变量（生产） | super_admin | 全权限管理 |
| `orgadmin1` | `orgadmin123` | admin | 中间权限层 |
| `teacher1` | `teacher123` | teacher | 最低权限 |

---

## 七、关键代码路径

### 认证流程
```
LoginView.vue → POST /auth/login → auth.py
  → password.py (verify_password PBKDF2)
  → Redis 限流检查
  → response.set_cookie(token, httponly=True)
  → get_user_roles() → 返回真实角色

router/index.ts → heartbeat 守卫 → POST /auth/heartbeat
  → 验证 Cookie JWT → 恢复 authStore.user + roles
```

### 前端菜单过滤
```
Layout.vue → showMenu(resource)
  → authStore.highestRole（优先级: super_admin > admin > teacher）
  → menuVisibility[resource].includes(role)
```

---

## 八、下一步

1. **修复服务器后端容器** — pull 最新代码 + rebuild
2. **等待 ICP 备案通过** — 约 7-20 天
3. **备案通过后**:
   - 配置 DNS A 记录（fablab.net.cn → 8.136.122.38）
   - 申请 Let's Encrypt HTTPS 证书
   - 设置 CORS_ORIGINS 为实际域名
   - 设置 DOCS_ENABLED=false
   - 申请微信开放平台 OAuth
4. **给 admin 角色分配权限** — user:read, campus:read, analytics:read, audit:read
