"""通用限流中间件 — 基于 IP 的令牌桶"""
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于 IP 的滑动窗口限流"""

    def __init__(self, app, requests_per_minute: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limit = requests_per_minute
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_limited(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        hits = self._hits[key]
        # 清理过期记录
        while hits and hits[0] < cutoff:
            hits.pop(0)
        if len(hits) >= self.limit:
            return True
        hits.append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        # 健康检查和内部路径不限流
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        key = self._key(request)
        if self._is_limited(key):
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )
        return await call_next(request)
