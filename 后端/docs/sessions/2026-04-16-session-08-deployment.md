# Session 08 — 生产环境部署

> **日期**: 2026-04-16 ~ 2026-04-17
> **状态**: IP 直连已上线，ICP 备案审核中
> **分支**: master → origin/master

---

## 背景

Phase 1-4 全部开发完成，178 tests，RBAC 验证通过。将系统部署到阿里云 ECS 进行测试。

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
| 域名 | fablab.net.cn（ICP 备案中） |
| 代码路径 | /opt/fablab |
| 付费类型 | 包年包月（到期 2027-04-15） |
| 访问地址 | `http://8.136.122.38`（备案后切换 https://fablab.net.cn） |

---

## 部署时间线

### Step 1: 购买服务器 ✅
- 选择华东 1（杭州）节点
- Ubuntu 22.04 LTS，2 vCPU / 4 GiB
- 安全组默认仅开放 22/3389

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

### Step 6: 后端容器修复 ✅
- 服务器在 `main` 分支，代码在 `master` 分支 → `git checkout master` 切换
- 本地改动 Dockerfile 被 stash → `git stash && git checkout master`
- `docker compose build backend` + `docker compose up -d` → 后端启动成功

### Step 7: 安全组配置 ✅
- 阿里云安全组默认未开放 80/443
- 手动添加入方向规则: TCP 80/80 + TCP 443/443，授权对象 0.0.0.0/0
- 使用快捷配置: 「Web HTTP 流量访问」+「Web HTTPS 流量访问」

### Step 8: Nginx 端口修正 ✅
- docker-compose.yml 映射 8080:80 → 浏览器需输端口号
- 改为 80:80 → 直接访问 `http://8.136.122.38`

### Step 9: CORS 配置 ✅
- `.env` 添加 `CORS_ORIGINS=http://8.136.122.38,http://8.136.122.38:8080`
- `docker compose up -d backend` 重建容器使配置生效

### Step 10: 登录 Cookie 修复 ✅
- **问题**: 登录显示成功但 Cookie 未被浏览器存储 → 后续请求 401 → 跳回登录页
- **根因 A**: Cookie 设置 `secure=True`（DEBUG=false），HTTP 下浏览器拒绝存储 Secure Cookie
- **根因 B**: `docker compose restart` 不更新环境变量，改 DEBUG=true 后需 `docker compose up -d` 重建容器
- **解决**: `.env` 设置 `DEBUG=true` + `docker compose up -d backend`
- **后续**: HTTPS 配好后改回 `DEBUG=false`

### Step 11: ICP 备案 ⏳
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
| 6 | 后端容器崩溃 | 服务器在 main 分支，代码在 master | `git checkout master` |
| 7 | 浏览器无法访问 | 安全组未开放 80/443 | 手动添加入方向规则 |
| 8 | 需要输入端口号 | docker-compose 映射 8080:80 | 改为 80:80 |
| 9 | 登录后跳回登录页 | Cookie secure=True + HTTP + restart 不更新 env | DEBUG=true + up -d 重建 |
| 10 | 密码错误无提示 | 前端未处理错误响应 | 待优化 |

---

## 当前服务状态

| 服务 | 状态 | 说明 |
|------|------|------|
| 前端页面 | ✅ | `http://8.136.122.38` |
| 后端 API | ✅ | 健康 |
| 密码登录 | ✅ | admin + ADMIN_PASSWORD |
| 微信扫码 | ❌ | 返回 503（未配置 WECHAT_APP_ID） |
| ICP 备案 | ⏳ | 管局审核中 |

---

## 待完成（备案通过后）

| 步骤 | 说明 |
|------|------|
| DNS A 记录 | fablab.net.cn → 8.136.122.38 |
| HTTPS 证书 | Let's Encrypt + certbot |
| 安全加固 | DEBUG=false, DOCS_ENABLED=false, CORS_ORIGINS=https://fablab.net.cn |
| 微信 OAuth | 微信开放平台创建网站应用 |
| 密码错误提示 | 前端优化 |

---

## 代码修改记录

| Commit | 说明 |
|--------|------|
| `5b53431` | feat(production): CORS/文档保护/HTTPS/安全加固/部署指南 |
| `9a6c0cb` | fix(deploy): Dockerfile 添加清华 pip 镜像 |
| `fda8fb2` | docs: 新建 Session 08 部署会话记录 |

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
3. **阿里云 ECS**: 默认密码登录关闭，安全组默认不开放 80/443
4. **ICP 备案**: .net.cn 域名必须备案才能绑定国内服务器
5. **先 IP 测试后域名**: 备案期间可用 IP 直连测试，不阻塞开发
6. **docker compose restart ≠ up -d**: restart 不更新 .env 环境变量，修改配置后必须用 `up -d`
7. **Secure Cookie + HTTP = 无效**: 浏览器静默拒绝 HTTP 下的 Secure Cookie，无任何报错
8. **git 分支对齐**: 服务器可能在不同分支，部署前确认 `git branch -v`
