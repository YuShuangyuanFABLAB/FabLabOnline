"""AuthMiddleware — JWT 校验 + 豁免路径"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from domains.identity.token_manager import TokenManager
from domains.identity.session_manager import SessionManager

# 不需要认证的路径前缀
EXEMPT_PATHS = (
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/qrcode",
    "/api/v1/auth/callback",
    "/api/v1/auth/login",
    "/api/v1/auth/totp/verify",
)

_token_manager = TokenManager()
_session_manager = SessionManager()


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 校验中间件。

    - EXEMPT_PATHS 中的路径直接放行
    - 其他路径需要 Bearer token
    - 校验通过后将 user_id / tenant_id 写入 request.state
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 豁免路径
        if path in EXEMPT_PATHS or any(path.startswith(p) for p in EXEMPT_PATHS):
            return await call_next(request)

        # 提取 token — 支持 Authorization header 和 HttpOnly Cookie
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        elif "token" in request.cookies:
            token = request.cookies["token"]

        if not token:
            return JSONResponse(status_code=401, content={"detail": "未提供认证凭据"})
        payload = _token_manager.verify_token(token)
        if payload is None:
            return JSONResponse(status_code=401, content={"detail": "无效或过期的凭据"})

        user_id = payload.get("sub")
        if not user_id:
            return JSONResponse(status_code=401, content={"detail": "凭据缺少用户标识"})

        # 检查会话是否仍然有效
        if not await _session_manager.is_session_valid(user_id):
            return JSONResponse(status_code=401, content={"detail": "会话已失效"})

        # 写入 request.state 供后续 handler 使用
        request.state.user_id = user_id
        request.state.tenant_id = payload.get("tenant_id", "")
        request.state.app_id = request.headers.get("X-App-ID", "unknown")

        return await call_next(request)
