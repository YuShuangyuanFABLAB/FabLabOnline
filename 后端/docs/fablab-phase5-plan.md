# 备案等待期开发计划 v2（审阅改进版）

> 目标：ICP 备案审核期间，完成可并行推进的改进
> 前置状态：199 tests, http://8.136.122.38 已上线
> 审阅者：安全审查、代码质量审查、架构审查（3 Agent 并行审阅）

---

## Context

系统已上线，ICP 备案等待中。v1 计划经 3 个专业 Agent 审阅后发现：
- **5 个安全问题**（生产密码默认值、Redis 健康检查将失败、速率限制可绕过、无 JWT 撤销、微信 CSRF）
- **4 个工程质量问题**（Item 2 范围过大、共享文件冲突、路由守卫设计错误、上下文超限风险）
- **3 个架构问题**（Docker 资源限制不当、passlib/pyotp 未用依赖、备份无异地存储）

本版本（v2）修复了所有审阅发现的问题。

---

## 核心改进（相比 v1）

1. **Item 2 拆分为 3 个独立任务**，每个保持在 30K token 上下文预算内
2. **docker-compose.yml / nginx.conf 变更合并为一个基础设施任务**，消除文件冲突
3. **安全修复前置** — CSRF、配置验证、密码问题优先解决
4. **路由守卫改用 roles 数组**（非 highestRole），避免多角色用户权限错误
5. **限流修复简化** — 1 行删除替代复杂清理逻辑
6. **新增清理项** — 移除未用依赖 passlib（保留 pyotp 供 TOTP 使用）
7. **设计文档对齐** — 6 处偏离已记录到 `后端/docs/design-deviations.md`

---

## 依赖图

```
Task A (生产配置) ──┬──> Task B (备份)
                    ├──> Task C (基础设施)
                    │         │
                    │         └──> Task D (CSRF修复)
                    │                   │
                    └───────────────────┴──> Task E (冒烟测试)
                                                   │
                                                   └──> Task F (密码修改后端)
                                                           │
                                                           └──> Task G (登录UX)
Task H (密码页面+路由守卫) ── 依赖 Task F
Task I (HTTPS脚本)     ── 独立
Task J (文档)          ── 独立
```

---

## Task A: 生产配置加固（Critical）

### 做什么
- 增强 `validate_production()` 添加更多检查
- 修复服务器 `.env` 安全隐患
- 创建部署脚本
- 移除未用依赖

### 不做什么
- 不改 Docker 资源限制（Task C 做）
- 不改 docker-compose.yml（Task C 做）
- 不新增抽象方法

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `后端/config/settings.py` | 修改 | ~20行（增强验证，inline log 而非新方法） |
| `后端/tests/test_production_validation.py` | 新建 | ~40行 |
| `scripts/deploy.sh` | 新建 | ~60行 |
| `后端/requirements.txt` | 修改 | 删除 passlib（保留 pyotp 供 TOTP） |

### 具体实现

**settings.py** — 在 `validate_production()` 中增加检查（inline warning，不新加方法）：
```python
def validate_production(self) -> None:
    if not self.DEBUG:
        # 已有：JWT_SECRET_KEY 检查
        ...
        # 新增：
        if not self.ADMIN_PASSWORD:
            logger.warning("ADMIN_PASSWORD 未设置，将使用默认密码")
        if self.DOCS_ENABLED:
            logger.warning("生产环境建议关闭 API 文档 (DOCS_ENABLED=false)")
        if not self.CORS_ORIGINS:
            logger.warning("CORS_ORIGINS 为空，仅允许 localhost 访问")
        wechat_partial = bool(self.WECHAT_APP_ID) != bool(self.WECHAT_APP_SECRET)
        if wechat_partial:
            raise ValueError("微信配置必须同时填写或同时留空")
```

**deploy.sh** — git pull + build + up --force-recreate + health check 循环

**requirements.txt** — 移除 `passlib[bcrypt]>=1.7.4`（保留 pyotp 供 TOTP，设计文档要求 super_admin TOTP 二次验证）

### TDD
是。先写测试验证 validate_production() 的各种情况。

