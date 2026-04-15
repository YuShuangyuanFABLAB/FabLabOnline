# Session 08 — 生产环境部署

> **日期**: 2026-04-16
> **状态**: 进行中（后端容器启动 Bug 待修复）
> **分支**: master → origin/master

---

## 背景

Phase 1-4 全部开发完成，173 tests，RBAC 验证通过。用户希望将系统部署到阿里云 ECS 进行测试。

---

## 服务器信息

| 项目 | 值 |
|------|-----|
| 云服务商 | 阿里云 ECS |
| 地域 | 华东 1（杭州） |
| 实例规格 | ecs.u1-c1m2.large（2 vCPU / 4 GiB） |
| 操作系统 | Ubuntu 22.04 64位 |
| 系统盘 | ESSD Entry 80 GiB |
| 公网带宽 | 5 Mbps（按固定带宽） |
| 公网 IP | 8.136.122.38 |
| 主私网 IP | 172.16.115.24 |
| 域名 | fablab.net.cn |
| 代码路径 | /opt/fablab |
| 付费类型 | 包年包月（到期 2027-04-15） |

---

## 部署时间线

### Step 1: 购买服务器 ✅
- 选择华东 1（杭州）节点
- Ubuntu 22.04 LTS，2 核 2GB
- 安全组开放 22/80/443 端口

### Step 2: Docker 安装 ✅
- `get.docker.com` 因 GFW 屏蔽失败（SSL connection reset）
- 改用清华镜像站安装成功:
  ```
  apt source: https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu jammy stable
  ```
- Docker Compose v2 通过 apt 安装

### Step 3: Git Clone ✅
- 首次尝试私有仓库 + GitHub 密码认证 → 失败（GitHub 已不支持密码）
- 临时使用 PAT Token → 成功（部署后应撤销）
- 最终方案: 仓库设为 public → `git clone https://github.com/YuShuangyuanFABLAB/FabLabOnline.git`

### Step 4: .env 配置 ✅
- 生成强密码: DB_PASSWORD, ADMIN_PASSWORD
- 生成 JWT 密钥: `python -c "import secrets; print(secrets.token_hex(32))"`
- 配置 DATABASE_URL, REDIS_URL 等
- heredoc 在 SSH 中不稳定，改用 nano 编辑

### Step 5: Docker Build ✅
- 首次构建 pip 访问 PyPI 超时
- Dockerfile 添加清华 pip 镜像: `-i https://pypi.tuna.tsinghua.edu.cn/simple`
- 第二次构建成功

### Step 6: Docker Compose Up ⚠️（进行中）
- db, redis, nginx 容器正常启动
- **backend 容器崩溃循环**，两个错误:
  1. `migrations/env.py:49 — SyntaxError: 'async with' outside async function`
  2. `init_db.py:167 — NameError: name 'hashlib' is not defined`
- **原因分析**: 服务器 clone 时拉到了旧版本代码，本地代码已修复
- **解决方案**: 本地 push → 服务器 `git pull` → `docker compose build backend` → 重启

### Step 7: ICP 备案 ⏳
- .net.cn 域名已购买
- 注册局审核已通过
- ICP 备案已提交，等待管局审核（预计 7-20 天）

---

## 遇到的问题与解决

| # | 问题 | 原因 | 解决 |
|---|------|------|------|
| 1 | Docker 安装失败 | GFW 屏蔽 docker.com | 清华镜像站安装 |
| 2 | pip install 超时 | 国内访问 PyPI 不稳定 | Dockerfile 加清华 pip 镜像 |
| 3 | git clone 认证失败 | GitHub 禁止密码认证 | 仓库改 public |
| 4 | SSH 密码登录拒绝 | 阿里云默认密钥认证 | 控制台重置密码 |
| 5 | heredoc EOF 不识别 | SSH shell 环境差异 | 改用 nano 编辑 |
| 6 | 后端容器崩溃 | 服务器代码版本过旧 | 本地 push 后服务器 pull |

---

## 待完成

| 步骤 | 状态 | 说明 |
|------|------|------|
| 修复后端容器启动 | ⏳ | 本地已 push，服务器需 pull + rebuild |
| ICP 备案通过 | ⏳ | 等待管局审核 |
| DNS A 记录配置 | ⏳ | 备案通过后配置 |
| HTTPS 证书 | ⏳ | Let's Encrypt + certbot |
| CORS 域名配置 | ⏳ | .env CORS_ORIGINS 设置实际域名 |
| 关闭 API 文档 | ⏳ | DOCS_ENABLED=false |
| 微信 OAuth | ⏳ | 备案通过后在微信开放平台配置 |

---

## 代码修改记录

| Commit | 说明 |
|--------|------|
| `5b53431` | feat(production): CORS/文档保护/HTTPS/安全加固/部署指南 |
| `9a6c0cb` | fix(deploy): Dockerfile 添加清华 pip 镜像 |

### 修改的文件

| 文件 | 修改内容 |
|------|---------|
| `Dockerfile` | 添加清华 pip 镜像 |
| `后端/config/settings.py` | 新增 CORS_ORIGINS, DOCS_ENABLED, ADMIN_PASSWORD |
| `后端/main.py` | CORS 动态读取配置, docs 条件挂载 |
| `后端/init_db.py` | 支持 ADMIN_PASSWORD 环境变量覆盖默认密码 |
| `nginx.conf` | 安全头、统一 proxy_set_header |
| `nginx-frontend.conf` | 安全头 |
| `nginx-ssl.conf` | 新建 HTTPS 配置模板 |
| `后端/tests/test_production_readiness.py` | 新建生产就绪测试 |
| `后端/docs/deployment-guide.md` | 新建完整部署指南 |

---

## 关键经验

1. **国内部署三件套镜像**: Docker CE 清华源、pip 清华源、npm 淘宝源
2. **GitHub 私有仓库**: 需 PAT 或 SSH key，公开仓库最简单
3. **阿里云 ECS**: 默认密码登录关闭，需控制台重置
4. **ICP 备案**: .net.cn 域名必须备案才能绑定国内服务器
5. **先 IP 测试后域名**: 备案期间可用 IP 直连测试，不阻塞开发
