"""initial schema

Revision ID: d46e1da4110b
Revises:
Create Date: 2026-04-04 16:18:09.648595

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


# revision identifiers, used by Alembic.
revision: str = 'd46e1da4110b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── tenants ─────────────────────────────────────────
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('isolation_mode', sa.String(16), server_default='shared'),
        sa.Column('status', sa.String(16), server_default='active'),
        sa.Column('config', JSONB, server_default='{}'),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_tenants_tenant_id', 'tenants', ['tenant_id'])

    # ─── campuses ────────────────────────────────────────
    op.create_table(
        'campuses',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('parent_id', sa.String(64)),
        sa.Column('campus_level', sa.String(16), server_default='branch'),
        sa.Column('status', sa.String(16), server_default='active'),
        sa.Column('config', JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    # ─── users ──────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('campus_id', sa.String(64)),
        sa.Column('wechat_openid', sa.String(128), unique=True),
        sa.Column('wechat_unionid', sa.String(128)),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('avatar_url', sa.String(512)),
        sa.Column('status', sa.String(16), server_default='active'),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    # ─── roles ──────────────────────────────────────────
    op.create_table(
        'roles',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('tenant_id', sa.String(64)),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('display_name', sa.String(128), nullable=False),
        sa.Column('description', sa.String(512)),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_system', sa.Boolean(), server_default='false'),
    )

    # ─── permissions ─────────────────────────────────────
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(128), primary_key=True),
        sa.Column('resource', sa.String(64), nullable=False),
        sa.Column('action', sa.String(16), nullable=False),
        sa.Column('display_name', sa.String(128), nullable=False),
        sa.Column('description', sa.String(512)),
    )

    # ─── role_permissions ────────────────────────────────
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(64), nullable=False),
        sa.Column('permission_id', sa.String(128), nullable=False),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    )

    # ─── user_roles ──────────────────────────────────────
    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('role_id', sa.String(64), nullable=False),
        sa.Column('scope_id', sa.String(64), nullable=False, server_default='*'),
        sa.PrimaryKeyConstraint('user_id', 'role_id', 'scope_id'),
    )

    # ─── apps ────────────────────────────────────────────
    op.create_table(
        'apps',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('app_key', sa.String(64), nullable=False, unique=True),
        sa.Column('app_secret_hash', sa.String(128), nullable=False),
        sa.Column('description', sa.String(512)),
        sa.Column('status', sa.String(16), server_default='active'),
        sa.Column('config', JSONB, server_default='{}'),
    )

    # ─── events (分区表 — raw SQL) ──────────────────────
    op.execute("""
        CREATE TABLE events (
            event_seq BIGSERIAL,
            event_id UUID NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            event_version INTEGER NOT NULL DEFAULT 1,
            event_source VARCHAR(16) NOT NULL DEFAULT 'client',
            timestamp TIMESTAMPTZ NOT NULL,
            tenant_id VARCHAR(64) NOT NULL,
            campus_id VARCHAR(64),
            user_id VARCHAR(64) NOT NULL,
            app_id VARCHAR(64) NOT NULL,
            payload JSONB NOT NULL,
            trace_id VARCHAR(64),
            PRIMARY KEY (event_seq, timestamp)
        ) PARTITION BY RANGE (timestamp);

        CREATE UNIQUE INDEX idx_events_event_id ON events (event_id);
        CREATE INDEX idx_events_tenant_time ON events (tenant_id, timestamp);
        CREATE INDEX idx_events_type ON events (event_type);
        CREATE INDEX idx_events_tenant_type_time ON events (tenant_id, event_type, timestamp);
        CREATE INDEX idx_events_tenant_user_time ON events (tenant_id, user_id, timestamp DESC);
        CREATE INDEX idx_events_user ON events (user_id);
        CREATE INDEX idx_events_source ON events (event_source);

        CREATE TABLE events_2026_04 PARTITION OF events
            FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
        CREATE TABLE events_2026_05 PARTITION OF events
            FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
        CREATE TABLE events_2026_06 PARTITION OF events
            FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
    """)

    # ─── event_consumers ─────────────────────────────────
    op.create_table(
        'event_consumers',
        sa.Column('consumer_name', sa.String(64), primary_key=True),
        sa.Column('last_event_seq', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ─── audit_logs ──────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('user_role', sa.String(64)),
        sa.Column('action', sa.String(16), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(64)),
        sa.Column('changes', JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_audit_tenant_time', 'audit_logs', ['tenant_id', 'timestamp'])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_time', 'audit_logs', ['timestamp'])

    # ─── configs ─────────────────────────────────────────
    op.create_table(
        'configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scope', sa.String(16), nullable=False),
        sa.Column('scope_id', sa.String(64)),
        sa.Column('key', sa.String(128), nullable=False),
        sa.Column('value', JSONB, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scope', 'scope_id', 'key'),
    )

    # ─── sessions ────────────────────────────────────────
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(128), primary_key=True),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('token_hash', sa.String(128), nullable=False),
        sa.Column('device_info', JSONB),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ─── daily_usage_stats ───────────────────────────────
    op.create_table(
        'daily_usage_stats',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('campus_id', sa.String(64)),
        sa.Column('event_type', sa.String(64), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('date', 'tenant_id', 'campus_id', 'event_type'),
    )


def downgrade() -> None:
    op.drop_table('daily_usage_stats')
    op.drop_table('sessions')
    op.drop_table('configs')
    op.drop_table('audit_logs')
    op.drop_table('event_consumers')
    op.execute("DROP TABLE IF EXISTS events")
    op.drop_table('apps')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('users')
    op.drop_table('campuses')
    op.drop_table('tenants')
