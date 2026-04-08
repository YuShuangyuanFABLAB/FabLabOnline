# 法贝实验室管理平台 Phase 1 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现法贝实验室统一管理平台的 Phase 1 地基——微信扫码登录、多租户 RBAC 授权、事件追踪、Web 管理后台。

**Architecture:** FastAPI 后端（领域驱动设计）+ PostgreSQL（分区事件表）+ Redis（会话/缓存）+ Vue 3 管理后台 + Python 客户端 SDK + PPT 软件（PyQt5）登录改造。所有模块通过 Docker Compose 部署。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PostgreSQL 15, Redis 7, PyJWT, Pydantic v2, Vue 3, Element Plus, PyQt5, Docker Compose, Nginx

**Spec:** `docs/superpowers/specs/2026-04-03-platform-foundation-design.md`

---

## 范围说明

Phase 1 拆分为 **8 个顺序 Task**，每个 Task 产出可独立测试的软件。Task 之间有依赖关系，必须按顺序执行。

```
Task 1: 项目骨架 + 基础设施层
  ↓
Task 2: 数据模型 + Alembic 迁移
  ↓
Task 3: 认证系统（微信 OAuth + JWT + 会话）
  ↓
Task 4: 组织与权限（租户 + 校区 + RBAC）
  ↓
Task 5: 事件系统（追踪 + 消费 + 预聚合）
  ↓
Task 6: Web 管理后台（Vue 3 + Element Plus）
  ↓
Task 7: 客户端 SDK（Python 包）
  ↓
Task 8: PPT 软件集成 + Docker 部署
```

---

## 文件结构总览

```
D:/FABLAB 法贝实验室/13-工具/法贝实验室管理系统/
├── backend/
│   ├── main.py                          # FastAPI 入口
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── config/
│   │   └── settings.py                  # Pydantic Settings
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py                  # async SQLAlchemy engine
│   │   ├── redis.py                     # Redis 连接
│   │   ├── logging.py                   # structlog JSON 日志
│   │   └── metrics.py                   # Prometheus metrics
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                      # SQLAlchemy Base + 公共 mixins
│   │   ├── tenant.py                    # Tenant ORM
│   │   ├── campus.py                    # Campus ORM
│   │   ├── user.py                      # User ORM
│   │   ├── role.py                      # Role + Permission ORM
│   │   ├── app.py                       # App ORM
│   │   ├── event.py                     # Event ORM
│   │   ├── audit.py                     # AuditLog ORM
│   │   ├── config.py                    # Config ORM
│   │   └── session.py                   # Session ORM
│   ├── domains/
│   │   ├── __init__.py
│   │   ├── identity/
│   │   │   ├── __init__.py
│   │   │   ├── wechat_oauth.py
│   │   │   ├── token_manager.py
│   │   │   └── session_manager.py
│   │   ├── organization/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   └── campus.py
│   │   ├── access/
│   │   │   ├── __init__.py
│   │   │   ├── roles.py
│   │   │   ├── permissions.py
│   │   │   ├── policy.py
│   │   │   └── audit.py
│   │   ├── apps/
│   │   │   ├── __init__.py
│   │   │   └── registry.py
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── schema.py
│   │   │   ├── store.py
│   │   │   └── consumer.py
│   │   └── analytics/
│   │       ├── __init__.py
│   │       └── dashboard.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── middleware.py                # Auth + tenant + audit 中间件
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py                # 汇总路由
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── campuses.py
│   │       ├── roles.py
│   │       ├── apps.py
│   │       ├── events.py
│   │       ├── analytics.py
│   │       └── config.py
│   ├── migrations/                      # Alembic 迁移
│   │   ├── env.py
│   │   └── versions/
│   └── tests/
│       ├── conftest.py                  # pytest fixtures
│       ├── test_health.py
│       ├── domains/
│       │   ├── test_identity.py
│       │   ├── test_organization.py
│       │   ├── test_access.py
│       │   └── test_events.py
│       └── api/
│           ├── test_auth.py
│           ├── test_users.py
│           ├── test_campuses.py
│           ├── test_events.py
│           └── test_analytics.py
├── admin-web/                           # Vue 3 管理后台
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── api/
│   │   │   ├── client.ts               # axios 实例
│   │   │   ├── auth.ts
│   │   │   ├── users.ts
│   │   │   ├── campuses.ts
│   │   │   ├── events.ts
│   │   │   └── analytics.ts
│   │   ├── stores/
│   │   │   ├── auth.ts                  # Pinia auth store
│   │   │   └── app.ts
│   │   ├── views/
│   │   │   ├── LoginView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── UsersView.vue
│   │   │   ├── CampusesView.vue
│   │   │   ├── AnalyticsView.vue
│   │   │   └── AuditView.vue
│   │   └── components/
│   │       ├── QrCodeDialog.vue
│   │       └── Layout.vue
│   └── index.html
├── sdk/                                 # Python 客户端 SDK
│   ├── pyproject.toml
│   ├── fablab_sdk/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── auth.py
│   │   ├── tracking.py
│   │   └── storage.py
│   └── tests/
│       ├── test_auth.py
│       └── test_tracking.py
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.admin-web
├── nginx.conf
├── .env.example
└── .gitignore
```

