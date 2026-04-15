# 法贝实验室管理系统 — 生产部署指南

> 本文档手把手教你将系统部署上线，配置 HTTPS 和微信扫码登录。
> 适用于没有任何运维经验的新手。
>
> 提供两种部署方式：
>
> - **方案 A**：云服务器（阿里云/腾讯云）
> - **方案 B**：本地笔记本 + Cloudflare Tunnel（免费，推荐新手先试这个）

---

# 方案 A：云服务器部署

在开始之前，你需要准备好以下内容：

### 必须有的

| 项目     | 说明                                | 在哪里获取                           |
| -------- | ----------------------------------- | ------------------------------------ |
| 云服务器 | 2 核 2GB 内存以上，Ubuntu 22.04 LTS | 阿里云/腾讯云控制台购买              |
| 域名     | 如 `fablab.example.com`           | 阿里云/腾讯云/Cloudflare 购买        |
| 域名备案 | 国内服务器必须，约 7-20 天          | 云服务商备案系统                     |
| SSH 工具 | 连接服务器用                        | Windows: PuTTY / PowerShell 自带 ssh |

### 可以后续配置的

| 项目             | 说明                                 |
| ---------------- | ------------------------------------ |
| 微信开放平台账号 | 用于扫码登录，测试阶段可先用密码登录 |
| SSL 证书         | 本指南使用免费的 Let's Encrypt       |

---

## Step 1: 服务器环境安装

### 1.1 连接服务器

```bash
# 用你的服务器公网 IP 替换 <IP>
ssh root@<IP>
```

### 1.2 安装 Docker

```bash
# 一键安装 Docker（官方脚本）
curl -fsSL https://get.docker.com | sh

# 启动 Docker 并设为开机自启
systemctl start docker
systemctl enable docker

# 验证安装
docker --version
docker compose version
```

看到版本号输出即安装成功。

### 1.3 配置防火墙（安全组）

在云服务商控制台找到「安全组」或「防火墙」：

| 端口 | 协议 | 说明                       |
| ---- | ---- | -------------------------- |
| 22   | TCP  | SSH 远程连接               |
| 80   | TCP  | HTTP（用于证书申请和跳转） |
| 443  | TCP  | HTTPS（主要访问端口）      |

**不要开放** 5432（数据库）、6379（Redis）、8000（后端）— 这些只需要内部访问。

---

## Step 2: 获取代码

```bash
# 创建项目目录
mkdir -p /opt/fablab
cd /opt/fablab

# 克隆代码
git clone https://github.com/YuShuangyuanFABLAB/FabLabOnline.git .

# 确认代码已下载
ls -la
```

你应该能看到 `docker-compose.yml`、`Dockerfile`、`后端/`、`admin-web/` 等目录。

---

## Step 3: 配置 .env 文件

这是最重要的步骤。`.env` 文件包含所有敏感配置。

### 3.1 创建 .env 文件

```bash
cd /opt/fablab
cp .env .env.production
```

### 3.2 生成强密码和密钥

```bash
# 生成数据库密码（记下来！）
echo "DB_PASSWORD=$(openssl rand -base64 24)"

# 生成 JWT 密钥（至少 32 字符）
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"

# 生成管理员密码
echo "ADMIN_PASSWORD=$(openssl rand -base64 16)"
```

### 3.3 编辑 .env 文件

```bash
nano .env
```

填入以下内容（把 `<xxx>` 替换为实际值）：

```env
# ─── 数据库 ───
DB_NAME=fablab
DB_USER=fablab
DB_PASSWORD=<Step 3.2 生成的数据库密码>
DATABASE_URL=postgresql+asyncpg://fablab:<数据库密码>@db:5432/fablab
REDIS_URL=redis://redis:6379/0

# ─── 安全 ───
JWT_SECRET_KEY=<Step 3.2 生成的 JWT 密钥>

# ─── 管理员 ───
ADMIN_PASSWORD=<Step 3.2 生成的管理员密码>

# ─── CORS（允许的域名）───
CORS_ORIGINS=https://<你的域名>

# ─── API 文档（生产环境关闭）───
DOCS_ENABLED=false

# ─── 微信 OAuth（暂时留空，Step 9 再填）───
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=

# ─── 其他 ───
APP_VERSION=1.0.0
DEBUG=false
```

