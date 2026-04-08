"""Analytics dashboard — 预聚合 + 查询"""
from datetime import date, timedelta

import structlog
from sqlalchemy import text, select

from infrastructure.database import async_session
from models.daily_usage_stats import DailyUsageStats

logger = structlog.get_logger()


async def update_daily_stat(tenant_id: str, campus_id: str | None, event_type: str):
    """事件消费者调用：UPSERT 预聚合表"""
    async with async_session() as db:
        await db.execute(text("""
            INSERT INTO daily_usage_stats (date, tenant_id, campus_id, event_type, count)
            VALUES (CURRENT_DATE, :tenant_id, :campus_id, :event_type, 1)
            ON CONFLICT (date, tenant_id, campus_id, event_type)
            DO UPDATE SET count = count + 1
        """), {"tenant_id": tenant_id, "campus_id": campus_id, "event_type": event_type})
        await db.commit()


async def get_dashboard_data(tenant_id: str, days: int = 7) -> dict:
    """看板数据：从预聚合表查询"""
    start_date = date.today() - timedelta(days=days)
    async with async_session() as db:
        result = await db.execute(text("""
            SELECT event_type, SUM(count) as total
            FROM daily_usage_stats
            WHERE tenant_id = :tenant_id AND date >= :start_date
            GROUP BY event_type
            ORDER BY total DESC
        """), {"tenant_id": tenant_id, "start_date": start_date})
        event_summary = [{"event_type": r[0], "total": r[1]} for r in result.all()]

        today_result = await db.execute(text("""
            SELECT COALESCE(SUM(count), 0) as today_total
            FROM daily_usage_stats
            WHERE tenant_id = :tenant_id AND date = CURRENT_DATE
        """), {"tenant_id": tenant_id})
        today_total = today_result.scalar()

        active_result = await db.execute(text("""
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM events
            WHERE tenant_id = :tenant_id
              AND timestamp >= CURRENT_DATE
              AND timestamp < CURRENT_DATE + INTERVAL '1 day'
        """), {"tenant_id": tenant_id})
        active_users = active_result.scalar() or 0

        return {
            "today_events": today_total,
            "active_users": active_users,
            "event_summary": event_summary,
            "period_days": days,
        }


async def get_usage_by_campus(tenant_id: str, start_date: date, end_date: date) -> list[dict]:
    """按校区统计使用量"""
    async with async_session() as db:
        result = await db.execute(text("""
            SELECT campus_id, event_type, SUM(count) as total
            FROM daily_usage_stats
            WHERE tenant_id = :tenant_id
              AND date >= :start_date AND date <= :end_date
            GROUP BY campus_id, event_type
            ORDER BY total DESC
        """), {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date})
        return [{"campus_id": r[0], "event_type": r[1], "total": r[2]} for r in result.all()]