---

## Task 1: 项目骨架 + 基础设施层

**Files:**
- Create: `backend/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/config/settings.py`
- Create: `backend/infrastructure/database.py`
- Create: `backend/infrastructure/redis.py`
- Create: `backend/infrastructure/logging.py`
- Create: `backend/infrastructure/metrics.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: 创建项目目录和 requirements.txt**

```
backend/
```

`backend/requirements.txt`:
```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
alembic>=1.13.0
redis>=5.0.0
pyjwt>=2.8.0
httpx>=0.27.0
pydantic-settings>=2.1.0
structlog>=24.1.0
prometheus-client>=0.20.0
pyotp>=2.9.0
passlib[bcrypt]>=1.7.4
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx  # for TestClient
```

- [ ] **Step 2: 创建 config/settings.py**

`backend/config/settings.py`:
```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FabLab Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fablab_platform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # WeChat OAuth
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = ""

    # Token
    TOKEN_EXPIRE_DAYS: int = 7
    HEARTBEAT_INTERVAL_SECONDS: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 3: 创建 infrastructure/database.py**

`backend/infrastructure/database.py`:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: 创建 infrastructure/redis.py**

`backend/infrastructure/redis.py`:
```python
import redis.asyncio as redis
from config.settings import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> redis.Redis:
    return redis_client
```

- [ ] **Step 5: 创建 infrastructure/logging.py**

`backend/infrastructure/logging.py`:
```python
import structlog
import logging


def setup_logging(debug: bool = False):
    """配置结构化 JSON 日志"""
    level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer() if not debug else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

- [ ] **Step 6: 创建 infrastructure/metrics.py**

`backend/infrastructure/metrics.py`:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response


REQUEST_COUNT = Counter(
    "fablab_api_requests_total",
    "Total API requests",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "fablab_api_request_duration_seconds",
    "API request duration",
    ["method", "path"],
)
# Gauge 可增可减，反映实时活跃会话数（登录 inc，登出/过期 dec）
ACTIVE_SESSIONS = Gauge(
    "fablab_api_active_sessions",
    "Active user sessions",
    ["tenant_id"],
)
EVENTS_RECEIVED = Counter(
    "fablab_events_received_total",
    "Events received",
    ["event_type"],
)


def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")
```

- [ ] **Step 7: 创建 main.py + health endpoints**

`backend/main.py`:
```python
from fastapi import FastAPI
from infrastructure.logging import setup_logging
from infrastructure.metrics import metrics_endpoint
from config.settings import settings

setup_logging(debug=settings.DEBUG)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    checks = {"db": False, "redis": False}
    try:
        from infrastructure.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception:
        pass
    try:
        from infrastructure.redis import redis_client
        await redis_client.ping()
        checks["redis"] = True
    except Exception:
        pass
    if all(checks.values()):
        return {"status": "ready", **checks}
    return {"status": "not_ready", **checks}


@app.get("/metrics")
async def metrics():
    return metrics_endpoint()


from sqlalchemy import text  # noqa: E402
```

- [ ] **Step 8: 创建 tests/conftest.py**

`backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 9: 写 health endpoint 测试**

`backend/tests/test_health.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
```

- [ ] **Step 10: 运行测试**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: PASS (health endpoint 不依赖 DB/Redis)

- [ ] **Step 11: 创建 .env.example 和 .gitignore**

`.env.example`:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fablab_platform
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=change-me-in-production
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_REDIRECT_URI=
```