保存退出：`Ctrl+O` → `Enter` → `Ctrl+X`

### 3.4 关键配置说明

| 配置项             | 说明                                                     |
| ------------------ | -------------------------------------------------------- |
| `DB_PASSWORD`    | 数据库密码，必须强密码                                   |
| `DATABASE_URL`   | 注意主机名是 `db`（Docker 内部服务名），不是 localhost |
| `JWT_SECRET_KEY` | JWT 签名密钥，泄露 = 任何人可以伪造登录凭证              |
| `ADMIN_PASSWORD` | 管理员 admin 的密码，覆盖默认的 admin123                 |
| `CORS_ORIGINS`   | 你的域名（带 https://），多个用逗号分隔                  |
| `DOCS_ENABLED`   | 生产环境必须 `false`，否则 API 文档公开暴露            |
| `DEBUG`          | 生产环境必须 `false`                                   |

---

## Step 4: 配置域名和 HTTPS

### 4.1 DNS 解析

在域名服务商控制台添加 A 记录：

| 记录类型 | 主机记录 | 记录值          | TTL |
| -------- | -------- | --------------- | --- |
| A        | @        | <服务器公网 IP> | 600 |
| A        | www      | <服务器公网 IP> | 600 |

等待 DNS 生效（通常几分钟到几小时）：

```bash
# 验证 DNS 是否生效（替换为你的域名）
ping fablab.example.com
```

### 4.2 申请 SSL 证书

使用 Let's Encrypt 免费证书 + acme.sh 自动续期：

```bash
# 安装 acme.sh
curl https://get.acme.sh | sh
source ~/.bashrc

# 申请证书（替换为你的域名）
# 需要先启动一个临时 nginx
cd /opt/fablab

# 创建证书目录
mkdir -p /opt/fablab/certbot-webroot

# 修改 nginx 使用 HTTP 配置先启动（用于证书验证）
# 临时启动 nginx
docker compose up -d nginx

# 申请证书
~/.acme.sh/acme.sh --issue -d fablab.example.com --webroot /opt/fablab/certbot-webroot

# 安装证书到项目目录
mkdir -p /opt/fablab/ssl
~/.acme.sh/acme.sh --install-cert -d fablab.example.com \
  --key-file /opt/fablab/ssl/key.pem \
  --fullchain-file /opt/fablab/ssl/cert.pem \
  --reloadcmd "cd /opt/fablab && docker compose restart nginx"
```

acme.sh 会自动设置定时任务续期证书。

### 4.3 切换到 HTTPS 配置

```bash
cd /opt/fablab

# 停止当前服务
docker compose down

# 备份 HTTP 配置，启用 SSL 配置
cp nginx.conf nginx-http.conf.bak
cp nginx-ssl.conf nginx.conf
```

编辑 `nginx.conf`，把所有 `server_name _;` 替换为你的域名：

```bash
# 替换域名为你的实际域名
sed -i 's/server_name _;/server_name fablab.example.com;/g' nginx.conf
```

编辑 `docker-compose.yml`，让 nginx 挂载 SSL 证书并暴露 443 端口：

```bash
nano docker-compose.yml
```

找到 `nginx` 服务，修改为：

```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/letsencrypt/live/fablab.example.com:ro
      - ./certbot-webroot:/var/www/certbot:ro
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_started
    restart: unless-stopped
```

同时修改 `env_file` 指向你的 .env 文件：

```bash
# 确保 docker-compose.yml 中 backend 服务的 env_file 指向正确的文件
# 如果 docker-compose.yml 中是 env_file: - .env
# 确保 .env 文件在项目根目录
cp .env.production .env
```

---

## Step 5: 构建和启动

### 5.1 构建镜像

```bash
cd /opt/fablab
docker compose build
```

首次构建需要 5-10 分钟（下载依赖 + 编译前端）。

### 5.2 启动所有服务

```bash
docker compose up -d
```

### 5.3 检查服务状态

```bash
docker compose ps
```

所有服务应该显示 `Up` 和 `healthy`：

