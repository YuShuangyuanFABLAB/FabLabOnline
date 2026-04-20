"""Auth API — 扫码登录 + 会话管理 + 登录限流"""
import json
import secrets
import time

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select

from config.settings import settings
from infrastructure.database import async_session
from infrastructure.redis import redis_client
from models.user import User
from domains.identity.wechat_oauth import WechatOAuth
from domains.identity.token_manager import TokenManager
from domains.identity.session_manager import SessionManager
from domains.identity.password import verify_password
from domains.access.roles import get_user_roles

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = WechatOAuth()
token_mgr = TokenManager()
session_mgr = SessionManager()

LOGIN_RATE_LIMIT = 5         # 最大失败次数
LOGIN_LOCKOUT_SECONDS = 900  # 锁定 15 分钟


class LoginRequest(BaseModel):
    user_id: str
    password: str


def _rate_key(user_id: str) -> str:
    return f"login_fail:{user_id}"


@router.post("/login")
async def password_login(body: LoginRequest):
    """密码登录（开发模式）— 生产环境应使用微信扫码"""
    # ── 限流检查 ──
    key = _rate_key(body.user_id)
    fail_count = await redis_client.get(key)
    if fail_count is not None and int(fail_count) >= LOGIN_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"登录失败次数过多，请 {LOGIN_LOCKOUT_SECONDS // 60} 分钟后重试",
        )

    async with async_session() as db:
        # 查询用户
        result = await db.execute(
            select(User).where(User.id == body.user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            await _record_failure(key)
            raise HTTPException(status_code=401, detail="用户不存在")

        # 验证密码
        from models.config import Config
        pw_result = await db.execute(
            select(Config).where(
                Config.scope == "user",
                Config.scope_id == body.user_id,
                Config.key == "password_hash",
            )
        )
        pw_config = pw_result.scalar_one_or_none()
        if not pw_config:
            await _record_failure(key)
            raise HTTPException(status_code=401, detail="密码未设置")

        stored_hash = pw_config.value
        if not verify_password(body.password, stored_hash):
            await _record_failure(key)
            raise HTTPException(status_code=401, detail="密码错误")

    # ── 登录成功：清除失败计数 ──
    await redis_client.delete(key)

    # 查询真实角色
    user_roles = await get_user_roles(user.id)
    role_ids = list({r["role_id"] for r in user_roles})

    # 签发 JWT
    token = token_mgr.create_token(user_id=user.id, tenant_id=user.tenant_id)
    await session_mgr.cache_user_status(user.id, "active")

    # 通过 HttpOnly Cookie 传递 token（不放入 response body）
    response = Response(
        content=json.dumps({"data": {"user": {
            "id": user.id, "name": user.name,
            "tenant_id": user.tenant_id, "roles": role_ids,
        }}}),
        media_type="application/json",
        status_code=200,
    )
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=not settings.DEBUG,  # 开发模式不要求 HTTPS
        samesite="strict",
        max_age=settings.JWT_EXPIRE_DAYS * 86400,
    )
    return response

async def _record_failure(key: str):
    """记录一次登录失败，设置 TTL"""
    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, LOGIN_LOCKOUT_SECONDS)


@router.post("/qrcode")
async def create_qrcode():
    """获取微信扫码登录二维码"""
    result = await oauth.create_qr_session()
    return {"data": result}


@router.get("/qrcode/{state}/status")
async def check_qr_status(state: str):
    """轮询扫码状态"""
    result = await oauth.get_session_status(state)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Session not found")
    return {"data": result}


@router.post("/callback")
async def wechat_callback(code: str, state: str):
    """微信 OAuth 回调 — 换取 openid 后查找/创建用户并签发 JWT"""
    try:
        oauth_result = await oauth.handle_callback(code, state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"微信登录失败，请重试")

    # 查找或创建用户
    async with async_session() as db:
        user_result = await db.execute(
            select(User).where(User.wechat_openid == oauth_result["openid"])
        )
        user = user_result.scalar_one_or_none()
        if not user:
            user = User(
                id=f"u_{secrets.token_hex(8)}",
                tenant_id="default",
                wechat_openid=oauth_result["openid"],
                wechat_unionid=oauth_result.get("unionid"),
                name="微信用户",
                status="active",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

    # 签发 JWT
    token = token_mgr.create_token(user_id=user.id, tenant_id=user.tenant_id)
    await session_mgr.cache_user_status(user.id, "active")
    await oauth.set_session_token(
        state, token,
        {"id": user.id, "name": user.name, "tenant_id": user.tenant_id},
    )

    return {
        "data": {
            "status": "authenticated",
            "user": {"id": user.id, "name": user.name},
        },
    }


def _maybe_renew_token(raw_token: str, user_id: str, tenant_id: str) -> str | None:
    """检查 Token 是否即将过期，若 < 24h 则自动续签"""
    payload = token_mgr.verify_token(raw_token)
    if not payload:
        return None
    exp = payload.get("exp", 0)
    remaining = exp - time.time()
    if 0 < remaining < 86400:
        return token_mgr.create_token(user_id=user_id, tenant_id=tenant_id)
    return None


@router.post("/heartbeat")
async def heartbeat(request: Request):
    """心跳保活 — 滑动过期 + 恢复用户信息"""
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", "")

    if not user_id:
        return {"data": {"alive": False}}

    # 查询用户名（供前端恢复会话）
    user_name = user_id
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user:
            user_name = user.name

    # 检查 Token 是否即将过期 → 自动续签 Cookie
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = _maybe_renew_token(auth_header[7:], user_id, tenant_id)
    elif "token" in request.cookies:
        token = _maybe_renew_token(request.cookies["token"], user_id, tenant_id)

    # 查询真实角色
    user_roles = await get_user_roles(user_id)
    role_ids = list({r["role_id"] for r in user_roles})

    response_data = {
        "alive": True,
        "user_id": user_id,
        "user_name": user_name,
        "tenant_id": tenant_id,
        "roles": role_ids,
    }

    if token:
        from starlette.responses import JSONResponse
        resp = JSONResponse({"data": response_data})
        resp.set_cookie(
            key="token", value=token,
            httponly=True, secure=not settings.DEBUG,
            samesite="strict", max_age=settings.JWT_EXPIRE_DAYS * 86400,
        )
        return resp

    return {"data": response_data}


@router.post("/logout")
async def logout(request: Request):
    """退出登录"""
    user_id = getattr(request.state, "user_id", None)
    response = Response(
        content=json.dumps({"data": {"logged_out": True, "user_id": str(user_id)}}),
        media_type="application/json",
    )
    response.delete_cookie(key="token")
    return response
