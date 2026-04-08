"""测试 EventReporter — JSONL 本地存储 + 批量上报 + 熔断器"""
import json
import time
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestTrackWritesToLocal:
    """track() 写入本地 JSONL"""

    def test_track_creates_jsonl_with_pending_status(self, tmp_path):
        """track() 在本地 JSONL 写入 status=pending 的记录"""
        local_file = tmp_path / "pending_events.jsonl"

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=MagicMock(), local_file=local_file)
        reporter.track("app.start", {"version": "1.0", "os_info": "win"})

        assert local_file.exists()
        lines = local_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["status"] == "pending"
        assert record["event"]["event_type"] == "app.start"
        assert record["event"]["payload"]["version"] == "1.0"


class TestFlushBatchUpload:
    """flush() 批量上报"""

    def test_flush_calls_api_and_marks_sent(self, tmp_path):
        """flush() 调用 API 批量上报后标记为 sent"""
        local_file = tmp_path / "pending_events.jsonl"
        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(return_value={"success": True})

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=2)

        reporter.track("app.start", {"version": "1.0", "os_info": "win"})
        reporter.track("ppt.generate", {"student_count": 30, "template": "basic", "duration_seconds": 120})

        # After 2 events (batch_size), flush should have been triggered
        assert mock_client.api.batch_report.called

    @pytest.mark.asyncio
    async def test_flush_resets_failures_on_success(self, tmp_path):
        """flush 成功后重置连续失败计数"""
        local_file = tmp_path / "pending_events.jsonl"
        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(return_value={"success": True})

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=1)
        reporter._consecutive_failures = 3

        reporter.track("app.start", {"version": "1.0", "os_info": "win"})
        assert reporter._consecutive_failures == 0


class TestCircuitBreaker:
    """熔断器：连续 5 次失败后暂停 5 分钟"""

    def test_circuit_breaker_opens_after_5_failures(self, tmp_path):
        """连续 5 次 API 失败后熔断器断开"""
        local_file = tmp_path / "pending_events.jsonl"
        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(side_effect=Exception("Network error"))

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=1)

        for i in range(5):
            reporter.track("app.start", {"version": "1.0", "os_info": "win"})

        assert reporter._consecutive_failures >= 5
        assert reporter._circuit_open_until > 0

    def test_circuit_breaker_blocks_flush_when_open(self, tmp_path):
        """熔断器断开时 flush 不调用 API"""
        local_file = tmp_path / "pending_events.jsonl"
        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(return_value={"success": True})

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=1)

        # Manually open the circuit breaker
        reporter._circuit_open_until = time.time() + 300  # 5 min from now
        reporter._consecutive_failures = 5

        reporter.track("app.start", {"version": "1.0", "os_info": "win"})

        # API should NOT have been called
        mock_client.api.batch_report.assert_not_called()

    def test_circuit_breaker_resets_after_cooldown(self, tmp_path):
        """冷却期后熔断器自动重置"""
        local_file = tmp_path / "pending_events.jsonl"
        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(return_value={"success": True})

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=1)

        # Set circuit open in the past (cooldown expired)
        reporter._circuit_open_until = time.time() - 1
        reporter._consecutive_failures = 5

        reporter.track("app.start", {"version": "1.0", "os_info": "win"})

        # Should have reset and attempted API call
        assert reporter._consecutive_failures == 0


class TestReplayPending:
    """replay_pending() 重传本地 pending 事件"""

    @pytest.mark.asyncio
    async def test_replay_sends_pending_events(self, tmp_path):
        """replay_pending() 读取本地 pending 事件并上报"""
        local_file = tmp_path / "pending_events.jsonl"
        # Pre-populate with pending events
        events = [
            {"event": {"event_type": "app.start", "payload": {"version": "1.0", "os_info": "win"}}, "status": "pending"},
            {"event": {"event_type": "app.error", "payload": {"error_type": "ValueError", "message": "test"}}, "status": "pending"},
        ]
        lines = [json.dumps(e, ensure_ascii=False) for e in events]
        local_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        mock_client = MagicMock()
        mock_client.api = MagicMock()
        mock_client.api.batch_report = AsyncMock(return_value={"success": True})

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=mock_client, local_file=local_file, batch_size=10)
        await reporter.replay_pending()

        assert mock_client.api.batch_report.called


class TestFileRotation:
    """文件大小超限自动 rotation"""

    def test_rotate_keeps_latest_half(self, tmp_path):
        """rotation 保留最新一半记录"""
        local_file = tmp_path / "pending_events.jsonl"
        # Write 10 records
        records = []
        for i in range(10):
            record = {"event": {"event_type": "app.start", "payload": {"i": i}}, "status": "pending"}
            records.append(json.dumps(record))
        local_file.write_text("\n".join(records) + "\n", encoding="utf-8")

        from fablab_sdk.tracking import EventReporter
        reporter = EventReporter(client=MagicMock(), local_file=local_file)

        # Trigger rotation
        reporter._rotate_local_file()

        lines = local_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 5
        # Should keep the LAST 5 (i=5..9)
        first = json.loads(lines[0])
        assert first["event"]["payload"]["i"] == 5
