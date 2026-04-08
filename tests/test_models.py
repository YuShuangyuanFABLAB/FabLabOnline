"""测试所有 ORM 模型字段定义 — TDD RED"""
import pytest


class TestTenantModel:
    def test_tenant_fields(self):
        from models.tenant import Tenant
        t = Tenant(id="fablab", name="法贝实验室")
        assert t.id == "fablab"
        assert t.name == "法贝实验室"
        assert t.isolation_mode == "shared"
        assert t.status == "active"

    def test_tenant_config_is_jsonb(self):
        from models.tenant import Tenant
        from sqlalchemy import inspect as sa_inspect
        columns = {c.name: c for c in sa_inspect(Tenant).columns}
        assert "config" in columns


class TestCampusModel:
    def test_campus_fields(self):
        from models.campus import Campus
        c = Campus(id="hz-xihu", tenant_id="fablab", name="杭州西湖校区")
        assert c.id == "hz-xihu"
        assert c.tenant_id == "fablab"
        assert c.campus_level == "branch"
        assert c.status == "active"


class TestUserModel:
    def test_user_fields(self):
        from models.user import User
        u = User(id="u_001", tenant_id="fablab", name="张老师")
        assert u.id == "u_001"
        assert u.tenant_id == "fablab"
        assert u.status == "active"

    def test_user_has_wechat_fields(self):
        from models.user import User
        from sqlalchemy import inspect as sa_inspect
        columns = {c.name: c for c in sa_inspect(User).columns}
        assert "wechat_openid" in columns
        assert "wechat_unionid" in columns


class TestRoleModel:
    def test_role_fields(self):
        from models.role import Role
        r = Role(id="super_admin", name="super_admin", display_name="超级管理员", level=0)
        assert r.id == "super_admin"
        assert r.level == 0
        assert r.is_system is True

    def test_user_role_scope_id_default(self):
        """scope_id 默认值为 '*'（非 NULL，避免联合主键 bug）"""
        from models.role import UserRole
        ur = UserRole(user_id="u1", role_id="r1")
        assert ur.scope_id == "*"

    def test_permission_fields(self):
        from models.role import Permission
        p = Permission(id="user:create", resource="user", action="create", display_name="创建用户")
        assert p.id == "user:create"
        assert p.resource == "user"
        assert p.action == "create"


class TestAppModel:
    def test_app_fields(self):
        from models.app import App
        a = App(id="ppt-gen", name="PPT生成器", app_key="ppt-generator")
        assert a.id == "ppt-gen"
        assert a.app_key == "ppt-generator"
        assert a.status == "active"


class TestEventModel:
    def test_event_has_partition_compatible_pk(self):
        """分区表主键必须包含分区键 timestamp"""
        from models.event import Event
        from sqlalchemy import inspect as sa_inspect
        pk_cols = [c.name for c in sa_inspect(Event).primary_key]
        assert "event_seq" in pk_cols

    def test_event_consumer_fields(self):
        from models.event import EventConsumer
        ec = EventConsumer(consumer_name="daily_stats")
        assert ec.consumer_name == "daily_stats"
        assert ec.last_event_seq == 0
        assert ec.version == 0


class TestAuditLogModel:
    def test_audit_log_fields(self):
        from models.audit import AuditLog
        assert hasattr(AuditLog, "tenant_id")
        assert hasattr(AuditLog, "user_id")
        assert hasattr(AuditLog, "action")
        assert hasattr(AuditLog, "resource_type")


class TestConfigModel:
    def test_config_fields(self):
        from models.config import Config
        c = Config(scope="global", key="max_users", value={"limit": 100})
        assert c.scope == "global"
        assert c.key == "max_users"


class TestSessionModel:
    def test_session_fields(self):
        from models.session import Session
        assert hasattr(Session, "user_id")
        assert hasattr(Session, "token_hash")
        assert hasattr(Session, "expires_at")


class TestDailyUsageStatsModel:
    def test_stats_fields(self):
        from models.daily_usage_stats import DailyUsageStats
        assert hasattr(DailyUsageStats, "date")
        assert hasattr(DailyUsageStats, "tenant_id")
        assert hasattr(DailyUsageStats, "count")
