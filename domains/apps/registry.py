"""应用注册 — 查询 / 注册 / 校验"""
import hashlib
import secrets

from sqlalchemy import select

from infrastructure.database import async_session
from models.app import App


async def list_apps() -> list[dict]:
    """列出所有活跃应用"""
    async with async_session() as db:
        result = await db.execute(select(App).where(App.status == "active"))
        apps = result.scalars().all()
        return [
            {"id": a.id, "name": a.name, "app_key": a.app_key, "status": a.status}
            for a in apps
        ]


async def register_app(app_id: str, name: str, app_key: str) -> dict:
    """注册新应用，返回基本信息 + app_secret（仅此一次可见）"""
    raw_secret = secrets.token_hex(32)
    secret_hash = hashlib.sha256(raw_secret.encode()).hexdigest()

    async with async_session() as db:
        app = App(
            id=app_id,
            name=name,
            app_key=app_key,
            app_secret_hash=secret_hash,
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)
        return {
            "id": app.id,
            "name": app.name,
            "app_key": app.app_key,
            "app_secret": raw_secret,
        }


async def verify_app(app_key: str, app_secret: str) -> App | None:
    """校验 app_key + app_secret，返回 App 对象或 None"""
    secret_hash = hashlib.sha256(app_secret.encode()).hexdigest()
    async with async_session() as db:
        result = await db.execute(
            select(App).where(
                App.app_key == app_key,
                App.app_secret_hash == secret_hash,
                App.status == "active",
            )
        )
        return result.scalar_one_or_none()
