"""Apps API — 应用注册"""
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from infrastructure.database import async_session
from models.app import App
from domains.access.policy import get_policy, PermissionContext
from domains.access.audit import write_audit_log

router = APIRouter(prefix="/apps", tags=["apps"])


class RegisterAppRequest(BaseModel):
    app_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    app_key: str = Field(..., min_length=1, max_length=128)


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
async def register_app(request: Request, body: RegisterAppRequest):
    tenant_id = request.state.tenant_id
    policy = get_policy()
    ctx = PermissionContext(tenant_id=tenant_id)
    if not await policy.check_permission(request.state.user_id, "create", "app", ctx):
        raise HTTPException(status_code=403, detail="Permission denied")

    raw_secret = secrets.token_hex(32)
    secret_hash = hashlib.sha256(raw_secret.encode()).hexdigest()

    async with async_session() as db:
        app = App(
            id=body.app_id,
            name=body.name,
            app_key=body.app_key,
            app_secret_hash=secret_hash,
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)

    await write_audit_log(
        tenant_id=tenant_id,
        user_id=request.state.user_id,
        action="create",
        resource_type="app",
        resource_id=body.app_id,
        changes={"name": body.name, "app_key": body.app_key},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True, "data": {
        "id": app.id, "name": app.name, "app_key": app.app_key,
        "app_secret": raw_secret,
    }}
