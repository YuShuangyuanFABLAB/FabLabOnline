"""权限查询 domain 逻辑"""
from infrastructure.database import async_session
from models.role import Permission, RolePermission
from sqlalchemy import select


async def get_all_permissions() -> list[Permission]:
    async with async_session() as db:
        result = await db.execute(select(Permission))
        return list(result.scalars().all())


async def get_role_permissions(role_id: str) -> list[str]:
    async with async_session() as db:
        result = await db.execute(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )
        return [rp.permission_id for rp in result.scalars().all()]