```
NAME         STATUS
backend      Up (healthy)
db           Up (healthy)
frontend     Up
nginx        Up
redis        Up (healthy)
```

### 5.4 查看日志（如果有问题）

```bash
# 查看所有服务日志
docker compose logs

# 只看后端日志
docker compose logs backend

# 实时跟踪日志
docker compose logs -f backend
```

---

## Step 6: 验证部署

### 6.1 浏览器验证

打开 `https://fablab.example.com`（替换为你的域名）：

1. 应该看到登录页面
2. 用 `admin` / `<你在 .env 中设置的 ADMIN_PASSWORD>` 登录
3. 登录后应该能看到侧边栏和数据看板
4. 测试各个页面：用户管理、校区管理、角色管理等

### 6.2 安全验证清单

| 验证项         | 方法                            | 预期结果                                       |
| -------------- | ------------------------------- | ---------------------------------------------- |
| HTTPS 正常     | 浏览器访问 `https://...`      | 地址栏显示锁图标                               |
| HTTP 跳转      | 浏览器访问 `http://...`       | 自动跳转到 HTTPS                               |
| API 文档已隐藏 | 浏览器访问 `https://.../docs` | 返回 404                                       |
| Cookie 安全    | F12 → Application → Cookies   | token 标记为 HttpOnly, Secure, SameSite=Strict |
| 密码加密       | 无法直接验证                    | 已用 PBKDF2 480000 次                          |

### 6.3 创建正式用户

通过 admin 账户登录后：

1. 创建真实用户（需通过 API 或数据库）
2. 分配角色和权限
3. **用完即删除测试用户** `teacher1` 和 `orgadmin1`

---

## Step 7: 微信扫码登录配置

> 这一步需要域名和 HTTPS 已经配置好。

### 7.1 注册微信开放平台

1. 访问 [微信开放平台](https://open.weixin.qq.com/)
2. 注册账号并完成开发者资质认证（需要企业营业执照）
3. 创建「网站应用」：
   - 填写网站名称、简介、图标
   - **授权回调域**填写你的域名，如 `fablab.example.com`（不带 https:// 和路径）
4. 提交审核（通常 1-3 个工作日）
5. 审核通过后，在应用详情页获取 **AppID** 和 **AppSecret**

### 7.2 配置 .env

```bash
nano /opt/fablab/.env
```

填入微信配置：

```env
WECHAT_APP_ID=wx1234567890abcdef
WECHAT_APP_SECRET=your_app_secret_here
WECHAT_REDIRECT_URI=https://fablab.example.com/api/v1/auth/callback
```

### 7.3 重启后端生效

```bash
cd /opt/fablab
docker compose restart backend
```

### 7.4 测试扫码登录

1. 浏览器打开登录页面
2. 点击「微信扫码登录」
3. 应该显示二维码
4. 用微信扫码测试

---

## Step 8: 日常运维

### 8.1 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend    # 后端实时日志
docker compose logs -f nginx      # nginx 访问日志
docker compose logs --since 1h    # 最近 1 小时日志

# 重启单个服务
docker compose restart backend

# 重新构建并启动（代码更新后）
docker compose up -d --build
```

### 8.2 数据库备份

```bash
# 创建备份目录
mkdir -p /opt/fablab/backups

# 手动备份
docker compose exec db pg_dump -U fablab fablab > /opt/fablab/backups/fablab_$(date +%Y%m%d).sql

# 设置每天自动备份（凌晨 3 点）
echo "0 3 * * * docker compose -f /opt/fablab/docker-compose.yml exec -T db pg_dump -U fablab fablab > /opt/fablab/backups/fablab_\$(date +\%Y\%m\%d).sql" | crontab -
```

### 8.3 更新部署

```bash
cd /opt/fablab

# 拉取最新代码
git pull origin master

# 重新构建并启动
docker compose up -d --build

# 检查服务状态
docker compose ps
```

### 8.4 常见问题排查

| 问题            | 排查方法                                                |
| --------------- | ------------------------------------------------------- |
| 页面打不开      | `docker compose ps` 检查服务是否都在运行              |
| 登录失败        | `docker compose logs backend` 看后端日志              |
| 502 Bad Gateway | 后端未启动或崩溃，`docker compose logs backend` 排查  |
| 证书过期        | `~/.acme.sh/acme.sh --renew -d fablab.example.com`    |
| 数据库连接失败  | 检查 `.env` 中 `DATABASE_URL` 的主机名是否为 `db` |
| Redis 连接失败  | 检查 `.env` 中 `REDIS_URL` 的主机名是否为 `redis` |

---

## 附录 A: 服务器最低配置

| 组件 | 最低要求         | 推荐             |
| ---- | ---------------- | ---------------- |
| CPU  | 1 核             | 2 核             |
| 内存 | 1 GB             | 2 GB+            |
| 磁盘 | 20 GB            | 40 GB+ SSD       |
| 系统 | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

---

## 附录 B: 文件结构说明

部署后的关键文件：

```
/opt/fablab/
├── .env                    # 所有配置（敏感！不要泄露）
├── docker-compose.yml      # Docker 服务编排
├── Dockerfile              # 后端构建
├── Dockerfile.admin-web    # 前端构建
├── nginx.conf              # Nginx 配置（HTTPS）
├── nginx-ssl.conf          # HTTPS 模板
├── nginx-http.conf.bak     # HTTP 配置备份
├── ssl/                    # SSL 证书
│   ├── cert.pem
│   └── key.pem
├── certbot-webroot/        # 证书验证目录
├── backups/                # 数据库备份
├── 后端/                    # Python 后端代码
├── admin-web/              # Vue 前端代码
└── sdk/                    # Python SDK
```

---

## 附录 C: 完整的 docker-compose.yml 生产配置参考

```yaml
name: fablab-platform

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.admin-web
    volumes:
      - ./nginx-frontend.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-fablab}
      POSTGRES_USER: ${DB_USER:-fablab}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-fablab}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/letsencrypt/live/<你的域名>:ro
      - ./certbot-webroot:/var/www/certbot:ro
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_started
    restart: unless-stopped

