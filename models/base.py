from sqlalchemy import Column, DateTime, String, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class TenantModel(TimestampMixin, SoftDeleteMixin):
    """
    多租户隔离基类 — 所有涉及租户的模型必须继承此类。
    自动注入 tenant_id 过滤，防止新人忘记加条件导致跨租户数据泄露。

    强制规则：
    - 所有查询必须走 tenant_query()，禁止直接用 select(Model)
    - tenant_id 从 JWT 中间件注入，不信任请求头
    """
    tenant_id = Column(String(64), nullable=False, index=True)

    @classmethod
    def tenant_query(cls, tenant_id: str):
        """安全查询：自动注入 tenant_id + 软删除过滤"""
        if not tenant_id:
            raise ValueError("tenant_id 不能为空（防呆：避免全表查询）")
        stmt = select(cls).where(
            cls.tenant_id == tenant_id,
            cls.deleted_at.is_(None),
        )
        return stmt

    @classmethod
    def assert_tenant_owned(cls, instance, tenant_id: str):
        """断言实例属于指定租户 — 写操作前调用"""
        if instance.tenant_id != tenant_id:
            raise PermissionError(
                f"租户隔离违规：对象 tenant_id={instance.tenant_id}，"
                f"请求 tenant_id={tenant_id}"
            )
