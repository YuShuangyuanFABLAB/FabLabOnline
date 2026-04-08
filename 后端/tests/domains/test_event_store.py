"""测试事件入队 + 批量写入"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from domains.events.store import enqueue_events, get_event_queue


class TestEnqueueEvents:
    @pytest.mark.asyncio
    async def test_enqueue_valid_events(self):
        """有效事件应入队"""
        queue = get_event_queue()
        while not queue.empty():
            queue.get_nowait()

        events = [
            {"event_type": "app.start", "payload": {"version": "1.0", "os_info": "win"}},
        ]
        result = await enqueue_events(events, "t1", "u1", "app1")
        assert result["enqueued"] == 1
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_enqueue_unknown_event_type_returns_error(self):
        """未知事件类型应返回错误"""
        events = [
            {"event_type": "unknown.type", "payload": {}},
        ]
        result = await enqueue_events(events, "t1", "u1", "app1")
        assert result["enqueued"] == 0
        assert len(result["errors"]) == 1
        assert "Unknown event type" in result["errors"][0]["error"]

    @pytest.mark.asyncio
    async def test_enqueue_invalid_payload_returns_error(self):
        """缺少必填字段应返回错误"""
        events = [
            {"event_type": "ppt.generate", "payload": {"template": "basic"}},
        ]
        result = await enqueue_events(events, "t1", "u1", "app1")
        assert result["enqueued"] == 0
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_enqueue_mix_valid_and_invalid(self):
        """混合有效/无效事件：部分入队"""
        events = [
            {"event_type": "app.start", "payload": {"version": "1.0", "os_info": "win"}},
            {"event_type": "unknown.type", "payload": {}},
        ]
        result = await enqueue_events(events, "t1", "u1", "app1")
        assert result["enqueued"] == 1
        assert len(result["errors"]) == 1


class TestEventQueue:
    def test_get_event_queue_returns_queue(self):
        """get_event_queue 应返回 Queue"""
        import asyncio
        q = get_event_queue()
        assert isinstance(q, asyncio.Queue)
