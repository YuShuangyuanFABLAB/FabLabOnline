"""校区 CRUD domain 逻辑"""
from datetime import datetime, timezone

from infrastructure.database import async_session
from models.campus import Campus
from sqlalchemy import select


async def get_campuses(tenant_id: str, page: int = 1, size: int = 20) -> list[Campus]:
    async with async_session() as db:
        result = await db.execute(
            select(Campus)
            .where(Campus.tenant_id == tenant_id, Campus.deleted_at.is_(None))
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all())


async def create_campus(tenant_id: str, campus_id: str, name: str, **kwargs) -> Campus:
    async with async_session() as db:
        campus = Campus(id=campus_id, tenant_id=tenant_id, name=name, **kwargs)
        db.add(campus)
        await db.commit()
        await db.refresh(campus)
        return campus


async def update_campus(campus_id: str, tenant_id: str, **kwargs) -> Campus | None:
    async with async_session() as db:
        result = await db.execute(
            select(Campus).where(
                Campus.id == campus_id,
                Campus.tenant_id == tenant_id,
                Campus.deleted_at.is_(None),
            )
        )
        campus = result.scalar_one_or_none()
        if not campus:
            return None
        for key, value in kwargs.items():
            setattr(campus, key, value)
        await db.commit()
        await db.refresh(campus)
        return campus


async def soft_delete_campus(campus_id: str, tenant_id: str) -> bool:
    async with async_session() as db:
        result = await db.execute(
            select(Campus).where(
                Campus.id == campus_id,
                Campus.tenant_id == tenant_id,
                Campus.deleted_at.is_(None),
            )
        )
        campus = result.scalar_one_or_none()
        if not campus:
            return False
        campus.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return True
