# -*- coding: utf-8 -*-
"""
事件追踪模块
在 PPT 关键操作点埋入事件追踪，通过 SDK 上报到服务端
Payload 字段严格对齐后端 EVENT_SCHEMAS（schema.py）
"""

import logging
logger = logging.getLogger(__name__)


class EventTracker:
    """PPT 操作事件追踪器"""

    def __init__(self, client=None):
        """
        Args:
            client: FablabClient 实例，None 表示离线模式
        """
        self.client = client

    def track_generate(self, *, student_count: int, template: str, duration_seconds: int) -> None:
        """追踪 PPT 生成事件 — PPTGeneratePayload"""
        self._track("ppt.generate", {
            "student_count": student_count,
            "template": template,
            "duration_seconds": duration_seconds,
        })

    def track_import(self, *, student_count: int) -> None:
        """追踪 Excel 导入事件 — PPTImportPayload"""
        self._track("ppt.import", {
            "student_count": student_count,
        })

    def track_export(self, *, format: str, file_size: int) -> None:
        """追踪 PPT 导出事件 — PPTExportPayload"""
        self._track("ppt.export", {
            "format": format,
            "file_size": file_size,
        })

    def track_app_start(self, *, version: str, os_info: str) -> None:
        """追踪应用启动事件 — AppStartPayload"""
        self._track("app.start", {
            "version": version,
            "os_info": os_info,
        })

    def _track(self, event_type: str, payload: dict) -> None:
        """发送追踪事件（离线模式下静默跳过）"""
        if self.client is None:
            return
        try:
            self.client.tracking.track(event_type, payload)
        except Exception as e:
            logger.warning(f"事件追踪失败 ({event_type}): {e}")