### 服务器手动步骤
1. `openssl rand -hex 32` 生成新 JWT_SECRET_KEY
2. 设置 ADMIN_PASSWORD（仅字母数字+下划线）
3. 修复 REDIS_URL 包含密码
4. 设置 DOCS_ENABLED=false
5. `docker compose up -d --force-recreate`

---

## Task B: 数据库备份自动化（Critical）

### 做什么
- 创建备份脚本（pg_dump + gzip + 轮转）
- 创建恢复脚本

### 不做什么
- 不配 OSS 异地备份（记录为后续 TODO）
- 不改 docker-compose.yml
- 不加新依赖

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `scripts/backup-db.sh` | 新建 | ~80行 |
| `scripts/restore-db.sh` | 新建 | ~60行 |

### 具体实现

**backup-db.sh**:
- `docker compose exec -T db pg_dump -U fablab fablab | gzip > backup.sql.gz`
- 保留策略：7 天日备 + 4 周周备 + 3 月月备
- 路径参数化（不硬编码 `/root/FabLabOnline`）
- 脚本 `chmod 700` 权限

**restore-db.sh**:
- 列出可用备份
- 需 `--confirm` 参数
- gunzip → psql

### TDD
否。基础设施脚本，手动测试。

### 设计文档约束
设计文档 12.1 节规定"云厂商自动备份（保留 30 天）"，但设计假设使用云数据库（RDS）。实际使用 Docker 自建 PostgreSQL，pg_dump 是正确的替代方案。已记录为设计偏离。

---

## Task C: 基础设施加固（High）

### 做什么
- 修复 RateLimitMiddleware 内存泄漏
- nginx 代理 /ready 和 /metrics
- Docker 日志轮转
- Docker 资源限制
- Redis 健康检查添加密码

### 不做什么
- 不引入 cachetools 等新依赖
- 不重写为 Redis 限流（nginx 已有限流）
- 不改后端 workers 数量

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `后端/api/rate_limit.py` | 修改 | ~3行（清理空键） |
| `后端/tests/test_rate_limit_memory.py` | 新建 | ~30行 |
| `nginx.conf` | 修改 | ~15行（添加 /ready, /metrics, ACME） |
| `docker-compose.yml` | 修改 | ~25行（日志轮转 + 资源限制 + Redis 健康检查） |

### 具体实现

**rate_limit.py** — 在 `_is_limited()` 中添加一行删除：
```python
if not hits:
    del self._hits[key]  # 清理空条目，防止内存泄漏
    return False
```

**nginx.conf** — 添加 location 块：
```nginx
location /ready { proxy_pass http://backend; ... }
location /metrics { proxy_pass http://backend; ... }
location /.well-known/acme-challenge/ { root /var/www/certbot; }
```

**docker-compose.yml**:
- 日志轮转：所有服务添加 `logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }`
- 资源限制：db:768M, backend:512M, redis:256M, frontend:64M, nginx:64M
- Redis 健康检查：`redis-cli -a ${REDIS_PASSWORD:-changeme} ping`

### 设计文档约束
设计文档 12.2 节要求 5 项监控指标（CPU > 80%、磁盘 > 85%、DB 连接数 > 80%、事件积压 > 1h、API 5xx > 5%）。当前仅实现基础健康检查。阿里云云监控（免费）可覆盖 CPU 和磁盘指标，Task E 冒烟测试中补充配置说明。

### TDD
是。限流修复需测试（模拟多 IP → 验证过期后 dict 缩小）。

---

## Task D: 微信 CSRF State 验证（High）

### 做什么
- 修复 `handle_callback()` 不验证 state 的 CSRF 漏洞
- 修复前端 QR 码加载失败提示

### 不做什么
- 不写微信注册指南（移到 Task J）
- 不做微信 API 错误处理重构
- 不改前端 QR 组件结构

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `后端/domains/identity/wechat_oauth.py` | 修改 | ~15行 |
| `后端/api/v1/auth.py` | 修改 | ~10行 |
| `后端/tests/test_wechat_csrf.py` | 新建 | ~40行 |
| `admin-web/src/views/LoginView.vue` | 修改 | ~1行（改占位文案） |