volumes:
  pgdata:
  redisdata:
```

> 注意：把 `<你的域名>` 替换为实际域名。

# 方案 B：本地笔记本 + Cloudflare Tunnel

> **推荐新手先用这个方案**。不需要云服务器、不需要备案、不需要手动配置 SSL。
> 一台旧笔记本 + 免费域名 + Cloudflare 免费账号 = 完整的生产环境。

## 原理

```
用户浏览器 → Cloudflare CDN（自动 HTTPS）→ Cloudflare Tunnel → 你的笔记本（Docker）
```

Cloudflare 免费提供 HTTPS 证书和 CDN 加速，你的笔记本不需要公网 IP。

---

## B1: 准备笔记本

### 硬件要求

| 项目 | 最低要求                                    |
| ---- | ------------------------------------------- |
| 系统 | Ubuntu 22.04 LTS（推荐）或 Ubuntu 24.04 LTS |
| CPU  | 2 核（大多数笔记本都满足）                  |
| 内存 | 2 GB+                                       |
| 磁盘 | 20 GB+ 可用空间                             |
| 网络 | 能上网即可（不需要公网 IP）                 |

### 安装 Ubuntu 系统

如果你的笔记本当前是 Windows：

1. **方案一：双系统（推荐）**

   - 下载 [Ubuntu 22.04 LTS 镜像](https://ubuntu.com/download/desktop)
   - 用 [Rufus](https://rufus.ie/) 制作 USB 启动盘
   - 重启从 USB 启动，选择「安装 Ubuntu alongside Windows」
   - 安装时选择「最小安装」即可
2. **方案二：全盘安装（旧笔记本推荐）**

   - 备份重要数据后，从 USB 启动选择「Erase disk and install Ubuntu」
   - 安装完成后系统更干净、更稳定
3. **方案三：WSL2（Windows 内置 Linux，最简单但有局限）**

   - Windows 搜索「Turn Windows features on or off」→ 勾选「Windows Subsystem for Linux」
   - 重启后 `wsl --install -d Ubuntu-22.04`
   - Docker 也能跑，但性能和稳定性不如原生 Linux

### 安装后基础配置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl git nano

# 设置时区
sudo timedatectl set-timezone Asia/Shanghai
```

---

## B2: 安装 Docker

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | sudo sh

