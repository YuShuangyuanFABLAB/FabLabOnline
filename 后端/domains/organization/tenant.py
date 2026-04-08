"""租户 CRUD domain 逻辑"""
from datetime import datetime, timezone

from infrastructure.database import async_session
from models.tenant import Tenant
from sqlalchemy import select


async def get_tenants(page: int = 1, size: int = 20) -> list[Tenant]:
    async with async_session() as db:
        result = await db.execute(
            select(Tenant)
            .where(Tenant.deleted_at.is_(None))
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all())


async def get_tenant(tenant_id: str) -> Tenant | None:
    async with async_session() as db:
        result = await db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()


async def create_tenant(tenant_id: str, name: str, **kwargs) -> Tenant:
    async with async_session() as db:
        tenant = Tenant(id=tenant_id, name=name, **kwargs)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant


async def update_tenant(tenant_id: str, **kwargs) -> Tenant | None:
    async with async_session() as db:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant or tenant.deleted_at:
            return None
        for key, value in kwargs.items():
            setattr(tenant, key, value)
        await db.commit()
        await db.refresh(tenant)
        return tenant


async def soft_delete_tenant(tenant_id: str) -> bool:
    async with async_session() as db:
        tenant = await db.get(Tenant, tenant_id)
        if not tenant or tenant.deleted_at:
            return False
        tenant.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True
