"""测试 consumer 幂等 + analytics dashboard + API 401"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date


class TestEventConsumer:
    @pytest.mark.asyncio
    async def test_is_processed_new_event(self):
        """新 event_id → is_processed 返回 False"""
        from domains.events.consumer import is_processed
        with patch("domains.events.consumer.redis_client") as mock_redis:
            mock_redis.sadd = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock()
            result = await is_processed("test_consumer", "evt_1")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_processed_duplicate_event(self):
        """重复 event_id → is_processed 返回 True"""
        from domains.events.consumer import is_processed
        with patch("domains.events.consumer.redis_client") as mock_redis:
            mock_redis.sadd = AsyncMock(return_value=0)
            result = await is_processed("test_consumer", "evt_1")
            assert result is True

    @pytest.mark.asyncio
    async def test_ack_events_version_mismatch(self):
        """乐观锁版本不匹配 → ConcurrencyError"""
        from domains.events.consumer import ack_events, ConcurrencyError
        with patch("domains.events.consumer.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_result = MagicMock()
            mock_result.rowcount = 0
            mock_db.execute.return_value = mock_result

            with pytest.raises(ConcurrencyError):
                await ack_events("consumer1", 100, 0)


class TestAnalyticsDashboard:
    @pytest.mark.asyncio
    async def test_update_daily_stat_upserts(self):
        """update_daily_stat 应执行 UPSERT"""
        from domains.analytics.dashboard import update_daily_stat
        with patch("domains.analytics.dashboard.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await update_daily_stat("t1", "c1", "ppt.generate")
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()


class TestEventsAPI:
    @pytest.mark.asyncio
    async def test_batch_report_without_auth_returns_401(self, client):
        resp = await client.post("/api/v1/events/batch", json=[])
        assert resp.status_code == 401


class TestAnalyticsAPI:
    @pytest.mark.asyncio
    async def test_dashboard_without_auth_returns_401(self, client):
        resp = await client.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 401
