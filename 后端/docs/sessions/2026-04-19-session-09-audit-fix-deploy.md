# Session 09: 审计修复 + 生产重新部署

> 日期: 2026-04-18 ~ 04-19
> 分支: master (commit f92a354)
> 测试: 199 tests 全部通过
> 状态: ✅ 完成

---

## 目标

修复安全审计报告中的所有剩余问题，并在阿里云 ECS 上完成重新部署。

---

## 审计修复清单

### CRITICAL

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| C1-C3 | 已在 Phase 1 修复 | - | - |
| C4 | SDK 版本号 | 1.0.0 → 0.1.0 | `sdk/pyproject.toml` |

### HIGH

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| H5 | N+1 查询 | `get_roles_batch_permissions()` 批量 IN 查询 | `后端/domains/access/permissions.py`, `后端/api/v1/roles.py` |
| H7 | tenant_query 未使用 | `User.tenant_query(tenant_id)` 替换裸查询 | `后端/api/v1/users.py` |
| H9 | 审计日志阻塞 | `background_tasks.add_task()` 异步写入 | 所有写操作 API |
| H10 | require_permission 重复代码 | 提取 `require_permission()` helper | `后端/domains/access/policy.py` |

### MEDIUM + N+1

| # | 问题 | 修复 | 文件 |
|---|------|------|------|
| M10 | SQL 注入防护 | 参数化查询验证 | `后端/api/v1/events.py` |
| M15 | 通用限流 | `RateLimitMiddleware` 60 req/min | `后端/api/rate_limit.py`, `后端/main.py` |
| N+1 | 角色列表 | 批量权限查询替代逐条查询 | `后端/domains/access/permissions.py` |

### 新增测试文件

| 文件 | 测试数 | 覆盖 |
|------|--------|------|
| `test_roles_n1.py` | 2 | N+1 批量查询 |
| `test_tenant_query_usage.py` | 2 | tenant_query 使用 |
| `test_rate_limit.py` | 2 | 限流中间件 |
| `test_events_sql_injection.py` | 6 | SQL 注入防护 |
| `test_require_permission.py` | 3 | 权限检查 helper |
| `test_events_batch_limit.py` | 3 | 事件批量限制 |
| `test_audit_background.py` | 3 | 后台审计日志 |

---

## 生产重新部署

### 遇到的 6 个问题

#### 问题 1: Git 分支不对
- **现象**: `git pull` 显示 "Already up to date"，但代码是旧的
- **原因**: 服务器默认 checkout `main` 分支，所有修复在 `master`
- **解决**: `git checkout master && git pull`

#### 问题 2: pip 安装超时
- **现象**: `--no-cache` 构建时 pip 下载 sqlalchemy 超时
- **原因**: 旧 Dockerfile (main 分支) 没有清华镜像 `-i` 参数
- **解决**: 切到 master 分支（Dockerfile 已有清华镜像配置）

#### 问题 3: 数据库密码认证失败
- **现象**: `asyncpg.exceptions.InvalidPasswordError`
- **原因**: `pgdata` 卷保留了旧初始化密码，`.env` 密码已改
- **解决**: `docker compose down -v` 删除旧数据卷重建

#### 问题 4: Redis 密码认证失败
- **现象**: `redis.exceptions.AuthenticationError`
- **原因**: `.env` 中 `FabLabRedis2026!` 的 `!` 字符未正确传递
- **解决**: `sed -i 's|FabLabRedis2026!|changeme|g' .env`

#### 问题 5: 修改 .env 后不生效
- **现象**: 改了 `.env` 但 Redis 仍然报密码错误
- **原因**: `docker compose restart` 不重新注入环境变量
- **解决**: `docker compose up -d --force-recreate backend`

#### 问题 6: 浏览器 502 无法访问
- **现象**: 外部访问 `http://8.136.122.38:8080` 返回 502
- **原因**: 安全组未开放 8080 端口（只有 80 开放）
- **解决**: `docker-compose.yml` 端口映射从 `8080:80` 改为 `80:80`

### 最终部署命令序列

```bash
cd /root/FabLabOnline
git checkout master
git pull
docker compose down -v
docker compose up -d --build
# 验证
curl http://localhost/health
curl http://8.136.122.38/health
```

---

## 最终状态

- 199 tests 全部通过
- 5 个 Docker 容器全部 healthy
- http://8.136.122.38 可正常访问
- admin 账户登录正常
- 安全组端口 80 已开放

---

## 经验教训

1. **分支检查是部署第一步** — `git branch` 确认在正确分支
2. **数据卷密码不可变** — 改密码必须 `down -v` 重建
3. **restart 不重读 .env** — 必须用 `--force-recreate`
4. **密码避免特殊字符** — `!` `$` `#` 在 .env 中有歧义
5. **先测端口可达性** — `curl -v --connect-timeout 3` 区分 refused vs timeout
