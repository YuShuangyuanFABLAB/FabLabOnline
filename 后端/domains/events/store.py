"""事件写入缓冲队列 + 批量入库"""
import asyncio
import json
import structlog
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from infrastructure.database import async_session
from domains.events.schema import validate_event

logger = structlog.get_logger()

# ─── 写入缓冲队列 ───────────────────────────────────────────────
_event_queue: asyncio.Queue | None = None
BATCH_SIZE = 100
FLUSH_INTERVAL = 1.0  # 秒
_writer_task: asyncio.Task | None = None


def get_event_queue() -> asyncio.Queue:
    global _event_queue
    if _event_queue is None:
        _event_queue = asyncio.Queue()
    return _event_queue


def start_writer_loop() -> asyncio.Task:
    """启动事件写入后台任务，返回 Task 引用"""
    global _writer_task
    _writer_task = asyncio.create_task(_event_writer_loop())
    return _writer_task


async def drain_queue():
    """排空队列中剩余事件（shutdown 时调用）"""
    queue = get_event_queue()
    batch = []
    while not queue.empty():
        try:
            batch.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    if batch:
        await _bulk_insert(batch)


async def enqueue_events(
    events_data: list[dict], tenant_id: str, user_id: str, app_id: str
) -> dict:
    """API 层调用：校验 payload 后放入内存队列（非阻塞，毫秒级返回）"""
    enqueued = 0
    errors = []
    for ed in events_data:
        try:
            validated_payload = validate_event(ed["event_type"], ed.get("payload", {}))
            event = {
                "event_id": ed.get("event_id", str(uuid4())),
                "event_type": ed["event_type"],
                "event_version": ed.get("event_version", 1),
                "event_source": ed.get("event_source", "client"),
                "timestamp": ed.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "tenant_id": tenant_id,
                "campus_id": ed.get("campus_id"),
                "user_id": user_id,
                "app_id": app_id,
                "payload": json.dumps(validated_payload),
                "trace_id": ed.get("trace_id"),
            }
            await get_event_queue().put(event)
            enqueued += 1
        except ValueError as e:
            errors.append({"event_type": ed.get("event_type"), "error": str(e)})
    return {"enqueued": enqueued, "errors": errors}


async def _event_writer_loop():
    """后台 task：每 1 秒或攒够 100 条后批量 INSERT"""
    queue = get_event_queue()
    while True:
        batch = []
        try:
            event = await asyncio.wait_for(queue.get(), timeout=FLUSH_INTERVAL)
            batch.append(event)
            while len(batch) < BATCH_SIZE:
                try:
                    event = queue.get_nowait()
                    batch.append(event)
                except asyncio.QueueEmpty:
                    break
        except asyncio.TimeoutError:
            pass

        if batch:
            await _bulk_insert(batch)


async def _bulk_insert(batch: list[dict]):
    """批量 INSERT"""
    try:
        async with async_session() as db:
            values_clause = ", ".join([
                f"(:event_id_{i}, :event_type_{i}, :event_version_{i}, :event_source_{i}, "
                f":timestamp_{i}, :tenant_id_{i}, :campus_id_{i}, :user_id_{i}, :app_id_{i}, "
                f":payload_{i}::jsonb, :trace_id_{i})"
                for i in range(len(batch))
            ])
            params = {}
            for i, e in enumerate(batch):
                params.update({
                    f"event_id_{i}": e["event_id"],
                    f"event_type_{i}": e["event_type"],
                    f"event_version_{i}": e["event_version"],
                    f"event_source_{i}": e["event_source"],
                    f"timestamp_{i}": e["timestamp"],
                    f"tenant_id_{i}": e["tenant_id"],
                    f"campus_id_{i}": e["campus_id"],
                    f"user_id_{i}": e["user_id"],
                    f"app_id_{i}": e["app_id"],
                    f"payload_{i}": e["payload"],
                    f"trace_id_{i}": e["trace_id"],
                })

            await db.execute(text(f"""
                INSERT INTO events (event_id, event_type, event_version, event_source,
                    timestamp, tenant_id, campus_id, user_id, app_id, payload, trace_id)
                VALUES {values_clause}
            """), params)
            await db.commit()
            logger.info("bulk_insert_success", count=len(batch))
    except Exception as e:
        if "no partition" in str(e).lower():
            for e_data in batch:
                try:
                    await _single_insert_with_partition(e_data)
                except Exception as single_err:
                    logger.error("event_insert_failed", event_id=e_data["event_id"], error=str(single_err))
        else:
            logger.error("bulk_insert_failed", count=len(batch), error=str(e))


async def _single_insert_with_partition(event: dict):
    """单条插入 + 自动创建分区（兜底）"""
    async with async_session() as db:
        try:
            await db.execute(text("""
                INSERT INTO events (event_id, event_type, event_version, event_source,
                    timestamp, tenant_id, campus_id, user_id, app_id, payload, trace_id)
                VALUES (:event_id, :event_type, :event_version, :event_source,
                    :timestamp, :tenant_id, :campus_id, :user_id, :app_id, :payload::jsonb, :trace_id)
            """), event)
            await db.commit()
        except Exception:
            await _ensure_current_month_partition(db, event["timestamp"])
            await db.execute(text("""
                INSERT INTO events (event_id, event_type, event_version, event_source,
                    timestamp, tenant_id, campus_id, user_id, app_id, payload, trace_id)
                VALUES (:event_id, :event_type, :event_version, :event_source,
                    :timestamp, :tenant_id, :campus_id, :user_id, :app_id, :payload::jsonb, :trace_id)
            """), event)
            await db.commit()


async def _ensure_current_month_partition(db, timestamp_str: str):
    """自动创建当月分区"""
    try:
        ts = datetime.fromisoformat(timestamp_str) if isinstance(timestamp_str, str) else timestamp_str
    except Exception:
        ts = datetime.now(timezone.utc)

    year, month = ts.year, ts.month
    partition_name = f"events_{year}_{month:02d}"
    end_month = month + 1 if month < 12 else 1
    end_year = year if month < 12 else year + 1

    await db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF events
        FOR VALUES FROM ('{year}-{month:02d}-01') TO ('{end_year}-{end_month:02d}-01')
    """))
    logger.info("auto_created_partition", partition=partition_name)


async def ensure_future_partitions():
    """启动时预创建未来 3 个月分区（防止首次插入失败）"""
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        for offset in range(0, 4):  # 当月 + 未来 3 个月
            m = now.month + offset
            y = now.year
            while m > 12:
                m -= 12
                y += 1
            partition_name = f"events_{y}_{m:02d}"
            end_m = m + 1 if m < 12 else 1
            end_y = y if m < 12 else y + 1
            await db.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {partition_name} PARTITION OF events
                FOR VALUES FROM ('{y}-{m:02d}-01') TO ('{end_y}-{end_m:02d}-01')
            """))
        await db.commit()
        logger.info("future_partitions_ensured")