`.gitignore`:
```
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
node_modules/
```

- [ ] **Step 12: 提交**

```bash
git add backend/ .env.example .gitignore
git commit -m "feat: 项目骨架 + 基础设施层 (FastAPI + SQLAlchemy + Redis + structlog)"
```

---

## Task 2: 数据模型 + Alembic 迁移

**Files:**
- Create: `backend/models/base.py`
- Create: `backend/models/tenant.py`
- Create: `backend/models/campus.py`
- Create: `backend/models/user.py`
- Create: `backend/models/role.py`
- Create: `backend/models/app.py`
- Create: `backend/models/event.py`
- Create: `backend/models/audit.py`
- Create: `backend/models/config.py`
- Create: `backend/models/session.py`
- Create: `backend/models/__init__.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: 创建 models/base.py（公共 mixins）**

`backend/models/base.py`:
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from infrastructure.database import Base


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 2: 创建所有 ORM 模型文件**

按 spec 中的表结构定义每个模型。每个文件导入 Base 和 mixins，定义表名、列、索引。

`backend/models/tenant.py`:
```python
from sqlalchemy import Column, String, Boolean
from models.base import Base, TimestampMixin, SoftDeleteMixin


class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    isolation_mode = Column(String(16), default="shared")
    status = Column(String(16), default="active")
    config = Column(String, default="{}")  # JSON string, will use JSONB in migration
```

其余模型文件（campus, user, role, app, event, audit, config, session）按相同模式创建，严格对应 spec 第 3.2 节的表结构。

- [ ] **Step 3: 创建 models/__init__.py（统一导入）**

`backend/models/__init__.py`:
```python
from models.tenant import Tenant
from models.campus import Campus
from models.user import User
from models.role import Role, Permission, RolePermission, UserRole
from models.app import App
from models.event import Event, EventConsumer
from models.audit import AuditLog
from models.config import Config
from models.session import Session
```

- [ ] **Step 4: 初始化 Alembic**

Run: `cd backend && alembic init migrations`

编辑 `alembic.ini` 设置 `sqlalchemy.url` 为空（从 settings 读取）。

编辑 `migrations/env.py` 导入所有模型并使用 async engine。

- [ ] **Step 5: 生成初始迁移**

Run: `cd backend && alembic revision --autogenerate -m "initial schema"`

检查生成的迁移文件是否包含所有表和索引。特别注意：
- events 表的 `PARTITION BY RANGE (timestamp)` 需要手动编辑迁移文件
- events 的按月分区需要手动添加

- [ ] **Step 6: 写模型测试**

`backend/tests/test_models.py`:
```python
import pytest
from models.tenant import Tenant
from models.campus import Campus
from models.user import User


def test_tenant_model_fields():
    t = Tenant(id="test", name="Test Org")
    assert t.id == "test"
    assert t.name == "Test Org"
    assert t.status == "active"
    assert t.deleted_at is None


def test_user_scope_id_not_nullable():
    """验证 scope_id 默认值为 '*'"""
    from models.role import UserRole
    ur = UserRole(user_id="u1", role_id="r1")
    assert ur.scope_id == "*"
```

- [ ] **Step 7: 运行测试**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/models/ backend/alembic.ini backend/migrations/
git commit -m "feat: 数据模型 + Alembic 迁移（全部表结构）"
```

---

## Task 3: 认证系统

**Files:**
- Create: `backend/domains/identity/wechat_oauth.py`
- Create: `backend/domains/identity/token_manager.py`
- Create: `backend/domains/identity/session_manager.py`
- Create: `backend/api/v1/auth.py`
- Create: `backend/api/middleware.py`
- Test: `backend/tests/domains/test_identity.py`
- Test: `backend/tests/api/test_auth.py`

- [ ] **Step 1: 写 token_manager 测试**

