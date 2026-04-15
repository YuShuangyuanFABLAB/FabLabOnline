# 法贝实验室统一管理平台 - Phase 1 设计文档

> 版本: 1.1
> 日期: 2026-04-03
> 状态: 待审核
> 范围: Phase 1 — 平台地基（认证、授权、事件追踪、管理后台）
> 评审记录: 经 DeepSeek / 豆包 / 千问 / ChatGPT 四轮架构评审

---

## 1. 背景与目标

### 1.1 背景

法贝实验室课程反馈助手（PPT 生成软件）已完成核心功能开发，需要分发给不同校区的老师使用。面临以下挑战：

- 软件被直接拷贝导致竞品获取能力
- 无法控制谁在使用软件
- 离职老师仍可继续使用
- 缺乏使用数据洞察

### 1.2 目标

建设**法贝实验室统一管理平台**的 Phase 1（平台地基），实现：

1. 微信扫码登录 — 老师身份识别
2. 授权管理 — 多级管理员控制谁能用
3. 使用追踪 — 记录详细操作行为
4. Web 管理后台 — 可视化管理用户、校区、查看统计

### 1.3 长期愿景

该平台未来将承载：

| Phase   | 功能                                        | 预估时间    |
| ------- | ------------------------------------------- | ----------- |
| Phase 1 | 平台地基（认证+授权+追踪）                  | 当前        |
| Phase 2 | 校区运营（学员管理、排课、数据看板）        | 3-6 个月后  |
| Phase 3 | 实时监控（视频流、设备管理）                | 6-12 个月后 |
| Phase 4 | AI 智能（课程质量分析、行为分析、智慧教室） | 12 个月+    |

**规模目标**: 支撑 ≤ 1000 家校区。

### 1.4 容量模型

| 阶段         | 校区数   | 用户数     | 事件/秒 | 存储/月         |
| ------------ | -------- | ---------- | ------- | --------------- |
| Phase 1 初期 | 5-10     | 50-100     | <1      | ~10MB           |
| Phase 1 成熟 | 50-100   | 500-1000   | ~10     | ~100MB          |
| Phase 2      | 200-500  | 2000-5000  | ~100    | ~1GB            |
| Phase 3      | 500-1000 | 5000-15000 | ~1000+  | ~500GB+(含视频) |

---

## 2. 系统架构

### 2.1 整体架构

```
                    ┌─────────────────────────────────────┐
                    │          云服务器 (Docker)            │
                    │                                      │
                    │  ┌─────────────────────────────┐    │
                    │  │     Nginx (反向代理+限流)     │    │
                    │  └──────────────┬──────────────┘    │
                    │                 │                    │
                    │  ┌──────────────┴──────────────┐    │
                    │  │      FastAPI 后端服务         │    │
                    │  │  ┌──────┐ ┌──────┐ ┌──────┐  │    │
                    │  │  │identity│ │access│ │events│  │    │
                    │  │  └──────┘ └──────┘ └──────┘  │    │
                    │  │  ┌──────────┐ ┌───────────┐  │    │
                    │  │  │organization│ │analytics │  │    │
                    │  │  └──────────┘ └───────────┘  │    │
                    │  └──────────────┬──────────────┘    │
                    │                 │                    │
                    │  ┌──────┐  ┌────┴────┐              │
                    │  │Redis │  │PostgreSQL│              │
                    │  └──────┘  └─────────┘              │
                    │                                      │
                    │  ┌──────────────────────────────┐   │
                    │  │    Web 管理后台 (Vue 3)        │   │
                    │  └──────────────────────────────┘   │
                    └─────────────────────────────────────┘

老师电脑                           管理员浏览器
┌──────────┐                      ┌──────────┐
│ PPT 软件  │ ←── API (HTTPS) ──→ │ Web 后台  │
│ + SDK     │                      │ 管理界面  │
└──────────┘                      └──────────┘
```

### 2.2 技术栈

| 组件       | 选型                  | 理由                                    |
| ---------- | --------------------- | --------------------------------------- |
| 后端框架   | FastAPI (Python)      | 异步高性能，与现有 PyQt5 项目技术栈统一 |
| 数据库     | PostgreSQL 15+        | JSONB 支持好，原生分区，适合事件模型    |
| 缓存       | Redis                 | Token 管理、心跳、限流                  |
| Web 后台   | Vue 3 + Element Plus  | 中文生态好，后台组件丰富                |
| 反向代理   | Nginx                 | 反代 + HTTPS + 限流                     |
| 客户端 SDK | Python 包             | 封装认证+追踪，未来新软件引入即用       |
| 部署       | Docker Compose        | 标准化一键部署                          |
| 可观测性   | 结构化日志 + /metrics | Phase 1 最小方案                        |

### 2.3 年成本估算

