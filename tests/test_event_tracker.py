"""测试 EventTracker — PPT 关键操作的事件追踪（字段对齐后端 schema）"""
from unittest.mock import MagicMock


class TestTrackPptGenerate:
    """PPT 生成完成事件 — 后端 schema: student_count, template, duration_seconds"""

    def test_track_generate_calls_sdk(self):
        """ppt.generate 事件 payload 匹配后端 PPTGeneratePayload"""
        from src.core.event_tracker import EventTracker

        mock_client = MagicMock()
        mock_client.tracking = MagicMock()

        tracker = EventTracker(client=mock_client)
        tracker.track_generate(
            student_count=30,
            template="basic",
            duration_seconds=120,
        )

        mock_client.tracking.track.assert_called_once()
        call_args = mock_client.tracking.track.call_args
        assert call_args[0][0] == "ppt.generate"
        payload = call_args[0][1]
        assert payload["student_count"] == 30
        assert payload["template"] == "basic"
        assert payload["duration_seconds"] == 120


class TestTrackPptImport:
    """Excel 导入事件 — 后端 schema: student_count"""

    def test_track_import_calls_sdk(self):
        """ppt.import 事件 payload 匹配后端 PPTImportPayload"""
        from src.core.event_tracker import EventTracker

        mock_client = MagicMock()
        mock_client.tracking = MagicMock()

        tracker = EventTracker(client=mock_client)
        tracker.track_import(student_count=8)

        mock_client.tracking.track.assert_called_once()
        call_args = mock_client.tracking.track.call_args
        assert call_args[0][0] == "ppt.import"
        payload = call_args[0][1]
        assert payload["student_count"] == 8


class TestTrackPptExport:
    """PPT 导出事件 — 后端 schema: format, file_size"""

    def test_track_export_calls_sdk(self):
        """ppt.export 事件 payload 匹配后端 PPTExportPayload"""
        from src.core.event_tracker import EventTracker

        mock_client = MagicMock()
        mock_client.tracking = MagicMock()

        tracker = EventTracker(client=mock_client)
        tracker.track_export(
            format="pptx",
            file_size=262144,
        )

        mock_client.tracking.track.assert_called_once()
        call_args = mock_client.tracking.track.call_args
        assert call_args[0][0] == "ppt.export"
        payload = call_args[0][1]
        assert payload["format"] == "pptx"
        assert payload["file_size"] == 262144


class TestTrackAppStart:
    """应用启动事件 — 后端 schema: version, os_info"""

    def test_track_app_start_calls_sdk(self):
        """app.start 事件 payload 匹配后端 AppStartPayload"""
        from src.core.event_tracker import EventTracker

        mock_client = MagicMock()
        mock_client.tracking = MagicMock()

        tracker = EventTracker(client=mock_client)
        tracker.track_app_start(version="1.1.1", os_info="Windows 11")

        mock_client.tracking.track.assert_called_once()
        call_args = mock_client.tracking.track.call_args
        assert call_args[0][0] == "app.start"
        payload = call_args[0][1]
        assert payload["version"] == "1.1.1"
        assert payload["os_info"] == "Windows 11"


class TestOfflineMode:
    """离线模式 — client 为 None 时不报错"""

    def test_no_error_when_client_none(self):
        """client 为 None 时 track 方法不抛异常"""
        from src.core.event_tracker import EventTracker

        tracker = EventTracker(client=None)
        tracker.track_generate(student_count=1, template="basic", duration_seconds=5)
        tracker.track_import(student_count=5)
        tracker.track_export(format="pptx", file_size=100)
        tracker.track_app_start(version="1.0", os_info="win")
