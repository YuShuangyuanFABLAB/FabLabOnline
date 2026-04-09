"""Auth API — 扫码登录 + 会话管理"""
import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from infrastructure.database import async_session
from models.user import User
from domains.identity.wechat_oauth import WechatOAuth
from domains.identity.token_manager import TokenManager
from domains.identity.session_manager import SessionManager

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = WechatOAuth()
token_mgr = TokenManager()
session_mgr = SessionManager()


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
    oauth_result = await oauth.handle_callback(code, state)

    # 查找或创建用户
    async with async_session() as db:
        user_result = await db.execute(
            select(User).where(User.wechat_openid == oauth_result["openid"])
        )
        user = user_result.scalar_one_or_none()
        if not user:
            # 首次登录：创建用户（分配到默认 tenant，待管理员审核分配校区）
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

    # 缓存用户状态
    await session_mgr.cache_user_status(user.id, "active")

    # 更新扫码会话状态为已认证
    await oauth.set_session_token(
        state, token,
        {"id": user.id, "name": user.name, "tenant_id": user.tenant_id},
    )

    return {
        "data": {
            "status": "authenticated",
            "token": token,
            "user": {"id": user.id, "name": user.name},
        },
    }


@router.post("/heartbeat")
async def heartbeat(request: Request):
    """心跳保活 — 滑动过期：距过期 < 1 天时自动签发新 Token"""
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", "")

    # 检查 Token 是否即将过期
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        payload = token_mgr.verify_token(auth_header[7:])
        if payload:
            exp = payload.get("exp", 0)
            now = time.time()
            remaining = exp - now
            # 距过期 < 1 天 → 签发新 Token
            if 0 < remaining < 86400:
                new_token = token_mgr.create_token(user_id=user_id, tenant_id=tenant_id)
                return {"data": {"alive": True, "user_id": user_id, "token": new_token}}

    return {"data": {"alive": True, "user_id": user_id}}


@router.post("/logout")
async def logout(request: Request):
    """退出登录"""
    user_id = getattr(request.state, "user_id", None)
    return {"data": {"logged_out": True, "user_id": user_id}}