### 具体实现

**wechat_oauth.py** — 在 `handle_callback()` 开头：
```python
state_key = f"wx_qr_state:{state}"
state_data = await redis_client.get(state_key)
if not state_data or json.loads(state_data).get("status") != "pending":
    raise ValueError("Invalid or expired state parameter")
# 标记为 consumed
await redis_client.setex(state_key, 300, json.dumps({"status": "consumed"}))
```

**auth.py** — 捕获 ValueError 返回 400：
```python
try:
    result = await oauth.handle_callback(code, state)
except ValueError as e:
    logger.warning(f"WeChat callback failed: {e}")
    raise HTTPException(status_code=400, detail="微信登录失败，请重试")
```

**LoginView.vue** — 一行文案：`"二维码加载中..."` → `"微信扫码暂未开放"`

### TDD
是。3 个测试用例（无效 state → 400、已消费 state → 400、有效 state → 成功）。

---

## Task E: 冒烟测试（High）

### 做什么
- 创建全端点测试脚本
- 手动浏览器验证

### 不做什么
- 不修复发现的 bug（记录为后续任务）
- 不自动提交测试结果

### 前置依赖
Task C 完成（/ready 和 /metrics 可通过 nginx 访问）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `scripts/smoke-test.sh` | 新建 | ~150行 |

### 具体实现
- 登录获取 Cookie → 逐个测试 V1 路由 → 退出
- 每个端点报告 pass/fail
- 最终汇总

### TDD
否。运维脚本。

---

## Task F: 密码修改后端（High）

### 做什么
- 新增 `PUT /api/v1/auth/password` 端点
- 验证旧密码 → 哈希新密码 → 更新 configs 表

### 不做什么
- 不迁移密码存储到 users 表（记录为技术债务）
- 不做忘记密码/邮件重置流程
- 不做管理员重置他人密码

### 设计文档约束
设计文档 6.1 节规定：密码登录**仅限 super_admin**（紧急登录通道），其他角色只能微信扫码。当前密码登录是开发阶段临时方案。Task F 的密码修改功能对应设计文档的"紧急登录通道维护"，微信上线后应限制为 super_admin 专用。

### 前置依赖
Task A 完成（生产配置已加固）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `后端/api/v1/auth.py` | 修改 | ~30行 |
| `后端/tests/test_password_change.py` | 新建 | ~80行 |

### 具体实现
```python
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

@router.put("/password")
async def change_password(request: Request, body: ChangePasswordRequest):
    user_id = request.state.user_id
    # 查询当前 hash (scope="user", scope_id=user_id, key="password_hash")
    # verify_password(body.old_password, current_hash)
    # hash_password(body.new_password) → 更新
    # 返回 {"success": True}
```

### TDD
是。4 个测试用例。

---

## Task G: 登录 UX 优化（Medium）

### 做什么
- 改进登录错误消息（后端错误码 → 友好中文提示）
- 添加 Element Plus 表单内联验证

### 不做什么
- 不做密码修改页面（Task H）
- 不做路由守卫（Task H）
- 不改其他页面的错误处理

### 前置依赖
Task F 完成（密码修改端点存在）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `admin-web/src/views/LoginView.vue` | 修改 | ~20行 |

### 具体实现
- 错误码映射表：`"用户不存在"` → 友好提示、`"密码错误"` → 友好提示、429 → 显示倒计时
- `el-form` :rules 添加 user_id 必填、password 最少 6 位

### TDD
否。前端 UI 改动。

---

## Task H: 密码修改页面 + 路由守卫（High）

### 做什么
- 新建密码修改页面
- 添加路由级权限守卫（用 roles 数组，不是 highestRole）
- Layout 下拉菜单添加"修改密码"入口

### 不做什么
- 不做用户资料编辑页面
- 不做管理员创建/编辑用户页面
- 路由守卫是 UX 优化，不是安全特性（后端 require_permission 才是权威守卫）

