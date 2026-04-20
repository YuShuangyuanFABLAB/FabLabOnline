# FabLab Online — 法贝实验室管理系统

FabLab 实验室管理平台，支持多校区、多角色权限管理和数据分析。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL |
| 前端 | Vue 3 + TypeScript + Element Plus + Vite |
| 基础设施 | Docker Compose (nginx + backend + frontend + PostgreSQL + Redis) |
| 认证 | JWT (HttpOnly Cookie) + 微信扫码登录 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/YuShuangyuanFABLAB/FabLabOnline.git
cd FabLabOnline

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置密码和密钥

# 3. 启动服务
docker compose up -d --build

# 4. 初始化数据库（首次部署）
docker compose exec backend python manage.py create-superadmin

# 5. 访问
# 前端: http://localhost
# API 文档: http://localhost/docs (开发模式)
```

## 项目结构

```
├── admin-web/          # Vue 3 前端
├── 后端/                # FastAPI 后端
│   ├── api/            # 路由和中间件
│   ├── domains/        # 业务领域（identity, access, event...）
│   ├── models/         # SQLAlchemy 模型
│   ├── infrastructure/ # 数据库、Redis 基础设施
│   └── tests/          # 测试（221 tests）
├── scripts/            # 运维脚本
│   ├── deploy.sh       # 一键部署
│   ├── backup-db.sh    # 数据库备份 + 轮转
│   ├── restore-db.sh   # 数据库恢复
│   ├── smoke-test.sh   # 冒烟测试
│   ├── setup-https.sh  # HTTPS 配置（备案后）
│   └── renew-cert.sh   # 证书续期
├── nginx.conf          # Nginx 反向代理配置
└── docker-compose.yml  # 服务编排
```

## 环境变量

见 `.env.example`，关键配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_SECRET_KEY` | JWT 签名密钥（生产必须修改） | `change-me-in-production` |
| `ADMIN_PASSWORD` | 管理员初始密码 | 空 |
| `DB_PASSWORD` | PostgreSQL 密码 | `changeme` |
| `REDIS_PASSWORD` | Redis 密码 | `changeme` |
| `DEBUG` | 开发模式 | `true` |
| `DOCS_ENABLED` | API 文档开关 | `true` |

## 角色 & 权限

| 角色 | 权限范围 |
|------|----------|
| `super_admin` | 全部功能 + 角色管理 + 系统配置 |
| `admin` | 用户管理 + 校区管理 + 数据分析 |
| `teacher` | 数据查看 + 事件上报 |

## 部署

```bash
# 一键部署（推荐）
./scripts/deploy.sh master /path/to/project

# 数据库备份
./scripts/backup-db.sh /path/to/project
```

## 测试

```bash
# 后端测试
cd 后端 && python -m pytest -v

# 前端构建验证
cd admin-web && npm run build
```

## License

Private — 法贝实验室内部使用
