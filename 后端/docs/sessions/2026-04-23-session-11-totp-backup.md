# Session 11: TOTP 二次验证 + 备份 cron + 部署更新

> 日期: 2026-04-23
> 前置状态: 221 tests, http://8.136.122.38 已部署
> 结束状态: 231 tests, TOTP + 备份 cron 完成, 服务器已更新

## 背景

ICP 备案审核中。文档审阅确认 TOTP 二次验证（DEV-02）和备份 cron 是备案等待期最有价值的改进。

## 执行摘要

### 1. 服务器部署更新

- 服务器从 f92a354 更新到 8a4e985（+10 Task）
- Docker 镜像加速器配置（`docker.1panel.live`）
- 5 容器全部 healthy
- 冒烟测试通过：health、登录、密码修改（401/422）、心跳

### 2. SSH 免密登录

- 生成 ed25519 密钥 `~/.ssh/id_ed25519`
- 公钥添加到服务器 `authorized_keys`
- 验证：`ssh -o PasswordAuthentication=no root@8.136.122.38` 成功

### 3. 备份 cron 定时任务

- crontab: `0 3 * * *` 每天 3:00 执行 `backup-db.sh`
- 日志写入 `/var/log/fablab-backup.log`
- 7 日日备 + 4 周周备自动轮转

### 4. TOTP 二次验证

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/totp/setup` | POST | 生成 TOTP 密钥，返回 secret + URI |
| `/api/v1/auth/totp/verify` | POST | 验证 TOTP 码，签发 JWT |

**登录流程变更：**
1. 用户提交密码
2. 密码正确后查询 TOTP 配置
3. 已启用 → 返回 `{"totp_required": true, "totp_challenge": "xxx"}`
4. 前端提交验证码 + challenge
5. 验证通过 → 签发 JWT（HttpOnly Cookie）

**文件变更：**

| 文件 | 操作 |
|------|------|
| `domains/identity/totp.py` | 新建（密钥生成 + 验证 + URI） |
| `api/v1/auth.py` | 修改（+109 行：setup/verify 端点 + 登录流程） |
| `api/middleware.py` | 修改（+1 行：/totp/verify 免认证） |
| `tests/test_totp.py` | 新建（10 测试） |
| 7 个旧测试文件 | 修改（适配第 3 次 DB 查询） |

## 关键经验

### 1. 登录流程变更需更新所有依赖测试

给登录流程增加 TOTP 查询后，7 个旧登录测试因 `side_effect` 只有 2 个元素而失败。每次修改 DB 查询数量，必须 grep 所有测试中的 `side_effect` 并补齐。

### 2. session_mgr.cache_user_status 需要 mock

登录成功后 `session_mgr.cache_user_status()` 通过 `redis_client` 写入。测试必须 `patch("api.v1.auth.session_mgr.cache_user_status")`，否则连接真实 Redis 失败。

### 3. Docker Hub 国内镜像不稳定

腾讯云镜像 DNS 不通（`mirror.ccs.tencentyun.com`），改用 `docker.1panel.live` 成功。建议配置多个备选源。

### 4. TOTP challenge 用 Redis TTL 管理生命周期

登录密码通过后生成 challenge 存入 Redis（TTL 300s），TOTP 验证通过后删除。无需额外数据表，自动过期防滥用。

## 提交记录

```
a88dce8 feat(auth): TOTP 二次验证 + 备份 cron 定时任务
8a4e985 docs: Session 10 备案等待期生产加固记录
```

## 设计偏离更新

DEV-02（TOTP 未实现）已解决，偏离记录从 6 项减少为 5 项。

## 待办

- [ ] 前端 TOTP 输入界面（当前仅后端就绪）
- [ ] ICP 备案通过后：DNS + HTTPS + 微信 OAuth
- [ ] 微信上线后：密码登录限制为 super_admin only（DEV-01）