### 前置依赖
Task F 完成（后端端点就绪）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `admin-web/src/views/PasswordView.vue` | 新建 | ~100行 |
| `admin-web/src/api/auth.ts` | 修改 | ~5行 |
| `admin-web/src/router/index.ts` | 修改 | ~25行 |
| `admin-web/src/components/Layout.vue` | 修改 | ~5行 |

### 具体实现

**路由守卫**（关键设计修正）：
```typescript
const roleRequired: Record<string, string[]> = {
  '/roles': ['super_admin'],
  '/users': ['super_admin', 'admin'],
  '/config': ['super_admin'],
  // ...
}

// 在 beforeEach 中：
const required = roleRequired[to.path]
if (required && !required.some(r => authStore.user.roles.includes(r))) {
  return navigateTo('/')
}
```

注意：使用 `user.roles.includes(r)` 而非 `highestRole`，因为用户可能有多个角色。

### TDD
否。前端 UI。

---

## Task I: HTTPS 脚本准备（Medium）

### 做什么
- 创建 HTTPS 自动化脚本（备案后一键执行）
- 创建证书续期脚本

### 不做什么
- 不激活 HTTPS（等备案）
- 不改 docker-compose.yml（Task C 已完成资源限制和日志轮转，本任务只加 443 端口和证书卷）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `scripts/setup-https.sh` | 新建 | ~120行 |
| `scripts/renew-cert.sh` | 新建 | ~30行 |
| `docker-compose.yml` | 修改 | ~5行（443 端口 + 证书卷） |

### 具体实现
- setup-https.sh: 安装 acme.sh → webroot 申请 → 安装证书 → 切换 nginx-ssl.conf
- renew-cert.sh: acme.sh --renew → nginx -s reload
- 含 --dry-run 模式

### TDD
否。基础设施脚本。

---

## Task J: 文档（Medium）

### 做什么
- 项目 README.md
- 微信注册指南

### 不做什么
- 不写完整用户手册（等微信上线后写，避免描述过时流程）
- 不写 API 参考文档（FastAPI /docs 已有）

### 文件变更
| 文件 | 操作 | 行数 |
|------|------|------|
| `README.md` | 新建 | ~80行 |
| `后端/docs/wechat-setup-guide.md` | 新建 | ~80行 |

### TDD
否。文档。

---

## 执行时间线

| 阶段 | 任务 | 上下文预算 |
|------|------|------------|
| Day 1 AM | Task A（生产配置） | ~15K |
| Day 1 PM | Task B（备份）+ Task D（CSRF） | ~12K |
| Day 2 AM | Task C（基础设施） | ~20K |
| Day 2 PM | Task E（冒烟测试） | ~10K |
| Day 3 AM | Task F（密码修改后端） | ~20K |
| Day 3 PM | Task G（登录 UX） | ~10K |
| Day 4 AM | Task H（密码页面+路由守卫） | ~15K |
| Day 4 PM | Task I（HTTPS 脚本）+ Task J（文档） | ~15K |

所有任务均在 30K token 上下文预算内。

---

## 验证方案

**每个 Task 完成后**：
1. `python -m pytest -v` — 后端全量通过
2. `npm run build` — 前端构建成功
3. git commit + push

**全部完成后**：
1. 服务器运行 `deploy.sh` 更新
2. 运行 `smoke-test.sh` 验证全端点
3. 浏览器手动测试密码修改 + 路由守卫
4. 验证备份脚本正常工作

---

## 设计文档偏离记录

完整记录见 `后端/docs/design-deviations.md`，共 6 项偏离：

| 编号 | 偏离 | 类型 | 风险 |
|------|------|------|------|
| DEV-01 | 密码登录扩展到所有用户（设计要求仅 super_admin） | 临时性 | 低 |
| DEV-02 | TOTP 未实现（设计要求 super_admin 必须有） | 延期 | 中 |
| DEV-03 | PBKDF2 替代 bcrypt（Python 3.14 不兼容） | 技术替代 | 低 |
| DEV-04 | HttpOnly Cookie 替代 Bearer Token | 改进型 | 无 |
| DEV-05 | pg_dump 替代云厂商自动备份 | 成本驱动 | 中 |
| DEV-06 | 监控方案简化（仅基础健康检查） | 阶段简化 | 低 |