# 把当前用户加入 docker 组（这样不用每次 sudo）
sudo usermod -aG docker $USER

# 重新登录让权限生效（重要！）
exit
# 重新 SSH 或重新打开终端

# 验证
docker --version
docker compose version
```

---

## B3: 注册 Cloudflare 和域名

### 3.1 注册 Cloudflare

1. 访问 [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. 用邮箱注册（免费账号即可）

### 3.2 购买域名

> 推荐在 Cloudflare 直接买域名，价格透明无加价。

1. 登录 Cloudflare 控制台
2. 左侧菜单 → **Domain Registration** → **Register Domains**
3. 搜索你想要的域名（如 `fablab.online`、`fablab.club`）
4. `.online` / `.club` / `.site` 域名通常首年 ¥10-30

> **为什么不用国内域名？** 国内域名需要备案，而家庭宽带无法备案。Cloudflare 注册的境外域名无需备案。

### 3.3 添加站点

1. Cloudflare 控制台 → **Add a site**
2. 输入你购买的域名
3. 选择 **Free 计划**
4. Cloudflare 会给你两个 NS（域名服务器）地址
5. 按提示去域名管理页面修改 NS 记录
6. 等待生效（通常几分钟，最长 24 小时）

---

## B4: 获取代码并配置

### 4.1 克隆代码

```bash
mkdir -p ~/fablab
cd ~/fablab
git clone https://github.com/YuShuangyuanFABLAB/FabLabOnline.git .
```

### 4.2 生成密钥并配置 .env

```bash
# 生成随机密钥（记下来！）
echo "数据库密码: $(openssl rand -base64 24)"
echo "JWT 密钥: $(openssl rand -hex 32)"
echo "管理员密码: $(openssl rand -base64 16)"
```

```bash
nano .env
```

填入：

```env
# 数据库
DB_NAME=fablab
DB_USER=fablab
DB_PASSWORD=<生成的数据库密码>
DATABASE_URL=postgresql+asyncpg://fablab:<数据库密码>@db:5432/fablab
REDIS_URL=redis://redis:6379/0

# 安全
JWT_SECRET_KEY=<生成的 JWT 密钥>
ADMIN_PASSWORD=<生成的管理员密码>

# CORS — 填你的域名
CORS_ORIGINS=https://fablab.example.com

# 生产环境关闭 API 文档
DOCS_ENABLED=false

# 微信 OAuth（暂时留空）
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=

# 其他
APP_VERSION=1.0.0
DEBUG=false
```

---

## B5: 构建并启动 Docker

```bash
cd ~/fablab
docker compose build
docker compose up -d
```

检查状态：

```bash
docker compose ps
```

全部 `Up` 和 `healthy` 即可。此时服务运行在笔记本的 `localhost:8080`。

---

## B6: 配置 Cloudflare Tunnel

这一步让外部用户通过域名访问你的笔记本。

### 6.1 安装 cloudflared

```bash
# Ubuntu/Debian
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
```

### 6.2 登录 Cloudflare

```bash
cloudflared tunnel login
```

会弹出一个浏览器链接，点击授权。授权后会下载一个证书文件。

### 6.3 创建隧道

```bash
# 创建隧道（名字随意，如 fablab）
cloudflared tunnel create fablab

# 记下输出的 Tunnel ID（一串 UUID）
# 例如：Tunnel credentials written to /home/xxx/.cloudflared/<UUID>.json
```

### 6.4 配置 DNS

```bash
# 把域名指向隧道（替换 <Tunnel-ID> 和 <你的域名>）
cloudflared tunnel route dns fablab fablab.example.com
```

这会自动在 Cloudflare 添加一条 CNAME 记录。

### 6.5 创建隧道配置文件

```bash
nano ~/.cloudflared/config.yml
```

写入：

```yaml
tunnel: fablab
credentials-file: /home/<你的用户名>/.cloudflared/<Tunnel-ID>.json

ingress:
  - hostname: fablab.example.com
    service: http://localhost:8080
  - service: http_status:404
