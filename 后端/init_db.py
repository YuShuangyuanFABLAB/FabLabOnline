"""数据库初始化 — 建表 + 种子数据"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import text
from infrastructure.database import engine, async_session
from models.base import Base
from domains.identity.password import hash_password

import models  # noqa: F401


async def create_tables():
    """创建所有表（events 分区表需要特殊处理）"""
    async with engine.begin() as conn:
        tables_to_create = [
            t for t in Base.metadata.sorted_tables
            if t.name != "events"
        ]
        for table in tables_to_create:
            await conn.run_sync(
                lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True)
            )

    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                event_seq    BIGSERIAL,
                event_id     UUID NOT NULL,
                event_type   VARCHAR(64) NOT NULL,
                event_version INTEGER NOT NULL DEFAULT 1,
                event_source VARCHAR(16) NOT NULL DEFAULT 'client',
                timestamp    TIMESTAMPTZ NOT NULL,
                tenant_id    VARCHAR(64) NOT NULL,
                campus_id    VARCHAR(64),
                user_id      VARCHAR(64) NOT NULL,
                app_id       VARCHAR(64) NOT NULL,
                payload      JSONB NOT NULL,
                trace_id     VARCHAR(64),
                PRIMARY KEY (event_seq, timestamp)
            ) PARTITION BY RANGE (timestamp)
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_id
            ON events (event_id, timestamp)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_events_tenant_time
            ON events (tenant_id, timestamp)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_events_tenant_type_time
            ON events (tenant_id, event_type, timestamp)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_events_user ON events (user_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_events_source ON events (event_source)
        """))

    print("Tables created successfully")


async def seed_data():
    """插入初始种子数据"""
    async with async_session() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM tenants"))
        if result.scalar() > 0:
            print("Seed data already exists, skipping")
            return

        now = datetime.now(timezone.utc)
        empty_json = json.dumps({})

        # 管理员密码：优先使用环境变量 ADMIN_PASSWORD，否则用默认值
        from config.settings import settings
        admin_password = settings.ADMIN_PASSWORD or "admin123"
        if admin_password == "admin123":
            print("⚠️  WARNING: Using default admin password 'admin123'. "
                  "Set ADMIN_PASSWORD in .env for production!")
        password_hash = hash_password(admin_password)

        # ─── tenants (has TimestampMixin: created_at, updated_at) ───
        await db.execute(text("""
            INSERT INTO tenants (id, tenant_id, name, isolation_mode, status, config, created_at, updated_at)
            VALUES ('default', 'default', '法贝实验室', 'shared', 'active', :cfg, :now, :now)
        """), {"cfg": empty_json, "now": now})

        # ─── roles (Base only, NO timestamps) ───
        for role_id, name, dname, desc, level in [
            ("super_admin", "super_admin", "超级管理员", "系统最高权限", 100),
            ("admin", "admin", "管理员", "校区管理员", 50),
            ("teacher", "teacher", "教师", "普通教师", 10),
        ]:
            await db.execute(text("""
                INSERT INTO roles (id, tenant_id, name, display_name, description, level, is_system)
                VALUES (:id, 'default', :name, :dname, :desc, :level, true)
            """), {"id": role_id, "name": name, "dname": dname, "desc": desc, "level": level})

        # ─── users (Base + TenantModel, has timestamps) ───
        await db.execute(text("""
            INSERT INTO users (id, tenant_id, name, phone, status, created_at, updated_at)
            VALUES ('admin', 'default', '系统管理员', '13800138000', 'active', :now, :now)
        """), {"now": now})

        # ─── configs (Base, has updated_at) ───
        await db.execute(text("""
            INSERT INTO configs (scope, scope_id, key, value, updated_at)
            VALUES ('user', 'admin', 'password_hash', :val, :now)
        """), {"val": json.dumps(password_hash), "now": now})

        # ─── user_roles (Base only, NO timestamps) ───
        await db.execute(text("""
            INSERT INTO user_roles (user_id, role_id, scope_id)
            VALUES ('admin', 'super_admin', '*')
        """))

        # ─── permissions + role_permissions ───
        default_permissions = [
            ("user:read", "user", "read", "查看用户", ""),
            ("user:create", "user", "create", "创建用户", ""),
            ("user:update", "user", "update", "修改用户", ""),
            ("user:delete", "user", "delete", "删除用户", ""),
            ("role:read", "role", "read", "查看角色", ""),
            ("role:update", "role", "update", "修改角色", ""),
            ("campus:read", "campus", "read", "查看校区", ""),
            ("campus:create", "campus", "create", "创建校区", ""),
            ("campus:update", "campus", "update", "修改校区", ""),
            ("app:read", "app", "read", "查看应用", ""),
            ("app:update", "app", "update", "修改应用", ""),
            ("config:read", "config", "read", "查看配置", ""),
            ("config:update", "config", "update", "修改配置", ""),
            ("audit:read", "audit", "read", "查看审计", ""),
            ("analytics:read", "analytics", "read", "查看分析", ""),
            ("event:read", "event", "read", "查看事件", ""),
            ("event:create", "event", "create", "上报事件", ""),
        ]
        for pid, resource, action, dname, desc in default_permissions:
            await db.execute(text("""
                INSERT INTO permissions (id, resource, action, display_name, description)
                VALUES (:id, :resource, :action, :dname, :desc)
            """), {"id": pid, "resource": resource, "action": action, "dname": dname, "desc": desc})

        # super_admin 拥有所有权限
        for pid, *_ in default_permissions:
            await db.execute(text("""
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES ('super_admin', :pid)
            """), {"pid": pid})

        # ─── campuses (Base + TenantModel, has timestamps) ───
        await db.execute(text("""
            INSERT INTO campuses (id, tenant_id, name, campus_level, status, config, created_at, updated_at)
            VALUES ('hq', 'default', '总部', 'headquarters', 'active', :cfg, :now, :now)
        """), {"cfg": empty_json, "now": now})

        # ─── apps (Base only, NO timestamps) ───
        for app_id, app_name, app_key, secret_raw, app_desc in [
            ("ppt-generator", "PPT生成器", "ppt_gen_key", "ppt_gen_secret", "PPT课件生成桌面客户端"),
            ("admin-web", "管理后台", "admin_web_key", "admin_web_secret", "Web管理后台"),
        ]:
            await db.execute(text("""
                INSERT INTO apps (id, name, app_key, app_secret_hash, description, status, config)
                VALUES (:id, :name, :key, :secret, :desc, 'active', :cfg)
            """), {
                "id": app_id,
                "name": app_name,
                "key": app_key,
                "secret": hashlib.sha256(secret_raw.encode()).hexdigest(),
                "desc": app_desc,
                "cfg": empty_json,
            })

        await db.commit()
        print("Seed data inserted successfully")


async def _has_alembic_version() -> bool:
    """检查 alembic_version 表是否存在且有记录"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
            return result.scalar() > 0
    except Exception:
        return False


async def init():
    """数据库初始化 — Alembic 管理迁移，本脚本仅负责种子数据"""
    if not await _has_alembic_version():
        print("No Alembic migrations found, creating tables directly...")
        await create_tables()
    await seed_data()
    print("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init())