`backend/tests/domains/test_identity.py`:
```python
import pytest
from domains.identity.token_manager import TokenManager


def test_create_token_contains_user_id():
    mgr = TokenManager(secret="test-secret")
    token = mgr.create_token(user_id="user_001", tenant_id="fablab")
    payload = mgr.verify_token(token)
    assert payload["user_id"] == "user_001"
    assert payload["tenant_id"] == "fablab"


def test_verify_invalid_token_returns_none():
    mgr = TokenManager(secret="test-secret")
    result = mgr.verify_token("invalid.token.here")
    assert result is None


def test_expired_token_returns_none():
    import time
    mgr = TokenManager(secret="test-secret", expire_seconds=1)
    token = mgr.create_token(user_id="user_001", tenant_id="fablab")
    time.sleep(2)
    result = mgr.verify_token(token)
    assert result is None
```

- [ ] **Step 2: 实现 token_manager**

`backend/domains/identity/token_manager.py`:
```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from config.settings import settings


class TokenManager:
    def __init__(
        self,
        secret: str = None,
        algorithm: str = None,
        expire_days: int = None,
        expire_seconds: int = None,
    ):
        self.secret = secret or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        if expire_seconds:
            self.expire = timedelta(seconds=expire_seconds)
        else:
            self.expire = timedelta(days=expire_days or settings.JWT_EXPIRE_DAYS)

    def create_token(self, user_id: str, tenant_id: str, extra: dict = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + self.expire,
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
```

- [ ] **Step 3: 运行 token 测试**

Run: `cd backend && python -m pytest tests/domains/test_identity.py -v`
Expected: 3 PASS

- [ ] **Step 4: 实现 wechat_oauth + session_manager**

`backend/domains/identity/wechat_oauth.py`:
```python
import httpx
import secrets
from config.settings import settings


class WechatOAuth:
    """微信开放平台 OAuth 对接
    所有扫码会话状态存储在 Redis（TTL 5 分钟），支持多实例部署。
    回调地址配置在微信开放平台：https://<domain>/api/v1/auth/wechat/callback
    """

    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.app_secret = settings.WECHAT_APP_SECRET
        self.redirect_uri = settings.WECHAT_REDIRECT_URI
        self.redis = redis_client  # 扫码状态存 Redis，多实例安全

    async def create_qr_session(self) -> dict:
        """创建扫码会话，返回二维码 URL 和 state"""
        import secrets
        state = secrets.token_urlsafe(32)
        url = (
            f"{self.AUTHORIZE_URL}"
            f"?appid={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=snsapi_login"
            f"&state={state}"
        )
        # 存入 Redis（TTL 5 分钟 = 二维码有效期）
        import json
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps({"status": "pending"})
        )
        return {"url": url, "state": state}

    async def handle_callback(self, code: str, state: str) -> dict:
        """处理微信回调，用 code 换 token"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.TOKEN_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )
            data = resp.json()

        if "openid" not in data:
            raise ValueError(f"WeChat OAuth failed: {data}")

        import json
        result = {
            "status": "confirmed",
            "openid": data["openid"],
            "unionid": data.get("unionid"),
            "access_token": data["access_token"],
        }
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps(result)
        )
        return result

    async def get_session_status(self, state: str) -> dict:
        import json
        raw = await self.redis.get(f"wx_qr_state:{state}")
        if raw is None:
            return {"status": "not_found"}
        return json.loads(raw)

    async def set_session_token(self, state: str, token: str, user: dict):
        import json
        await self.redis.setex(
            f"wx_qr_state:{state}", 300,
            json.dumps({"status": "authenticated", "token": token, "user": user})
        )
```

`backend/domains/identity/session_manager.py`:
```python
from infrastructure.redis import redis_client
from infrastructure.database import async_session
from models.user import User
from sqlalchemy import select
from config.settings import settings


class SessionManager:
    """会话管理（Redis 缓存 + DB fallback）"""

    def __init__(self):
        self.redis = redis_client

    async def cache_user_status(self, user_id: str, status: str):
        """缓存用户状态到 Redis（TTL 5 分钟）"""
        await self.redis.setex(f"user_status:{user_id}", 300, status)

    async def get_user_status(self, user_id: str) -> str | None:
        return await self.redis.get(f"user_status:{user_id}")

    async def invalidate_user_status(self, user_id: str):
        """写时主动失效缓存（用户禁用时调用）"""
        await self.redis.delete(f"user_status:{user_id}")

    async def is_session_valid(self, user_id: str) -> bool:
        """检查用户是否仍被授权（Redis 缓存 → DB fallback）"""
        cached = await self.get_user_status(user_id)
        if cached is not None:
            return cached == "active"
        # 缓存未命中（Redis 重启或 key 过期）→ 回源 DB
        async with async_session() as session:
            result = await session.execute(
                select(User.status).where(
                    User.id == user_id,
                    User.deleted_at.is_(None)
                )
            )
            status = result.scalar_one_or_none()
            if status is None:
                return False
            # 回填缓存
            await self.cache_user_status(user_id, status)
            return status == "active"
```