```

> 把 `<你的用户名>` 和 `<Tunnel-ID>` 替换为实际值。
> 最后一条 `- service: http_status:404` 是默认兜底规则，**必须保留**。

### 6.6 测试隧道

```bash
cloudflared tunnel run fablab
```

看到 `Connection ... registered` 即成功。不要关闭终端，另开一个终端测试：

```bash
# 在另一个终端
curl -I https://fablab.example.com/health
```

返回 `200 OK` 就对了。

### 6.7 设置为系统服务（后台运行 + 开机自启）

```bash
# 安装为系统服务
sudo cloudflared service install

# 启动并设为开机自启
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# 检查状态
sudo systemctl status cloudflared
```

现在隧道在后台运行，笔记本重启后也会自动连接。

---

## B7: 防止笔记本休眠

**这步很关键！** 笔记本合盖会休眠，服务会中断。

```bash
# 编辑 logind 配置
sudo nano /etc/systemd/logind.conf
```

找到并修改（取消注释 + 改值）：

```ini
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
```

重启生效：

```bash
sudo systemctl restart systemd-logind
```

现在合上笔记本盖子，系统继续运行。

---

## B8: 验证部署

1. 用**手机或其他设备**（不同网络）打开 `https://fablab.example.com`
2. 应该看到登录页面
3. 用 `admin` / `<.env 中的 ADMIN_PASSWORD>` 登录
4. 浏览器地址栏应显示锁图标（Cloudflare 自动 HTTPS）

---

## B9: 微信扫码登录

与方案 A 的 Step 7 相同。配置 `.env` 中的 `WECHAT_*` 后重启后端：

```bash
cd ~/fablab
nano .env  # 填写 WECHAT_APP_ID / WECHAT_APP_SECRET / WECHAT_REDIRECT_URI
docker compose restart backend
```

---

## 方案 B 日常运维

### Docker 开机自启

```bash
sudo systemctl enable docker
```

### 常用命令

```bash
# 查看服务状态
cd ~/fablab && docker compose ps

# 查看日志
docker compose logs -f backend

# 更新代码并重新部署
cd ~/fablab && git pull origin master && docker compose up -d --build

# 数据库备份
docker compose exec db pg_dump -U fablab fablab > ~/fablab_$(date +%Y%m%d).sql
```

### 自动备份（每天凌晨 3 点）

```bash
echo "0 3 * * * cd /home/$USER/fablab && docker compose exec -T db pg_dump -U fablab fablab > /home/$USER/backups/fablab_\$(date +\%Y\%m\%d).sql" | crontab -
mkdir -p ~/backups
```

### 常见问题

| 问题                 | 解决                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| 合盖后无法访问       | 检查 `/etc/systemd/logind.conf` 中 `HandleLidSwitch=ignore`          |
| 域名访问不了         | `sudo systemctl status cloudflared` 看隧道是否在线                     |
| 服务挂了             | `docker compose ps` + `docker compose logs backend`                  |
| 电脑重启后服务没恢复 | `sudo systemctl enable docker` + `sudo systemctl enable cloudflared` |
| 想临时停服务         | `docker compose down`（数据不会丢失）                                  |
| 想恢复服务           | `docker compose up -d`                                                 |

---

# 方案 B：本地笔记本 + Cloudflare Tunnel

> **推荐新手先用这个方案**。不需要云服务器、不需要备案、不需要手动配置 SSL。
> 一台旧笔记本 + 免费域名 + Cloudflare 免费账号 = 完整的生产环境。

## 原理

```
用户浏览器 → Cloudflare CDN（自动 HTTPS）→ Cloudflare Tunnel → 你的笔记本（Docker）
```

Cloudflare 免费提供 HTTPS 证书和 CDN 加速，你的笔记本不需要公网 IP。

---

## B1: 准备笔记本

### 硬件要求

| 项目 | 最低要求                                    |
| ---- | ------------------------------------------- |
| 系统 | Ubuntu 22.04 LTS（推荐）或 Ubuntu 24.04 LTS |
| CPU  | 2 核（大多数笔记本都满足）                  |
| 内存 | 2 GB+                                       |
| 磁盘 | 20 GB+ 可用空间                             |
| 网络 | 能上网即可（不需要公网 IP）                 |

### 安装 Ubuntu 系统

如果你的笔记本当前是 Windows：