| 项目                | 配置                     | 年费                  |
| ------------------- | ------------------------ | --------------------- |
| 云服务器 × 1       | 2核4G                    | ~600                  |
| 云数据库 PostgreSQL | 1核2G 基础版             | ~480                  |
| Redis               | 256MB 基础版             | ~180                  |
| 域名 (.com)         | -                        | ~60                   |
| HTTPS 证书          | 免费证书 (Let's Encrypt) | 0                     |
| 微信开放平台认证    | -                        | 300                   |
| **合计**      |                          | **~1620 元/年** |

---

## 3. 数据模型

### 3.1 多租户体系

```
机构(Tenant) ──── 1:N ──── 校区(Campus) ──── 1:N ──── 用户(User)
                                                1:N ──── 教室(Classroom) [Phase 3]
                                                1:N ──── 设备(Device) [Phase 3]
```

**隔离策略**: Phase 1 采用**共享表模式**（所有租户共享表，通过 `tenant_id` 字段隔离）。在 `TenantConfig` 中预留 `isolation_mode` 字段，未来支持 schema 隔离或独立部署。

**强制隔离机制**: 应用层通过 Repository 基类自动注入 `tenant_id` 条件。Code Review 时强制检查。Phase 2 可选升级为 PostgreSQL RLS（行级安全策略）。

### 3.2 核心表结构

#### tenants（机构表）

```sql
CREATE TABLE tenants (
    id VARCHAR(64) PRIMARY KEY,        -- 如 "fablab"
    name VARCHAR(128) NOT NULL,
    isolation_mode VARCHAR(16) DEFAULT 'shared',  -- shared / schema / dedicated
    status VARCHAR(16) DEFAULT 'active',          -- active / suspended
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ              -- 软删除
);
```

#### campuses（校区表）

```sql
CREATE TABLE campuses (
    id VARCHAR(64) PRIMARY KEY,        -- 如 "hangzhou-xihu"
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
    name VARCHAR(128) NOT NULL,
    parent_id VARCHAR(64),             -- 上级校区（总校/分校层级）
    campus_level VARCHAR(16) DEFAULT 'branch',  -- hq / branch / point
    status VARCHAR(16) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ              -- 软删除
);
CREATE INDEX idx_campuses_tenant ON campuses(tenant_id);
```

#### users（用户表）

```sql
CREATE TABLE users (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(id),
    campus_id VARCHAR(64) REFERENCES campuses(id),
    wechat_openid VARCHAR(128) UNIQUE,     -- 微信 OpenID
    wechat_unionid VARCHAR(128),            -- 微信 UnionID
    name VARCHAR(64) NOT NULL,
    phone VARCHAR(20),
    avatar_url TEXT,
    status VARCHAR(16) DEFAULT 'active',   -- active / disabled
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ              -- 软删除
);
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_campus ON users(campus_id);
CREATE INDEX idx_users_openid ON users(wechat_openid);
```

#### roles（角色表）

```sql
CREATE TABLE roles (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) REFERENCES tenants(id),  -- NULL = 系统角色
    name VARCHAR(64) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    description TEXT,
    level INTEGER NOT NULL DEFAULT 0,    -- 层级：0=系统, 1=机构, 2=校区
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**预定义角色**:

| 角色         | level | 说明                           |
| ------------ | ----- | ------------------------------ |
| super_admin  | 0     | 超级管理员，管理所有机构       |
| org_admin    | 1     | 机构管理员，管理本机构所有校区 |
| campus_admin | 2     | 校区管理员，管理本校区         |
| teacher      | 2     | 教师，使用 PPT 软件            |

#### permissions（权限表）

```sql
CREATE TABLE permissions (
    id VARCHAR(128) PRIMARY KEY,    -- 如 "user:create", "campus:read"
    resource VARCHAR(64) NOT NULL,   -- user / campus / role / app / analytics / config
    action VARCHAR(16) NOT NULL,     -- create / read / update / delete
    display_name VARCHAR(128) NOT NULL,
    description TEXT
);
```

#### role_permissions（角色-权限关联）

```sql
CREATE TABLE role_permissions (
    role_id VARCHAR(64) REFERENCES roles(id),
    permission_id VARCHAR(128) REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);
```

#### user_roles（用户-角色关联）

```sql
CREATE TABLE user_roles (
    user_id VARCHAR(64) REFERENCES users(id),
    role_id VARCHAR(64) REFERENCES roles(id),
    scope_id VARCHAR(64) NOT NULL DEFAULT '*',  -- 权限作用域（'*' = 全局，campus_id = 校区级）
    PRIMARY KEY (user_id, role_id, scope_id)
);
```

> **注意**: `scope_id` 使用 `NOT NULL DEFAULT '*'` 而非可空。PostgreSQL 中 `NULL != NULL`，
> 可空字段会导致同一 (user_id, role_id) 组合被插入多条 scope_id=NULL 的记录。

#### apps（应用注册表）

```sql
CREATE TABLE apps (
    id VARCHAR(64) PRIMARY KEY,          -- 如 "ppt-generator"
    name VARCHAR(128) NOT NULL,
    app_key VARCHAR(64) NOT NULL UNIQUE, -- API 标识
    app_secret_hash VARCHAR(128) NOT NULL,
    description TEXT,
    status VARCHAR(16) DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### events（事件表 — 按月分区）

```sql
CREATE TABLE events (
    event_seq BIGSERIAL,
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(64) NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    event_source VARCHAR(16) NOT NULL DEFAULT 'client',  -- client / system / ai
    timestamp TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    campus_id VARCHAR(64),
    user_id VARCHAR(64) NOT NULL,
    app_id VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    trace_id VARCHAR(64),
    PRIMARY KEY (event_seq)
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_events_tenant_time ON events (tenant_id, timestamp);
CREATE INDEX idx_events_type ON events (event_type);
CREATE INDEX idx_events_tenant_type_time ON events (tenant_id, event_type, timestamp);
CREATE INDEX idx_events_tenant_user_time ON events (tenant_id, user_id, timestamp DESC);  -- 用户行为轨迹查询
CREATE INDEX idx_events_user ON events (user_id);
CREATE INDEX idx_events_id ON events (event_id);
CREATE INDEX idx_events_source ON events (event_source);

-- 按月分区示例
CREATE TABLE events_2026_04 PARTITION OF events
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- ⚠️ 分区自动创建：应用启动时检查未来 3 个月的分区是否存在，不存在则自动创建
-- ⚠️ 分区创建兜底：INSERT 失败（partition not found）时自动创建当月分区并重试
-- ⚠️ 分区清理策略：每月定时删除超过 1 年的分区（DROP PARTITION）
```

#### event_consumers（事件消费进度）

```sql
CREATE TABLE event_consumers (
    consumer_name VARCHAR(64) PRIMARY KEY,
    last_event_seq BIGINT NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,   -- 乐观锁，防并发冲突
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### audit_logs（审计日志）

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant_id VARCHAR(64) NOT NULL,       -- 多租户隔离必须字段
    user_id VARCHAR(64) NOT NULL,
    user_role VARCHAR(64),
    action VARCHAR(16) NOT NULL,          -- create / read / update / delete / login / logout
    resource_type VARCHAR(64) NOT NULL,   -- user / campus / role / app / config
    resource_id VARCHAR(64),
    changes JSONB,                         -- 变更前后对比
    ip_address VARCHAR(45),
    user_agent TEXT
);
CREATE INDEX idx_audit_tenant_time ON audit_logs(tenant_id, timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_time ON audit_logs(timestamp);
```

#### configs（配置中心）

**缓存策略**:

| 操作   | 策略                                                                                                      |
| ------ | --------------------------------------------------------------------------------------------------------- |
| 读取   | Redis 缓存（key:`config:{scope}:{scope_id}:{key}`，TTL 5 分钟）→ 未命中查 DB → 写入缓存               |
| 写入   | 更新 DB → 立即 `redis.delete()` 对应 key（主动失效）→ 多实例时通过 Redis Pub/Sub 通知其他实例清除缓存 |
| 优先级 | campus > tenant > global > 代码默认值                                                                     |

```sql
CREATE TABLE configs (
    id SERIAL PRIMARY KEY,
    scope VARCHAR(16) NOT NULL,           -- global / tenant / campus
    scope_id VARCHAR(64),
    key VARCHAR(128) NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(scope, scope_id, key)
);
```

#### sessions（会话表 — Redis 为主，PostgreSQL 备份）

```sql
CREATE TABLE sessions (
    id VARCHAR(128) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL REFERENCES users(id),
    token_hash VARCHAR(128) NOT NULL,
    device_info JSONB,
    ip_address VARCHAR(45),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 4. 领域设计

### 4.1 目录结构

```
backend/
├── domains/                        # 业务领域
│   ├── identity/                   # 身份域
│   │   ├── wechat_oauth.py         # 微信 OAuth 对接
│   │   ├── token_manager.py        # Token 签发/刷新/吊销
│   │   └── session_manager.py      # 会话管理（心跳、超时）
│   │
│   ├── organization/               # 组织域
│   │   ├── tenant.py               # 租户管理
│   │   ├── campus.py               # 校区管理
│   │   └── hierarchy.py            # 层级关系
│   │
│   ├── access/                     # 权限域
│   │   ├── roles.py                # 角色管理
│   │   ├── permissions.py          # 权限定义
│   │   ├── policy.py               # 策略接口（RBAC → ABAC 可替换）
│   │   └── audit.py                # 审计日志
│   │
│   ├── apps/                       # 应用域
│   │   ├── registry.py             # 应用注册表
│   │   └── config.py               # 应用配置
│   │
│   ├── events/                     # 事件域
│   │   ├── schema.py               # 统一事件格式 + payload 校验
│   │   ├── store.py                # 事件入库
│   │   └── consumer.py             # 事件消费（poll + ack）
│   │
│   └── analytics/                  # 分析域
│       ├── dashboard.py            # 数据看板
│       └── reports.py              # 报表
│
├── api/                            # API 路由层
│   ├── middleware.py                # 网关中间件（鉴权、限流、日志）
│   └── v1/                         # API v1
│       ├── auth.py
│       ├── users.py
│       ├── campuses.py
│       ├── roles.py
│       ├── apps.py
│       ├── events.py
│       ├── analytics.py
│       └── config.py
│
├── admin-web/                      # Web 管理后台
│   └── (Vue 3 + Element Plus)
│
├── sdk/                            # 客户端 SDK
│   ├── __init__.py
│   ├── client.py                   # 主客户端类
│   ├── auth.py                     # 登录流程
│   ├── tracking.py                 # 事件上报（可靠）
│   └── storage.py                  # Token 安全存储
│
├── infrastructure/                 # 基础设施
│   ├── database.py                 # 数据库连接
│   ├── redis.py                    # Redis 连接
│   ├── logging.py                  # 结构化 JSON 日志
│   └── metrics.py                  # /metrics 端点
│
├── config/
│   └── settings.py                 # 全局配置
│
├── migrations/                     # 数据库迁移
│   └── ...
│
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
└── requirements.txt
```

### 4.2 权限策略接口

```python
# domains/access/policy.py

from abc import ABC, abstractmethod

class PermissionContext:
    """权限上下文 — 明确定义必须包含的字段"""
    tenant_id: str          # 租户 ID（必须）
    campus_id: str | None   # 校区 ID（校区级操作必须）
    resource_owner: str | None  # 资源所有者 user_id（ABAC 用）
    action_level: str       # "read" / "write" / "admin"

class PermissionPolicy(ABC):
    """权限策略接口 — Phase 1 用 RBAC 实现，未来可替换为 ABAC"""

    @abstractmethod
    def check_permission(
        self,
        user_id: str,
        action: str,        # "create" / "read" / "update" / "delete"
        resource: str,      # "user" / "campus" / "role" / "app" / "analytics"
        context: PermissionContext
    ) -> bool:
        pass


class RBACPolicy(PermissionPolicy):
    """Phase 1 实现：基于角色的权限检查（deny-by-default）"""

    def check_permission(self, user_id, action, resource, context):
        # 1. 获取用户角色
        roles = get_user_roles(user_id)
        if not roles:
            return False  # 无角色 = 拒绝（deny-by-default）

        # 2. 查角色权限表
        for role in roles:
            perms = get_role_permissions(role.id)
            if f"{resource}:{action}" in perms:
                # 3. 校区级角色限定 scope_id == context.campus_id
                if role.level == 2 and context.campus_id:
                    if role.scope_id != context.campus_id:
                        continue  # 无权操作其他校区
                return True

        # 4. 所有角色都没有该权限 → 拒绝
        return False  # deny-by-default

# 未来: class ABACPolicy(PermissionPolicy)
```

**调用方只依赖 `PermissionPolicy` 接口，不依赖具体实现。`PermissionContext` 明确定义必须传入的字段，防止未来 ABAC 升级时接口不兼容。**

### 4.3 事件系统

#### 统一事件格式

```python
# domains/events/schema.py

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class Event(BaseModel):
    """所有模块必须遵守的统一事件格式"""
    event_id: UUID              # 唯一标识，幂等去重
    event_type: str             # 格式: domain.action
    event_version: int          # 事件版本号
    event_source: str           # client / system / ai — 区分事件来源
    timestamp: datetime         # UTC 时间戳

    tenant_id: str              # 所属机构
    campus_id: str | None       # 所属校区
    user_id: str                # 触发用户
    app_id: str                 # 来源应用

    payload: dict               # 事件具体内容
    trace_id: str               # 链路追踪
```

#### Payload Schema 校验

```python
# domains/events/schema.py

from pydantic import BaseModel

class PPTGeneratePayload(BaseModel):
    student_count: int
    template: str
    duration_seconds: int

class AuthLoginPayload(BaseModel):
    device_info: dict
    ip_address: str

class AuthHeartbeatPayload(BaseModel):
    pass

class PPTExportPayload(BaseModel):
    format: str
    file_size: int

class PPTImportPayload(BaseModel):
    student_count: int

class AppStartPayload(BaseModel):
    version: str
    os_info: str

class AppErrorPayload(BaseModel):
    error_type: str
    message: str

# 事件类型 → Schema 映射
EVENT_SCHEMAS = {
    "auth.login": AuthLoginPayload,
    "auth.heartbeat": AuthHeartbeatPayload,
    "ppt.generate": PPTGeneratePayload,
    "ppt.export": PPTExportPayload,
    "ppt.import": PPTImportPayload,
    "app.start": AppStartPayload,
    "app.error": AppErrorPayload,
}

def validate_event(event_type: str, payload: dict) -> dict:
    """所有事件入库前必须经过校验"""
    schema = EVENT_SCHEMAS.get(event_type)
    if schema:
        return schema(**payload).model_dump()
    raise ValueError(f"Unknown event type: {event_type}")
```

#### 事件消费机制

```python
# domains/events/consumer.py

def poll_events(consumer_name: str, limit: int = 100) -> list[Event]:
    """获取该 consumer 尚未消费的事件（带行级锁，防并发重复消费）"""
    last_seq = get_consumer_progress(consumer_name)
    events = query(
        "SELECT * FROM events WHERE event_seq > %s "
        "ORDER BY event_seq LIMIT %s "
        "FOR UPDATE SKIP LOCKED",  # 多实例部署时防止重复消费
        [last_seq, limit]
    )
    return events

def ack_events(consumer_name: str, last_seq: int, current_version: int):
    """确认消费进度（带乐观锁校验 version）"""
    affected = update(
        "UPDATE event_consumers SET last_event_seq = %s, version = version + 1, "
        "updated_at = NOW() WHERE consumer_name = %s AND version = %s",
        [last_seq, consumer_name, current_version]
    )
    if affected == 0:
        raise ConcurrencyError(f"Consumer {consumer_name} version mismatch, retry poll")

def is_processed(consumer_name: str, event_id: str) -> bool:
    """幂等检查：Redis Set 记录已处理的 event_id（TTL 7天）"""
    return not redis.sadd(f"consumer:{consumer_name}:processed", event_id)
```

**消费语义**: at-least-once delivery。所有 consumer **必须**通过 `is_processed()` 检查确保幂等。

**并发安全**: `FOR UPDATE SKIP LOCKED` 确保多 worker 不会重复消费同一批事件。Phase 1 部署单实例，但代码层面已具备多实例安全能力。

#### 分析预聚合（事件消费者副产物）

```sql
-- domains/analytics/pre_agg.py
-- 事件消费者在消费事件时，顺便写入预聚合表，加速看板查询

CREATE TABLE daily_usage_stats (
    date DATE NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    campus_id VARCHAR(64),
    event_type VARCHAR(64) NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (date, tenant_id, campus_id, event_type)
);

-- 消费者逻辑：
-- INSERT INTO daily_usage_stats (date, tenant_id, campus_id, event_type, count)
-- VALUES (CURRENT_DATE, tenant_id, campus_id, event_type, 1)
-- ON CONFLICT (date, tenant_id, campus_id, event_type)
-- DO UPDATE SET count = count + 1;
```

**好处**: 看板页面直接查 `daily_usage_stats`（几百行），而非扫描 `events` 表（百万行），响应从秒级降到毫秒级。

#### 未来预留事件类型（不实现，但格式兼容）

| event_type             | Phase | 用途           |
| ---------------------- | ----- | -------------- |
| `video.stream_start` | 3     | 摄像头开始推流 |
| `video.stream_stop`  | 3     | 摄像头停止推流 |
| `device.online`      | 3     | 设备上线       |
| `analysis.request`   | 4     | 请求 AI 分析   |
| `analysis.result`    | 4     | AI 分析结果    |
| `analysis.alert`     | 4     | AI 告警        |

---

## 5. 客户端 SDK

### 5.1 核心接口

```python
# sdk/client.py

class FablabClient:
    """法贝平台客户端 SDK"""

    def __init__(self, app_key: str, server_url: str):
        self.app_key = app_key
        self.auth = AuthManager(self)
        self.tracking = EventReporter(self)

    def login(self) -> User:
        """弹出微信扫码窗口，返回用户信息"""

    def get_user(self) -> User:
        """获取当前登录用户"""

    def check_auth(self) -> bool:
        """检查当前用户是否仍被授权"""
```

### 5.2 可靠事件上报

```python
# sdk/tracking.py

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_LOCAL_FILE_SIZE = 50 * 1024 * 1024  # 50MB 上限

class EventReporter:
    """可靠的事件上报器（带熔断保护）"""

    MAX_LOCAL_FILE_SIZE = 50 * 1024 * 1024  # 50MB 上限
    CIRCUIT_BREAKER_THRESHOLD = 5           # 连续失败 5 次
    CIRCUIT_BREAKER_COOLDOWN = 300          # 熔断冷却 5 分钟

    def __init__(self, client: FablabClient):
        self._client = client
        # 使用用户 AppData 目录（非安装目录，有写权限）
        self._local_file = get_app_data_dir() / "pending_events.jsonl"
        self._batch: list[Event] = []
        self._batch_size = 10
        self._flush_interval = 30  # 秒
        # 熔断器状态
        self._consecutive_failures = 0
        self._circuit_open_until = 0  # Unix timestamp

    def track(self, event_type: str, payload: dict):
        """记录事件：先持久化到本地文件，再尝试上报。绝不阻塞主线程。"""
        event = self._create_event(event_type, payload)
        self._write_to_local(event)     # 先写本地，保证不丢
        self._batch.append(event)
        if len(self._batch) >= self._batch_size:
            self._flush()

    def _write_to_local(self, event: Event):
        """追加写入本地 JSONL 文件（带大小限制和异常保护）"""
        try:
            # 检查文件大小，超过上限则截断最旧的记录
            if self._local_file.exists() and self._local_file.stat().st_size > MAX_LOCAL_FILE_SIZE:
                self._rotate_local_file()
            record = {"event": event.model_dump(), "status": "pending"}
            with open(self._local_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            # 文件写入失败（被占用/权限问题）绝不能阻塞 PPT 主线程
            logger.warning(f"Failed to write event to local file: {e}")

    def _rotate_local_file(self):
        """文件超过大小时，保留最新的一半记录"""
        try:
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            keep_lines = lines[len(lines) // 2:]  # 保留后半部分
            self._local_file.write_text("\n".join(keep_lines) + "\n", encoding="utf-8")
        except Exception:
            pass  # 旋转失败不阻塞

    def _flush(self):
        """批量上报，成功后标记本地事件为 sent（带熔断保护）"""
        if not self._batch:
            return

        # 熔断器：连续失败 5 次后暂停上报 5 分钟
        if self._consecutive_failures >= 5:
            if time.time() < self._circuit_open_until:
                return  # 熔断中，不上报，事件留在本地
            else:
                self._consecutive_failures = 0  # 冷却结束，重试

        try:
            self._client.api.batch_report(self._batch)
            self._consecutive_failures = 0
            sent_events = list(self._batch)
            self._batch.clear()
            self._mark_local_sent(sent_events)  # 标记 sent，不删除
            self._compact_local()               # 定期清理已发送记录
        except Exception:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 5:
                self._circuit_open_until = time.time() + 300  # 暂停 5 分钟

    def replay_pending(self):
        """启动时调用：重传未成功的事件"""
        pending = self._read_pending_local()  # 只读 status != "sent" 的记录
        for batch in chunk(pending, self._batch_size):
            try:
                self._client.api.batch_report(batch)
                self._mark_local_sent(batch)
            except Exception:
                break  # 网络仍不可用，保留本地文件

    def _mark_local_sent(self, events: list[Event]):
        """标记本地事件为已发送（而非删除），crash-safe"""
        try:
            event_ids = {e.event_id for e in events}
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            updated = []
            for line in lines:
                record = json.loads(line)
                if record["event"]["event_id"] in event_ids:
                    record["status"] = "sent"
                updated.append(record)
            self._local_file.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in updated) + "\n",
                encoding="utf-8"
            )
        except Exception:
            pass  # 标记失败不影响主流程，下次会重传（幂等）

    def _compact_local(self):
        """定期清理：删除已发送的记录，释放磁盘空间"""
        try:
            if not self._local_file.exists():
                return
            lines = self._local_file.read_text(encoding="utf-8").strip().split("\n")
            pending = [l for l in lines if json.loads(l).get("status") != "sent"]
            if len(pending) < len(lines):  # 有可清理的
                self._local_file.write_text(
                    "\n".join(pending) + "\n" if pending else "",
                    encoding="utf-8"
                )
        except Exception:
            pass
```

**关键设计决策：**

- 所有文件操作用 `try-except` 包裹，**宁可丢事件也不能阻塞 PPT 主线程**
- 本地文件大小上限 50MB，超限自动截断旧记录
- 使用 `platformdirs` 库处理跨平台数据目录（Windows/macOS/Linux 自动适配）
- 熔断器：连续失败 5 次后暂停上报 5 分钟，防止服务器故障时卡死客户端
- 事件状态标记（pending/sent）而非清空文件，保证 crash-safe

### 5.3 Token 安全存储

```python
# sdk/storage.py

import keyring

class TokenStorage:
    """使用系统密钥链安全存储 Token"""

    SERVICE_NAME = "fablab-platform"

    def save_token(self, user_id: str, token: str):
        keyring.set_password(self.SERVICE_NAME, user_id, token)

    def get_token(self, user_id: str) -> str | None:
        return keyring.get_password(self.SERVICE_NAME, user_id)

    def delete_token(self, user_id: str):
        keyring.delete_password(self.SERVICE_NAME, user_id)
```

使用 `keyring` 库，Windows 上存储在 Windows Credential Manager，而非明文文件。

---

## 6. 认证流程

### 6.1 微信扫码登录流程

#### 紧急登录通道

超级管理员（super_admin）**必须**保留用户名 + 强密码 + TOTP 二次验证的紧急登录通道，作为微信 OAuth 不可用时的降级方案。

- 仅对 super_admin 角色开放（其他角色只能微信扫码）
- 密码使用 bcrypt 存储，最少 16 位随机生成
- TOTP 使用标准 RFC 6238（Google Authenticator 兼容）
- 紧急登录通道在管理后台登录页面有独立入口（不展示给普通用户）
- 建议将超级管理员紧急凭证离线备份（纸质/密码管理器）

```
PPT 软件                    后端                        微信开放平台
   │                         │                              │
   │  1. 请求登录二维码       │                              │
   │ ──────────────────────→ │                              │
   │                         │  2. 获取授权链接               │
   │                         │ ────────────────────────────→ │
   │                         │  3. 返回 url + state          │
   │                         │ ←──────────────────────────── │
   │  4. 显示二维码窗口       │                              │
   │ ←────────────────────── │                              │
   │                         │                              │
   │  (老师用微信扫码)        │                              │
   │                         │                              │
   │                         │  5. 微信回调(code + state)    │
   │                         │ ←──────────────────────────── │
   │                         │  6. 用 code 换 access_token   │
   │                         │ ────────────────────────────→ │
   │                         │  7. 返回 access_token + openid│
   │                         │ ←──────────────────────────── │
   │                         │                              │
   │                         │  8. 查找/创建用户，签发 JWT    │
   │                         │                              │
   │  9. 轮询登录状态         │                              │
   │ ──────────────────────→ │                              │
   │  10. 返回 token + 用户信息│                             │
   │ ←────────────────────── │                              │
   │                         │                              │
   │  11. 保存 token，进入主界面                             │
```

### 6.2 会话保持与心跳

- Token 有效期: 7 天（可通过配置中心调整）
- 客户端每 5 分钟发送心跳
- **每次 API 请求**都从 Redis 缓存检查用户 `status`（非仅心跳），禁用用户立即返回 401
- 心跳成功时采用**滑动过期**：距离过期 < 1 天时自动签发新 Token
- 被禁用的用户在下次 API 请求时立即失效（Redis 缓存 TTL 5 分钟同步数据库）
- **写时主动失效**：管理员禁用用户时，立即执行 `redis.delete(f"user_status:{user_id}")`，下一个请求直接查 DB 并更新缓存，**无越权窗口**

### 6.3 认证安全机制

- **tenant_id 从 JWT 解析**，不信任请求头中的 `X-Tenant-ID`（防止伪造）
- `X-Tenant-ID` 头仅用于日志和追踪，不参与权限判断
- 用户 status 变更时同步更新 Redis 缓存，确保实时生效
- 微信扫码轮询间隔 1 秒，超时 2 分钟（二维码有效期）

### 6.3 PPT 软件启动流程改造

```
main.py 启动
    │
    ├── SDK 初始化
    │
    ├── 检查本地 Token
    │   ├── 有 Token → 向服务器验证有效性
    │   │   ├── 有效 → 进入主界面
    │   │   └── 无效/过期 → 显示登录窗口
    │   └── 无 Token → 显示登录窗口
    │
    ├── 登录窗口（微信扫码）
    │   ├── 成功 → 保存 Token → 进入主界面
    │   └── 失败 → 提示无权限 → 退出
    │
    └── 主界面运行中
        ├── 每 5 分钟心跳
        ├── 操作事件上报
        └── 心跳 403 → 强制退出
```

---

## 7. API 设计

### 7.1 API 规范

- 基础路径: `/api/v1/`
- 鉴权: JWT Token（Authorization: Bearer xxx）
  - `tenant_id` 和 `user_id` **从 JWT 解析**，不信任请求头
  - `X-App-ID` 头用于标识客户端应用来源
  - `X-Tenant-ID` 头仅用于日志追踪，**不参与权限判断**
- 每次 API 请求中间件检查: JWT 有效 + Redis 中 `user.status == active`
- 返回格式: `{"success": bool, "data": any, "error": str | null}`
- 健康检查: `GET /health`（存活探针）、`GET /ready`（就绪探针，检查 DB/Redis 连接）

### 7.2 核心 API 列表

#### 认证

| 方法 | 路径                               | 说明                   |
| ---- | ---------------------------------- | ---------------------- |
| POST | /api/v1/auth/qrcode                | 获取微信扫码登录二维码 |
| GET  | /api/v1/auth/qrcode/{state}/status | 轮询扫码状态           |
| POST | /api/v1/auth/heartbeat             | 心跳（刷新 Token）     |
| POST | /api/v1/auth/logout                | 登出                   |

#### 用户管理

| 方法 | 路径                      | 说明                   |
| ---- | ------------------------- | ---------------------- |
| GET  | /api/v1/users             | 用户列表（分页、筛选） |
| GET  | /api/v1/users/{id}        | 用户详情               |
| PUT  | /api/v1/users/{id}        | 更新用户               |
| PUT  | /api/v1/users/{id}/status | 启用/禁用用户          |
| POST | /api/v1/users/{id}/roles  | 分配角色               |

#### 校区管理

| 方法   | 路径                  | 说明     |
| ------ | --------------------- | -------- |
| GET    | /api/v1/campuses      | 校区列表 |
| POST   | /api/v1/campuses      | 创建校区 |
| PUT    | /api/v1/campuses/{id} | 更新校区 |
| DELETE | /api/v1/campuses/{id} | 删除校区 |

#### 事件

| 方法 | 路径                 | 说明                   |
| ---- | -------------------- | ---------------------- |
| POST | /api/v1/events/batch | 批量上报事件           |
| GET  | /api/v1/events       | 查询事件（管理后台用） |

#### 分析

| 方法 | 路径                                  | 说明           |
| ---- | ------------------------------------- | -------------- |
| GET  | /api/v1/analytics/dashboard           | 看板数据       |
| GET  | /api/v1/analytics/usage               | 使用统计       |
| GET  | /api/v1/analytics/users/{id}/activity | 单用户活动记录 |

#### 应用管理

| 方法 | 路径              | 说明     |
| ---- | ----------------- | -------- |
| GET  | /api/v1/apps      | 应用列表 |
| POST | /api/v1/apps      | 注册应用 |
| PUT  | /api/v1/apps/{id} | 更新应用 |

---

## 8. Web 管理后台

### 8.1 功能模块

| 模块     | 页面       | 说明                                       |
| -------- | ---------- | ------------------------------------------ |
| 数据看板 | /dashboard | 总览统计（用户数、校区数、事件量、活跃度） |
| 用户管理 | /users     | 用户 CRUD、角色分配、启用/禁用             |
| 校区管理 | /campuses  | 校区 CRUD、层级管理                        |
| 角色权限 | /roles     | 角色 CRUD、权限分配                        |
| 应用管理 | /apps      | 应用注册、配置                             |
| 使用统计 | /analytics | 按校区/用户/时间的使用报表                 |
| 操作日志 | /audit     | 审计日志查询                               |
| 系统配置 | /config    | 全局/租户/校区级配置                       |

### 8.2 管理后台登录

- 管理后台同样使用微信扫码登录
- 管理员扫码后，根据角色权限展示对应菜单和数据
- 校区管理员只能看到本校区的数据

---

## 9. 架构约束文档

> **此章节定义了所有开发人员必须遵守的架构纪律。违反约束视为 bug。**

### 9.1 事件系统约束

- **禁止**直接查询 events 表做业务处理
- **必须**通过 consumer 模式消费事件（poll + ack）
- 新增 event_type **必须**在 `EVENT_SCHEMAS` 中注册 schema
- 所有 consumer **必须**幂等处理（at-least-once 语义）

### 9.2 权限系统约束

- **禁止**在业务代码中直接判断角色字符串（如 `if role == "admin"`）
- **必须**通过 `PermissionPolicy.check_permission()` 接口检查权限
- 新增资源类型 **必须**在 permissions 表中注册
- **deny-by-default**：权限不存在或未配置时，**必须**返回 `False`，绝不允许默认放行

### 9.3 客户端集成约束

- **禁止**绕过 SDK 直接调用后端 API（特殊场景需评审）
- **必须**使用 SDK 的事件上报接口（保证可靠性和格式统一）
- Token **禁止**明文存储在文件中，必须使用 `TokenStorage`（系统密钥链）

### 9.4 API 约束

- 所有 API **必须**在 `/api/v1/` 前缀下
- `tenant_id` **必须**从 JWT 解析，**禁止**信任请求头中的租户标识
- 所有请求 **必须**带 `X-App-ID` 头标识来源应用
- 所有写操作 **必须**异步写入审计日志
- 所有业务查询 **必须**默认过滤 `deleted_at IS NULL`

### 9.5 数据隔离约束

- 所有查询 **必须**带 `tenant_id` 过滤（防止跨租户数据泄露）
- 校区级数据 **必须**带 `campus_id` 过滤
- 应用层通过 Repository 基类自动注入 `tenant_id` 条件
- Phase 2 可选升级 PostgreSQL RLS 作为数据库层双保险

### 9.6 代码审查清单

每个 PR **必须**通过以下检查：

- [ ] 是否绕过 `PermissionPolicy` 直接判断角色？
- [ ] 查询是否带 `tenant_id` 过滤？
- [ ] 写操作是否写入审计日志？
- [ ] 是否绕过 SDK 直接调用后端 API？
- [ ] 新增 event_type 是否注册了 Schema？
- [ ] 敏感信息（密钥、Token）是否出现在日志中？

---

## 10. 部署方案

### 10.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env  # 敏感配置不提交到 Git，.env 加入 .gitignore

  admin-web:
    build: ./admin-web
    ports:
      - "3000:80"

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=fablab_platform
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - api
      - admin-web

volumes:
  pgdata:
  redisdata:
```

**Nginx 限流配置：**

```nginx
# 全局限流
limit_req_zone $binary_remote_addr zone=global:10m rate=20r/s;
# 事件上报限流
limit_req_zone $binary_remote_addr zone=events:10m rate=100r/m;
# 登录二维码限流
limit_req_zone $binary_remote_addr zone=qrcode:10m rate=10r/h;

server {
    location /api/v1/auth/qrcode {
        limit_req zone=qrcode burst=5 nodelay;
    }
    location /api/v1/events/ {
        limit_req zone=events burst=20 nodelay;
    }
    location /api/ {
        limit_req zone=global burst=30 nodelay;
    }
}
```

### 10.2 HTTPS 配置

使用 Let's Encrypt 免费证书，通过 certbot 自动续期。

---

## 11. Phase 1 交付物清单

| # | 交付物        | 说明                                           |
| - | ------------- | ---------------------------------------------- |
| 1 | 后端 API 服务 | FastAPI + PostgreSQL + Redis                   |
| 2 | Web 管理后台  | Vue 3 + Element Plus                           |
| 3 | 客户端 SDK    | Python 包（auth + tracking）                   |
| 4 | PPT 软件改造  | 登录窗口 + SDK 集成 + 操作追踪                 |
| 5 | 基础设施      | Nginx + Docker Compose + 结构化日志 + /metrics |
| 6 | 数据模型      | 多租户 + RBAC + 事件 + 审计 + 配置中心         |

---

## 12. 运维策略

### 12.1 备份与恢复

| 项目       | 策略                                 |
| ---------- | ------------------------------------ |
| PostgreSQL | 云厂商自动备份（保留 30 天）         |
| Redis      | AOF 持久化（仅缓存数据，丢失可接受） |
| 配置文件   | Git 仓库管理                         |
| 微信密钥等 | 独立安全存储（.env 文件 + 加密备份） |
| 恢复演练   | 每月在测试环境验证备份可用性         |

### 12.2 监控与告警

| 指标       | 告警阈值               | 方式     |
| ---------- | ---------------------- | -------- |
| CPU 使用率 | > 80% 持续 5 分钟      | 云监控   |
| 磁盘使用率 | > 85%                  | 云监控   |
| DB 连接数  | > 80% 连接池           | /metrics |
| 事件积压   | consumer 滞后 > 1 小时 | /metrics |
| API 错误率 | 5xx > 5% 持续 3 分钟   | /metrics |

### 12.3 审计日志异步写入

审计日志通过 FastAPI `BackgroundTasks` 异步写入，避免阻塞请求响应。确保审计日志写入失败时记录到结构化日志（不丢失记录）。

---

## 13. 工程规范

### 13.1 数据库迁移

使用 **Alembic** 作为数据库迁移工具，集成在 FastAPI 项目中。

- 迁移文件命名: 自动生成（`alembic revision --autogenerate`）
- 每次变更一个表或一个功能点，不混合多个不相关的变更
- 生产环境迁移在部署脚本中自动执行: `alembic upgrade head`
- 应用启动时检查分区并自动创建未来 3 个月的 events 分区

### 13.2 测试策略

| 测试类型     | 覆盖范围                           | 最低覆盖率    | 运行时机 |
| ------------ | ---------------------------------- | ------------- | -------- |
| 单元测试     | domains/ 下所有业务逻辑            | 70%           | 每次提交 |
| API 集成测试 | 所有写操作 + 权限检查 + 多租户隔离 | 核心路径 100% | 每次提交 |
| SDK 测试     | 本地 mock 服务端测试               | 关键路径      | 每次提交 |

**测试要求**:

- 每个 domain 模块有独立测试文件
- 权限测试必须验证 deny-by-default（未配置权限时返回 False）
- 多租户测试必须验证跨租户数据隔离
- API 测试必须覆盖所有错误状态码（401/403/404/422）

### 13.3 CI/CD（Phase 1 简版）

GitHub Actions 工作流:

```
Push → Lint (ruff) → Unit Tests → Integration Tests → Build Docker Image → Deploy (手动触发)
```

Phase 1 不做自动部署，手动触发 `docker-compose pull && docker-compose up -d`。

### 13.4 SDK 跨平台支持

使用 `platformdirs` 库自动处理不同操作系统的数据目录:

| 系统    | 路径                                               |
| ------- | -------------------------------------------------- |
| Windows | `%APPDATA%/fablab-platform/`                     |
| macOS   | `~/Library/Application Support/fablab-platform/` |
| Linux   | `~/.local/share/fablab-platform/`                |

```python
from platformdirs import user_data_dir

def get_app_data_dir() -> Path:
    return Path(user_data_dir("fablab-platform"))
```

### 13.5 长期架构演进备注

| 阶段         | 已知瓶颈                                | 应对策略                                             |
| ------------ | --------------------------------------- | ---------------------------------------------------- |
| Phase 2 末期 | PostgreSQL 轮询事件队列（>100 事件/秒） | 评估迁移至 Redis Streams 或 Kafka                    |
| Phase 3 前期 | 视频流需独立基础设施                    | Phase 2 时立项技术预研（SRS/ZLMediaKit + CDN + OSS） |
| Phase 3 前期 | 校区层级递归查询（>500 校区）           | 评估 Materialized Path 或 ltree 扩展                 |
| Phase 4      | AI 实时分析 GPU 成本                    | Phase 2 时建立成本模型，验证商业可行性               |
| Phase 2+     | 单机无高可用                            | 评估双机热备或迁移 K8s，定义 RTO 目标                |

### 13.6 待 Phase 2 前补充的事项

| 事项             | 说明                                                                                                                               | 优先级 |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------ |
| PgBouncer 连接池 | FastAPI 多 worker 下 SQLAlchemy 内置连接池可能耗尽 PG 最大连接数。Phase 1 单 worker 问题不大，Phase 2 前引入 PgBouncer             | P1     |
| JWT 密钥轮换策略 | 使用 RS256（非对称）替代 HS256，便于密钥轮换。轮换条件：泄露时立即、正常每半年一次。支持双 Key 过渡期（旧 Key 验签 + 新 Key 签发） | P1     |

---

## 13. 前置条件

在开始开发前，需要完成以下准备工作：

| # | 事项             | 说明                    |
| - | ---------------- | ----------------------- |
| 1 | 注册微信开放平台 | 使用企业/个体工商户资质 |
| 2 | 创建网站应用     | 获取 AppID 和 AppSecret |
| 3 | 购买域名         | 需要已备案域名          |
| 4 |                  |                         |
| 5 | 域名备案         | ICP 备案（约 1-2 周）   |
| 6 | 安装 Docker      | 服务器环境准备          |