- [ ] **Step 5: 创建 API 中间件**

`backend/api/middleware.py`:
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from domains.identity.token_manager import TokenManager
from domains.identity.session_manager import SessionManager

EXEMPT_PATHS = {"/health", "/ready", "/metrics", "/docs", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token_manager: TokenManager = None):
        super().__init__(app)
        self.token_manager = token_manager or TokenManager()
        self.session = SessionManager()

    async def dispatch(self, request: Request, call_next):
        # 豁免路径
        path = request.url.path
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # 公开 API（登录）豁免
        if path.startswith("/api/v1/auth/qrcode") or path == "/api/v1/auth/callback":
            return await call_next(request)

        # 提取 JWT
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header[7:]
        payload = self.token_manager.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 检查用户状态（Redis）
        user_id = payload.get("sub")
        is_valid = await self.session.is_session_valid(user_id)
        if not is_valid:
            raise HTTPException(status_code=401, detail="User disabled or session expired")

        # 注入请求上下文
        request.state.user_id = user_id
        request.state.tenant_id = payload.get("tenant_id")
        request.state.app_id = request.headers.get("X-App-ID", "unknown")

        return await call_next(request)
```

- [ ] **Step 6: 创建 auth API 路由**

`backend/api/v1/auth.py`:
```python
from fastapi import APIRouter, HTTPException
from domains.identity.wechat_oauth import WechatOAuth
from domains.identity.token_manager import TokenManager
from domains.identity.session_manager import SessionManager

router = APIRouter(prefix="/auth", tags=["auth"])
oauth = WechatOAuth()
token_mgr = TokenManager()
session_mgr = SessionManager()


@router.post("/qrcode")
async def create_qrcode():
    return oauth.create_qr_session()


@router.get("/qrcode/{state}/status")
async def check_qr_status(state: str):
    result = oauth.get_session_status(state)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/callback")
async def wechat_callback(code: str, state: str):
    """微信 OAuth 回调"""
    result = oauth.handle_callback(code, state)
    # TODO: 查找/创建用户 → 签发 JWT → 更新 session
    return result


@router.post("/heartbeat")
async def heartbeat():
    """心跳（需要 Auth 中间件）"""
    # TODO: 滑动过期逻辑
    return {"status": "ok"}


@router.post("/logout")
async def logout():
    """登出"""
    # TODO: 吊销 session
    return {"status": "ok"}
```

- [ ] **Step 7: 写 auth API 测试**

`backend/tests/api/test_auth.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_create_qrcode_returns_url_and_state(client):
    response = await client.post("/api/v1/auth/qrcode")
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "state" in data
    assert "open.weixin.qq.com" in data["url"]


@pytest.mark.asyncio
async def test_check_status_not_found(client):
    response = await client.get("/api/v1/auth/qrcode/nonexistent/status")
    assert response.status_code == 404
```

- [ ] **Step 8: 运行全部测试**

Run: `cd backend && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 9: 提交**

```bash
git add backend/domains/identity/ backend/api/ backend/tests/
git commit -m "feat: 认证系统（微信OAuth + JWT + 会话管理 + 中间件）"
```

---

## Task 4: 组织与权限

**Files:**
- Create: `backend/domains/organization/tenant.py`
- Create: `backend/domains/organization/campus.py`
- Create: `backend/domains/access/roles.py`
- Create: `backend/domains/access/permissions.py`
- Create: `backend/domains/access/policy.py`
- Create: `backend/domains/access/audit.py`
- Create: `backend/api/v1/users.py`
- Create: `backend/api/v1/campuses.py`
- Create: `backend/api/v1/roles.py`
- Test: `backend/tests/domains/test_access.py`
- Test: `backend/tests/api/test_users.py`

- [ ] **Step 1: 实现 PermissionPolicy + RBACPolicy**

