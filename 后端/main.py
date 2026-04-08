from fastapi import FastAPI
from sqlalchemy import text

from config.settings import settings
from infrastructure.logging import setup_logging
from infrastructure.metrics import metrics_endpoint
from api.middleware import AuthMiddleware
from api.v1.router import router as v1_router

setup_logging(debug=settings.DEBUG)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.add_middleware(AuthMiddleware)
app.include_router(v1_router)


@app.on_event("startup")
async def startup_event():
    import asyncio
    from domains.events.store import _event_writer_loop
    asyncio.create_task(_event_writer_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    checks = {"db": False, "redis": False}

    try:
        from infrastructure.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception:
        pass

    try:
        from infrastructure.redis import redis_client
        await redis_client.ping()
        checks["redis"] = True
    except Exception:
        pass

    if all(checks.values()):
        return {"status": "ready", **checks}
    return {"status": "not_ready", **checks}


@app.get("/metrics")
async def metrics():
    return metrics_endpoint()
