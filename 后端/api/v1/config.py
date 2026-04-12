"""Config API — 配置管理（Redis 缓存）"""
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from infrastructure.database import async_session
from infrastructure.redis import redis_client
from models.config import Config as ConfigModel
from domains.access.policy import get_policy, PermissionContext
from domains.access.audit import write_audit_log

router = APIRouter(prefix="/config", tags=["config"])


class UpdateConfigRequest(BaseModel):
    scope: str = Field(..., min_length=1, max_length=64)
    scope_id: str | None = None
    key: str = Field(..., min_length=1, max_length=128)
    value: dict


async def get_config_value(scope: str, scope_id: str | None, key: str) -> dict | None:
    """读取配置：Redis 缓存 → DB → 返回"""
    cache_key = f"config:{scope}:{scope_id or 'global'}:{key}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    async with async_session() as db:
        result = await db.execute(
            select(ConfigModel).where(
                ConfigModel.scope == scope,
                ConfigModel.scope_id == scope_id,
                ConfigModel.key == key,
            )
        )
        config = result.scalar_one_or_none()
        if config:
            await redis_client.setex(cache_key, 300, json.dumps(config.value))
            return config.value
    return None


@router.get("")
async def get_config(request: Request, scope: str = "global", scope_id: str | None = None, key: str | None = None):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "config", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    if key:
        value = await get_config_value(scope, scope_id, key)
        return {"success": True, "data": {"key": key, "value": value}}

    async with async_session() as db:
        query = select(ConfigModel).where(ConfigModel.scope == scope)
        if scope_id:
            query = query.where(ConfigModel.scope_id == scope_id)
        result = await db.execute(query)
        configs = result.scalars().all()
        return {"success": True, "data": [
            {"key": c.key, "value": c.value, "scope": c.scope, "scope_id": c.scope_id}
            for c in configs
        ]}


@router.put("")
async def update_config(request: Request, body: UpdateConfigRequest):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "update", "config", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        result = await db.execute(
            select(ConfigModel).where(
                ConfigModel.scope == body.scope,
                ConfigModel.scope_id == body.scope_id,
                ConfigModel.key == body.key,
            )
        )
        config = result.scalar_one_or_none()
        if config:
            config.value = body.value
        else:
            config = ConfigModel(scope=body.scope, scope_id=body.scope_id, key=body.key, value=body.value)
            db.add(config)
        await db.commit()

    cache_key = f"config:{body.scope}:{body.scope_id or 'global'}:{body.key}"
    await redis_client.delete(cache_key)

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="update",
        resource_type="config",
        resource_id=body.key,
        changes={"scope": body.scope, "scope_id": body.scope_id, "value": body.value},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True, "data": {"key": body.key, "value": body.value}}