1. **方案一：双系统（推荐）**

   - 下载 [Ubuntu 22.04 LTS 镜像](https://ubuntu.com/download/desktop)
   - 用 [Rufus](https://rufus.ie/) 制作 USB 启动盘
   - 重启从 USB 启动，选择「安装 Ubuntu alongside Windows」
   - 安装时选择「最小安装」即可
2. **方案二：全盘安装（旧笔记本推荐）**

   - 备份重要数据后，从 USB 启动选择「Erase disk and install Ubuntu」
   - 安装完成后系统更干净、更稳定
3. **方案三：WSL2（Windows 内置 Linux，最简单但有局限）**

   - Windows 搜索「Turn Windows features on or off」→ 勾选「Windows Subsystem for Linux」
   - 重启后 `wsl --install -d Ubuntu-22.04`
   - Docker 也能跑，但性能和稳定性不如原生 Linux

### 安装后基础配置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl git nano

# 设置时区
sudo timedatectl set-timezone Asia/Shanghai
```

---

## B2: 安装 Docker

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | sudo sh

# 把当前用户加入 docker 组（这样不用每次 sudo）
sudo usermod -aG docker $USER

# 重新登录让权限生效（重要！）
exit
# 重新 SSH 或重新打开终端

# 验证
docker --version
docker compose version
```

---

## B3: 注册 Cloudflare 和域名

### 3.1 注册 Cloudflare

1. 访问 [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. 用邮箱注册（免费账号即可）

### 3.2 购买域名

> 推荐在 Cloudflare 直接买域名，价格透明无加价。

1. 登录 Cloudflare 控制台
2. 左侧菜单 → **Domain Registration** → **Register Domains**
3. 搜索你想要的域名（如 `fablab.online`、`fablab.club`）
4. `.online` / `.club` / `.site` 域名通常首年 ¥10-30

> **为什么不用国内域名？** 国内域名需要备案，而家庭宽带无法备案。Cloudflare 注册的境外域名无需备案。

### 3.3 添加站点

1. Cloudflare 控制台 → **Add a site**
2. 输入你购买的域名
3. 选择 **Free 计划**
4. Cloudflare 会给你两个 NS（域名服务器）地址
5. 按提示去域名管理页面修改 NS 记录
6. 等待生效（通常几分钟，最长 24 小时）

---

## B4: 获取代码并配置

### 4.1 克隆代码

```bash
mkdir -p ~/fablab
cd ~/fablab
git clone https://github.com/YuShuangyuanFABLAB/FabLabOnline.git .
```

### 4.2 生成密钥并配置 .env

```bash
# 生成随机密钥（记下来！）
echo "数据库密码: $(openssl rand -base64 24)"
echo "JWT 密钥: $(openssl rand -hex 32)"
echo "管理员密码: $(openssl rand -base64 16)"
```

```bash
nano .env
```

填入：

```env
# 数据库
DB_NAME=fablab
DB_USER=fablab
DB_PASSWORD=<生成的数据库密码>
DATABASE_URL=postgresql+asyncpg://fablab:<数据库密码>@db:5432/fablab
REDIS_URL=redis://redis:6379/0

# 安全
JWT_SECRET_KEY=<生成的 JWT 密钥>
ADMIN_PASSWORD=<生成的管理员密码>

# CORS — 填你的域名
CORS_ORIGINS=https://fablab.example.com

# 生产环境关闭 API 文档
DOCS_ENABLED=false

# 微信 OAuth（暂时留空）
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=

# 其他
APP_VERSION=1.0.0
DEBUG=false
```

---

## B5: 构建并启动 Docker

```bash
cd ~/fablab
docker compose build
docker compose up -d
```

检查状态：

```bash
docker compose ps
```

全部 `Up` 和 `healthy` 即可。此时服务运行在笔记本的 `localhost:8080`。

---

## B6: 配置 Cloudflare Tunnel

这一步让外部用户通过域名访问你的笔记本。

### 6.1 安装 cloudflared

```bash
# Ubuntu/Debian
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared
```

### 6.2 登录 Cloudflare

```bash
cloudflared tunnel login
```

会弹出一个浏览器链接，点击授权。授权后会下载一个证书文件。

### 6.3 创建隧道

```bash
# 创建隧道（名字随意，如 fablab）
cloudflared tunnel create fablab

# 记下输出的 Tunnel ID（一串 UUID）
# 例如：Tunnel credentials written to /home/xxx/.cloudflared/<UUID>.json
```

### 6.4 配置 DNS

```bash
# 把域名指向隧道（替换 <Tunnel-ID> 和 <你的域名>）
cloudflared tunnel route dns fablab fablab.example.com
```

这会自动在 Cloudflare 添加一条 CNAME 记录。

### 6.5 创建隧道配置文件

```bash
nano ~/.cloudflared/config.yml
```

写入：

```yaml
tunnel: fablab
credentials-file: /home/<你的用户名>/.cloudflared/<Tunnel-ID>.json

ingress:
  - hostname: fablab.example.com
    service: http://localhost:8080
  - service: http_status:404
```

> 把 `<你的用户名>` 和 `<Tunnel-ID>` 替换为实际值。
> 最后一条 `- service: http_status:404` 是默认兜底规则，**必须保留**。

### 6.6 测试隧道

```bash
cloudflared tunnel run fablab
```

看到 `Connection ... registered` 即成功。不要关闭终端，另开一个终端测试：

```bash
# 在另一个终端
curl -I https://fablab.example.com/health
```

返回 `200 OK` 就对了。

### 6.7 设置为系统服务（后台运行 + 开机自启）

```bash
# 安装为系统服务
sudo cloudflared service install

# 启动并设为开机自启
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# 检查状态
sudo systemctl status cloudflared
```

现在隧道在后台运行，笔记本重启后也会自动连接。

---

## B7: 防止笔记本休眠

**这步很关键！** 笔记本合盖会休眠，服务会中断。

```bash
# 编辑 logind 配置
sudo nano /etc/systemd/logind.conf
```

找到并修改（取消注释 + 改值）：

```ini
HandleLidSwitch=ignore
HandleLidSwitchDocked=ignore
```

重启生效：

```bash
sudo systemctl restart systemd-logind
```

现在合上笔记本盖子，系统继续运行。

---

## B8: 验证部署

1. 用**手机或其他设备**（不同网络）打开 `https://fablab.example.com`
2. 应该看到登录页面
3. 用 `admin` / `<.env 中的 ADMIN_PASSWORD>` 登录
4. 浏览器地址栏应显示锁图标（Cloudflare 自动 HTTPS）

---

## B9: 微信扫码登录

与方案 A 的 Step 7 相同。配置 `.env` 中的 `WECHAT_*` 后重启后端：

```bash
cd ~/fablab
nano .env  # 填写 WECHAT_APP_ID / WECHAT_APP_SECRET / WECHAT_REDIRECT_URI
docker compose restart backend
```

---

## 方案 B 日常运维

### Docker 开机自启

```bash
sudo systemctl enable docker
```

### 常用命令

```bash
# 查看服务状态
cd ~/fablab && docker compose ps

# 查看日志
docker compose logs -f backend

# 更新代码并重新部署
cd ~/fablab && git pull origin master && docker compose up -d --build

# 数据库备份
docker compose exec db pg_dump -U fablab fablab > ~/fablab_$(date +%Y%m%d).sql
```

### 自动备份（每天凌晨 3 点）

```bash
echo "0 3 * * * cd /home/$USER/fablab && docker compose exec -T db pg_dump -U fablab fablab > /home/$USER/backups/fablab_\$(date +\%Y\%m\%d).sql" | crontab -
mkdir -p ~/backups
```

### 常见问题

| 问题                 | 解决                                                                     |
| -------------------- | ------------------------------------------------------------------------ |
| 合盖后无法访问       | 检查 `/etc/systemd/logind.conf` 中 `HandleLidSwitch=ignore`          |
| 域名访问不了         | `sudo systemctl status cloudflared` 看隧道是否在线                     |
| 服务挂了             | `docker compose ps` + `docker compose logs backend`                  |
| 电脑重启后服务没恢复 | `sudo systemctl enable docker` + `sudo systemctl enable cloudflared` |
| 想临时停服务         | `docker compose down`（数据不会丢失）                                  |
| 想恢复服务           | `docker compose up -d`                                                 |

---
