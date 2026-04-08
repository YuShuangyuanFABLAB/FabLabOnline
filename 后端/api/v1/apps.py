"""Apps API — 应用注册"""
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from infrastructure.database import async_session
from models.app import App
from domains.access.policy import get_policy, PermissionContext

router = APIRouter(prefix="/apps", tags=["apps"])


@router.get("")
async def list_apps(request: Request):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "read", "app", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        result = await db.execute(select(App).where(App.status == "active"))
        apps = result.scalars().all()
        return {"success": True, "data": [
            {"id": a.id, "name": a.name, "app_key": a.app_key, "status": a.status}
            for a in apps
        ]}


@router.post("")
async def register_app(request: Request, app_id: str, name: str, app_key: str):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "create", "app", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    async with async_session() as db:
        app = App(
            id=app_id,
            name=name,
            app_key=app_key,
            app_secret_hash=hashlib.sha256(secrets.token_hex(32).encode()).hexdigest(),
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)
        return {"success": True, "data": {"id": app.id, "name": app.name, "app_key": app.app_key}}
