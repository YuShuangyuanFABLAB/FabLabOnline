"""事件批量上报大小限制测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBatchSizeLimit:
    """批量上报事件必须有上限"""

    @patch("api.v1.events.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.events.enqueue_events", new_callable=AsyncMock)
    async def test_batch_within_limit_accepted(self, mock_enqueue, mock_audit):
        """100 条以内应正常接受"""
        mock_enqueue.return_value = {"enqueued": 50, "errors": []}

        from api.v1.events import batch_report
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "user1"
        request.state.app_id = "app1"

        events = [{"type": "click", "payload": {}} for _ in range(50)]
        from starlette.background import BackgroundTasks
        result = await batch_report(request, events, BackgroundTasks())
        assert result["success"] is True

    @patch("api.v1.events.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.events.enqueue_events", new_callable=AsyncMock)
    async def test_batch_over_limit_rejected(self, mock_enqueue, mock_audit):
        """超过 100 条应返回 400"""
        from api.v1.events import batch_report
        from fastapi import HTTPException
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "user1"
        request.state.app_id = "app1"

        events = [{"type": "click", "payload": {}} for _ in range(101)]
        from starlette.background import BackgroundTasks
        with pytest.raises(HTTPException) as exc_info:
            await batch_report(request, events, BackgroundTasks())
        assert exc_info.value.status_code == 400
        mock_enqueue.assert_not_called()

    @patch("api.v1.events.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.events.enqueue_events", new_callable=AsyncMock)
    async def test_batch_exactly_100_accepted(self, mock_enqueue, mock_audit):
        """恰好 100 条应正常接受"""
        mock_enqueue.return_value = {"enqueued": 100, "errors": []}

        from api.v1.events import batch_report
        request = MagicMock()
        request.state.tenant_id = "default"
        request.state.user_id = "user1"
        request.state.app_id = "app1"

        events = [{"type": "click", "payload": {}} for _ in range(100)]
        from starlette.background import BackgroundTasks
        result = await batch_report(request, events, BackgroundTasks())
        assert result["success"] is True