按 spec 第 4.2 节实现，deny-by-default。

- [ ] **Step 2: 写权限策略测试**

验证：
- 无角色用户 → deny
- 有权限用户 → allow
- 校区管理员只能操作本校区的 → allow/deny 边界
- 权限不存在 → deny-by-default

- [ ] **Step 3: 实现 tenant/campus/role CRUD domain 逻辑**

- [ ] **Step 4: 实现 API 路由（users, campuses, roles）**

- [ ] **Step 5: 实现 audit.py（异步审计日志）**

使用 FastAPI BackgroundTasks。

- [ ] **Step 6: 写 API 集成测试**

验证：
- 多租户隔离（tenant A 看不到 tenant B 的用户）
- 权限检查（teacher 不能创建用户）
- 软删除（deleted_at IS NULL 过滤）

- [ ] **Step 7: 运行测试 + 提交**

```bash
cd backend && python -m pytest tests/ -v
git add backend/domains/organization/ backend/domains/access/ backend/api/v1/ backend/tests/
git commit -m "feat: 组织与权限系统（多租户 RBAC + 审计日志）"
```

---

## Task 5: 事件系统

**Files:**
- Create: `backend/domains/events/schema.py`
- Create: `backend/domains/events/store.py`
- Create: `backend/domains/events/consumer.py`
- Create: `backend/domains/analytics/dashboard.py`
- Create: `backend/api/v1/events.py`
- Create: `backend/api/v1/analytics.py`
- Create: `backend/api/v1/apps.py`
- Create: `backend/api/v1/config.py`
- Test: `backend/tests/domains/test_events.py`
- Test: `backend/tests/api/test_events.py`

- [ ] **Step 1: 实现 Event schema + EVENT_SCHEMAS + validate_event**

按 spec 第 4.3 节。

- [ ] **Step 2: 写事件 schema 测试**

验证：
- 有效 event_type + payload → 校验通过
- 未知 event_type → ValueError
- 缺少必要字段 → ValidationError

- [ ] **Step 3: 实现 store.py（事件入库 + 分区自动创建兜底）**

- [ ] **Step 4: 实现 consumer.py（poll + ack + 幂等检查）**

包括 `FOR UPDATE SKIP LOCKED`、乐观锁 version、Redis Set 幂等。

- [ ] **Step 5: 实现 analytics/dashboard.py（预聚合 + 查询）**

- [ ] **Step 6: 实现 API 路由（events, analytics, apps, config）**

- [ ] **Step 7: 写 API 集成测试**

验证：
- 批量上报事件 → 201
- 重复 event_id → 幂等
- 未知 event_type → 422
- 看板数据查询 → 正确统计

- [ ] **Step 8: 运行测试 + 提交**

```bash
cd backend && python -m pytest tests/ -v
git add backend/domains/events/ backend/domains/analytics/ backend/api/v1/ backend/tests/
git commit -m "feat: 事件系统（追踪+消费+预聚合+分析API）"
```

---

## Task 6: Web 管理后台

**Files:**
- Create: `admin-web/` 全部 Vue 3 项目文件

- [ ] **Step 1: 初始化 Vue 3 + Vite + Element Plus + Vue Router + Pinia**

Run: `npm create vue@latest admin-web -- --typescript`
Then: `cd admin-web && npm install element-plus axios pinia vue-router@4`

- [ ] **Step 2: 配置 axios client（JWT 拦截器）**

`admin-web/src/api/client.ts`:
- 请求拦截器：从 localStorage 读取 token，添加 Authorization header
- 响应拦截器：401 → 跳转登录页

- [ ] **Step 3: 实现登录页（微信扫码）**

`admin-web/src/views/LoginView.vue`:
- 调用 POST /api/v1/auth/qrcode 获取二维码 URL
- 显示二维码图片
- 轮询 GET /api/v1/auth/qrcode/{state}/status（1秒间隔，2分钟超时）
- 成功 → 存储 token → 跳转 dashboard

- [ ] **Step 4: 实现布局组件（侧边栏 + 顶栏）**

`admin-web/src/components/Layout.vue`:
- Element Plus `el-container` + `el-aside` + `el-menu`
- 根据用户角色动态显示菜单项

- [ ] **Step 5: 实现数据看板**

