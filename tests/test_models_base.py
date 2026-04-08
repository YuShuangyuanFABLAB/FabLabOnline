"""测试 TenantModel 基类 — 多租户隔离防呆机制"""
import pytest
from sqlalchemy import String, Column

from models.base import Base, TenantModel, TimestampMixin, SoftDeleteMixin


class FakeTenantModel(Base, TenantModel):
    """测试用假模型"""
    __tablename__ = "test_tenant_models"
    id = Column(String(64), primary_key=True)
    name = Column(String(128))


class TestTimestampMixin:
    def test_has_created_at(self):
        assert hasattr(TimestampMixin, "created_at")

    def test_has_updated_at(self):
        assert hasattr(TimestampMixin, "updated_at")


class TestSoftDeleteMixin:
    def test_has_deleted_at(self):
        assert hasattr(SoftDeleteMixin, "deleted_at")


class TestTenantModel:
    def test_has_tenant_id(self):
        assert hasattr(TenantModel, "tenant_id")

    def test_tenant_query_injects_tenant_id(self):
        """tenant_query() 自动注入 tenant_id + 软删除过滤"""
        stmt = FakeTenantModel.tenant_query("tenant_abc")
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "tenant_abc" in sql

    def test_tenant_query_rejects_empty_tenant_id(self):
        """空 tenant_id 必须报错（防呆）"""
        with pytest.raises(ValueError, match="tenant_id"):
            FakeTenantModel.tenant_query("")

    def test_tenant_query_rejects_none_tenant_id(self):
        with pytest.raises(ValueError, match="tenant_id"):
            FakeTenantModel.tenant_query(None)

    def test_assert_tenant_owned_passes(self):
        """匹配的 tenant_id 不抛异常"""
        instance = FakeTenantModel(id="1", name="test", tenant_id="t1")
        FakeTenantModel.assert_tenant_owned(instance, "t1")

    def test_assert_tenant_owned_raises_on_mismatch(self):
        """不匹配的 tenant_id 抛 PermissionError"""
        instance = FakeTenantModel(id="1", name="test", tenant_id="t1")
        with pytest.raises(PermissionError, match="租户隔离违规"):
            FakeTenantModel.assert_tenant_owned(instance, "t2")
