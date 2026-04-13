from pydantic_settings import BaseSettings


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


settings = Settings()
