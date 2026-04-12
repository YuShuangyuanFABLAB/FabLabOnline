import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config.settings import settings
from infrastructure.logging import setup_logging
from infrastructure.metrics import metrics_endpoint
from api.middleware import AuthMiddleware
from api.v1.router import router as v1_router

setup_logging(debug=settings.DEBUG)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# CORS — 限制允许的源（Docker 部署通过 nginx 同源，这里为本地开发和 API 开放做准备）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.DEBUG
        if isinstance(settings.DEBUG, list)
        else ["http://localhost", "http://localhost:5173", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.include_router(v1_router)


@app.on_event("startup")
async def startup_event():
    import asyncio
    from domains.events.store import start_writer_loop, ensure_future_partitions
    start_writer_loop()
    await ensure_future_partitions()


@app.on_event("shutdown")
async def shutdown_event():
    from domains.events.store import drain_queue, _writer_task
    await drain_queue()
    if _writer_task and not _writer_task.done():
        _writer_task.cancel()
        try:
            await _writer_task
        except asyncio.CancelledError:
            pass


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
