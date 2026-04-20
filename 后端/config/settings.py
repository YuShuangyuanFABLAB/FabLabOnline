import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FabLab Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fablab_platform"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # WeChat OAuth
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = ""

    # CORS
    CORS_ORIGINS: str = ""  # 逗号分隔，如 "https://fablab.com,https://admin.fablab.com"

    # API 文档
    DOCS_ENABLED: bool = True  # 生产环境应设为 False

    # Admin
    ADMIN_PASSWORD: str = ""  # 留空则使用默认密码 admin123（不安全！）

    # Token / Session
    TOKEN_EXPIRE_DAYS: int = 7
    HEARTBEAT_INTERVAL_SECONDS: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate_production(self) -> None:
        """生产环境配置校验 — 应在应用启动时调用"""
        if not self.DEBUG:
            if self.JWT_SECRET_KEY == "change-me-in-production":
                raise ValueError(
                    "JWT_SECRET_KEY 必须在生产环境中修改，不能使用默认值"
                )
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError(
                    f"JWT_SECRET_KEY 长度不足 32 字符（当前 {len(self.JWT_SECRET_KEY)} 字符）"
                )
            if not self.ADMIN_PASSWORD:
                logger.warning("ADMIN_PASSWORD 未设置，将使用默认密码")
            if self.DOCS_ENABLED:
                logger.warning("生产环境建议关闭 API 文档 (DOCS_ENABLED=false)")
            if not self.CORS_ORIGINS:
                logger.warning("CORS_ORIGINS 为空，仅允许 localhost 访问")
            wechat_has_id = bool(self.WECHAT_APP_ID)
            wechat_has_secret = bool(self.WECHAT_APP_SECRET)
            if wechat_has_id != wechat_has_secret:
                raise ValueError("微信配置必须同时填写或同时留空")


settings = Settings()
