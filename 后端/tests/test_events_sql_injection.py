"""C4: SQL 动态表名注入修复 — get_events / get_user_activity 必须查 events 表"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetEventsUsesEventsTable:
    """get_events() 必须查 events 分区表，不是 events_{tenant_id}"""

    @patch("api.v1.events.async_session")
    async def test_queries_events_table_not_per_tenant(self, mock_session_cls):
        """SQL 应查 events 表 + WHERE tenant_id = :tid，不是 f"events_{tenant_id}" """
        # mock 数据库
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_ctx

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from api.v1.events import get_events
        await get_events("default")

        # 验证 execute 被调用
        assert mock_ctx.execute.called, "get_events 应调用 db.execute"
        call_args = mock_ctx.execute.call_args
        sql_text = str(call_args[0][0])

        # 核心: SQL 必须包含 "FROM events" 不是 "FROM events_default"
        assert "FROM events " in sql_text or sql_text.strip().endswith("events"), (
            f"SQL 应查 events 表，实际: {sql_text}"
        )
        assert "events_default" not in sql_text, (
            f"SQL 不应包含动态表名 events_default，实际: {sql_text}"
        )

    @patch("api.v1.events.async_session")
    async def test_tenant_id_parameterized(self, mock_session_cls):
        """tenant_id 应通过参数化传入，而非拼接进表名"""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_ctx

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from api.v1.events import get_events
        await get_events("default")

        call_args = mock_ctx.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]

        # tenant_id 应作为参数传入
        assert "tenant_id" in params, (
            f"tenant_id 应作为参数化查询参数，实际参数: {params}"
        )
        assert params["tenant_id"] == "default", (
            f"tenant_id 参数值应为 'default'，实际: {params}"
        )


class TestGetUserActivityUsesEventsTable:
    """get_user_activity() 必须查 events 分区表"""

    @patch("api.v1.analytics.async_session")
    async def test_queries_events_table_not_per_tenant(self, mock_session_cls):
        """SQL 应查 events 表，不是 f"events_{tenant_id}" """
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_ctx

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from api.v1.analytics import get_user_activity
        await get_user_activity("default", "user1")

        assert mock_ctx.execute.called, "get_user_activity 应调用 db.execute"
        call_args = mock_ctx.execute.call_args
        sql_text = str(call_args[0][0])

        assert "FROM events " in sql_text or "FROM events\n" in sql_text, (
            f"SQL 应查 events 表，实际: {sql_text}"
        )
        assert "events_default" not in sql_text, (
            f"SQL 不应包含动态表名 events_default，实际: {sql_text}"
        )

    @patch("api.v1.analytics.async_session")
    async def test_tenant_id_parameterized(self, mock_session_cls):
        """tenant_id 应通过 WHERE 参数化传入"""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_ctx

        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_ctx.execute = AsyncMock(return_value=mock_result)

        from api.v1.analytics import get_user_activity
        await get_user_activity("default", "user1")

        call_args = mock_ctx.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1]

        assert "tenant_id" in params, (
            f"tenant_id 应作为参数化查询参数，实际参数: {params}"
        )


class TestInvalidTenantIdRejected:
    """非法 tenant_id 仍应被拒绝"""

    async def test_sql_injection_tenant_id_rejected(self):
        """包含特殊字符的 tenant_id 应被拒绝"""
        from api.v1.events import get_events
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_events("'; DROP TABLE users;--")
        assert exc_info.value.status_code == 400

    async def test_get_user_activity_rejects_bad_tenant(self):
        from api.v1.analytics import get_user_activity
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_user_activity("'; DROP TABLE users;--", "user1")
        assert exc_info.value.status_code == 400
