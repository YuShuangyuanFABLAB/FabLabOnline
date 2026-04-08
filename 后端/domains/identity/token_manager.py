from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError

from config.settings import settings


class TokenManager:
    """JWT Token 签发与验证"""

    def __init__(
        self,
        secret: str | None = None,
        algorithm: str | None = None,
        expire_seconds: int | None = None,
    ):
        self.secret = secret or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        if expire_seconds is not None:
            self.expire = timedelta(seconds=expire_seconds)
        else:
            self.expire = timedelta(days=settings.JWT_EXPIRE_DAYS)

    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        extra: dict[str, Any] | None = None,
    ) -> str:
        """签发 JWT，payload 包含 sub/tenant_id/iat/exp + 可选 extra"""
        now = datetime.now(timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": now + self.expire,
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """验证 JWT，返回 payload 或 None"""
        if not token:
            return None
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except (JWTError, Exception):
            return None
