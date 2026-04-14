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

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)

# CORS — 使用 CORS_ORIGINS 配置项，生产环境填实际域名
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not _cors_origins:
    _cors_origins = ["http://localhost", "http://localhost:5173", "http://localhost:80"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)
app.include_router(v1_router)


@app.on_event("startup")
async def startup_event():
    settings.validate_production()
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