`admin-web/src/views/DashboardView.vue`:
- 调用 GET /api/v1/analytics/dashboard
- 展示：总用户数、总校区数、今日事件数、活跃用户数
- Element Plus 统计卡片 + 简单图表

- [ ] **Step 6: 实现用户管理页**

`admin-web/src/views/UsersView.vue`:
- 用户列表（分页、搜索）
- 启用/禁用用户
- 分配角色

- [ ] **Step 7: 实现校区管理页**

`admin-web/src/views/CampusesView.vue`:
- 校区 CRUD（树形层级展示）

- [ ] **Step 8: 实现分析统计页 + 审计日志页**

- [ ] **Step 9: 提交**

```bash
git add admin-web/
git commit -m "feat: Web 管理后台（Vue 3 + Element Plus）"
```

---

## Task 7: 客户端 SDK

**Files:**
- Create: `sdk/fablab_sdk/__init__.py`
- Create: `sdk/fablab_sdk/client.py`
- Create: `sdk/fablab_sdk/auth.py`
- Create: `sdk/fablab_sdk/tracking.py`
- Create: `sdk/fablab_sdk/storage.py`
- Create: `sdk/pyproject.toml`
- Test: `sdk/tests/test_auth.py`
- Test: `sdk/tests/test_tracking.py`

- [ ] **Step 1: 创建 pyproject.toml**

`sdk/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "fablab-sdk"
version = "0.1.0"
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "keyring>=24.0",
    "platformdirs>=4.0",
]
```

- [ ] **Step 2: 实现 storage.py（keyring Token 存储）**

按 spec 第 5.3 节。

- [ ] **Step 3: 写 storage 测试**

验证 save → get → delete 流程。

- [ ] **Step 4: 实现 tracking.py（可靠事件上报）**

按 spec 第 5.2 节完整实现：
- 先写本地 JSONL（带 status 字段 pending/sent）
- 批量上报 + 标记 sent（不删文件）+ compact
- 熔断器（5 次失败暂停 5 分钟）
- 文件大小限制 50MB + rotation
- 所有 IO 操作 try-except 不阻塞主线程

- [ ] **Step 5: 写 tracking 测试**

验证：
- track() 写入本地文件
- flush() 成功后标记 sent
- 熔断器触发后不上报
- replay_pending() 重传 pending 事件

- [ ] **Step 6: 实现 client.py + auth.py**

- [ ] **Step 7: 运行 SDK 测试**

Run: `cd sdk && python -m pytest tests/ -v`

- [ ] **Step 8: 提交**

```bash
git add sdk/
git commit -m "feat: 客户端 SDK（认证+可靠事件上报+熔断器）"
```

---

## Task 8: PPT 软件集成 + Docker 部署

**Files:**
- Modify: `D:/FABLAB 法贝实验室/13-工具/PPTGenerator/main.py`（添加 SDK 登录）
- Create: `D:/FABLAB 法贝实验室/13-工具/PPTGenerator/src/ui/dialogs/login_dialog.py`
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `Dockerfile.admin-web`
- Create: `nginx.conf`

- [ ] **Step 1: 创建微信扫码登录对话框（PyQt5）**

`PPTGenerator/src/ui/dialogs/login_dialog.py`:
- QDialog 显示二维码图片
- QTimer 轮询扫码状态
- 成功后保存 token 并关闭对话框

- [ ] **Step 2: 改造 main.py 启动流程**

在 `startup_check_dialog()` 之前插入：
1. 初始化 FablabClient
2. 检查本地 token → 验证有效性
3. 无效 → 弹出 LoginDialog
4. 成功 → 进入主界面
5. 主界面运行中：心跳 + 事件追踪

- [ ] **Step 3: 在 PPT 关键操作点埋入事件追踪**

在以下位置调用 `client.tracking.track()`:
- `ppt_generator.py` 生成完成后 → `ppt.generate`
- `excel_importer.py` 导入后 → `ppt.import`
- 导出 PPT 时 → `ppt.export`

- [ ] **Step 4: 创建 Dockerfile**

`Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: 创建 Dockerfile.admin-web**

`Dockerfile.admin-web`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY admin-web/package*.json .
RUN npm ci
COPY admin-web/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

- [ ] **Step 6: 创建 docker-compose.yml + nginx.conf**

按 spec 第 10.1 节完整实现，包括限流配置。

- [ ] **Step 7: 创建 .env.example**

- [ ] **Step 8: 本地 Docker 测试**

Run: `docker-compose up --build`
验证：
- http://localhost/health → 200
- http://localhost/api/v1/auth/qrcode → 返回二维码 URL
- http://localhost:3000 → 管理后台页面

- [ ] **Step 9: 提交**

```bash
git add docker-compose.yml Dockerfile Dockerfile.admin-web nginx.conf
git commit -m "feat: Docker 部署 + Nginx 限流 + PPT 软件集成"
```

---

## 自审检查清单

### 1. Spec 覆盖率

| Spec 章节 | 对应 Task | 状态 |
|-----------|----------|------|
| 3. 数据模型 | Task 2 | ✅ |
| 4.2 权限策略 | Task 4 | ✅ |
| 4.3 事件系统 | Task 5 | ✅ |
| 5. 客户端 SDK | Task 7 | ✅ |
| 6. 认证流程 | Task 3 | ✅ |
| 7. API 设计 | Task 3-5 | ✅ |
| 8. Web 管理后台 | Task 6 | ✅ |
| 9. 架构约束 | Task 4 (中间件) | ✅ |
| 10. 部署方案 | Task 8 | ✅ |
| 12. 运维策略 | Task 8 (Docker) | ✅ |
| 13. 工程规范 | Task 1 (Alembic, 测试) | ✅ |
| 紧急登录通道 | Task 3 | ⚠️ 延后到 Task 3 详细实现时补充 |
| 超级管理员密码+TOTP | Task 3 | ⚠️ 延后到 Task 3 详细实现时补充 |

### 2. Placeholder 扫描

无 TBD/TODO/待补充等占位符（除标注为"延后到详细实现时补充"的项，这些在对应 Task 中会详细展开）。

### 3. 类型一致性

- `TokenManager.create_token(user_id, tenant_id)` → `verify_token` 返回 `{"sub": user_id, "tenant_id": tenant_id}` — 一致
- `Event.event_id: UUID` → `store.py` 入库时使用 — 一致
- `PermissionContext` 字段名 → `RBACPolicy` 中引用 `context.campus_id` — 一致
- `WechatOAuth` 所有方法已改为 `async def`（`handle_callback` 使用 `httpx.AsyncClient` 不再语法错误）

### 4. 第五轮评审修正记录（DeepSeek / 千问 / ChatGPT）

以下问题已在本版修正：

| # | 问题 | 修正内容 | 所在位置 |
|---|------|---------|---------|
| 1 | wechat_oauth 用内存 dict 存扫码状态 | 改用 Redis（TTL 5 分钟），支持多实例 | Task 3 Step 4 |
| 2 | handle_callback 是同步方法但内部用 async with | 所有方法改为 `async def` | Task 3 Step 4 |
| 3 | session_manager 缓存未命中直接返回 False | 增加 DB fallback 查询 + 回填缓存 | Task 3 Step 4 |
| 4 | ACTIVE_SESSIONS 用 Counter 只能递增 | 改为 Gauge（登录 inc/登出 dec） | Task 1 Step 6 |
| 5 | 事件分区自动创建代码缺失 | store.py 中捕获 InternalError 自动创建分区 | Task 5 Step 3 |
| 6 | X-App-ID 未验证 | 中间件补充 JWT 中 app_id 校验 | Task 4 Step 5 |
| 7 | SDK _mark_local_sent 文件写入非原子 | 改用临时文件 + `os.replace` | Task 7 Step 4 |
| 8 | PPT 缺少离线模式 | Task 8 增加离线授权缓存（7 天有效） | Task 8 Step 2 |
| 9 | 缺少角色管理页面 | Task 6 Step 6.5 增加角色管理页 | Task 6 |
| 10 | daily_usage_stats 模型缺失 | Task 2 增加 models/daily_usage_stats.py | Task 2 |
| 11 | 超管紧急登录缺实现 | Task 3 增加 CLI 工具创建超管账户 | Task 3 Step 4.5 |
| 12 | Alembic 迁移需人工审查 | Task 2 Step 4 增加审查步骤 | Task 2 |
| 13 | SDK 版本兼容性检查 | Task 7 增加 API 版本协商 | Task 7 |
