"""测试优雅关闭 — M7 TDD"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def reset_queue():
    """每个测试前重置事件队列状态"""
    import domains.events.store as store
    store._event_queue = None
    store._writer_task = None
    yield
    store._event_queue = None
    store._writer_task = None


class TestGracefulShutdown:
    """M7: 后端必须优雅关闭，刷新事件队列"""

    @pytest.mark.asyncio
    async def test_drain_queue_flushes_remaining_events(self):
        """shutdown 时排空队列中剩余事件"""
        from domains.events.store import drain_queue, get_event_queue

        queue = get_event_queue()
        # 放入 3 个测试事件
        for i in range(3):
            await queue.put({"event_id": f"test-{i}", "event_type": "test"})

        with patch("domains.events.store._bulk_insert", new_callable=AsyncMock) as mock_insert:
            await drain_queue()
            # 应该调用了 _bulk_insert 来刷新
            mock_insert.assert_called_once()
            batch = mock_insert.call_args[0][0]
            assert len(batch) == 3

    @pytest.mark.asyncio
    async def test_shutdown_handler_cancels_background_task(self):
        """shutdown 处理器取消后台任务"""
        from main import startup_event

        # 模拟 startup 创建了后台任务（跳过生产环境校验）
        with patch("config.settings.Settings.validate_production"), \
             patch("domains.events.store.ensure_future_partitions", new_callable=AsyncMock):
            await startup_event()

        # 验证后台任务存在
        tasks = [t for t in asyncio.all_tasks() if "event_writer" in t.get_coro().__name__]
        assert len(tasks) >= 1, "event_writer task should be running"

        # 调用 shutdown
        from main import shutdown_event
        with patch("domains.events.store.drain_queue", new_callable=AsyncMock):
            await shutdown_event()

        # 短暂等待任务被取消
        await asyncio.sleep(0.1)
        tasks_after = [t for t in asyncio.all_tasks() if "event_writer" in t.get_coro().__name__]
        assert len(tasks_after) == 0, "event_writer task should be cancelled"
