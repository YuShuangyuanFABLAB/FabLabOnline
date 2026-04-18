"""H-audit: 审计日志应通过 BackgroundTasks 异步写入，不阻塞响应"""
import pytest
import inspect
from unittest.mock import AsyncMock, MagicMock, patch


def _make_request(tenant_id="default", user_id="admin"):
    req = MagicMock()
    req.state.tenant_id = tenant_id
    req.state.user_id = user_id
    req.client = MagicMock(host="127.0.0.1")
    req.headers = {"user-agent": "test"}
    return req


class TestAuditLogUsesBackgroundTasks:
    """写操作的审计日志应通过 BackgroundTasks 调度，不阻塞响应"""

    @patch("api.v1.campuses.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.campuses.create_campus", new_callable=AsyncMock)
    @patch("api.v1.campuses.require_permission", new_callable=AsyncMock)
    async def test_create_campus_uses_background_tasks(
        self, mock_perm, mock_create, mock_audit
    ):
        """create_campus 应接受 BackgroundTasks 参数并通过 add_task 写审计日志"""
        campus_obj = MagicMock(id="campus-1", name="Test")
        mock_create.return_value = campus_obj

        from api.v1.campuses import create_campus_endpoint, CreateCampusRequest
        from starlette.background import BackgroundTasks

        request = _make_request()
        body = CreateCampusRequest(campus_id="campus-1", name="Test")
        bg = BackgroundTasks()

        # 检查函数签名包含 BackgroundTasks
        sig = inspect.signature(create_campus_endpoint)
        param_names = list(sig.parameters.keys())
        assert "background_tasks" in param_names, (
            f"create_campus_endpoint 应接受 background_tasks 参数，实际参数: {param_names}"
        )

        await create_campus_endpoint(request, body, bg)

        # 审计日志不应直接 await — 应通过 BackgroundTasks 调度
        mock_audit.assert_not_awaited()
        # BackgroundTasks 中应有任务
        assert len(bg.tasks) > 0, (
            "create_campus 应通过 background_tasks.add_task 调度审计日志"
        )

    @patch("api.v1.campuses.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.campuses.update_campus", new_callable=AsyncMock)
    @patch("api.v1.campuses.require_permission", new_callable=AsyncMock)
    async def test_update_campus_uses_background_tasks(
        self, mock_perm, mock_update, mock_audit
    ):
        """update_campus 应通过 BackgroundTasks 写审计日志"""
        campus_obj = MagicMock(id="campus-1", name="Updated")
        mock_update.return_value = campus_obj

        from api.v1.campuses import update_campus_endpoint, UpdateCampusRequest
        from starlette.background import BackgroundTasks

        request = _make_request()
        body = UpdateCampusRequest(name="Updated")
        bg = BackgroundTasks()

        sig = inspect.signature(update_campus_endpoint)
        assert "background_tasks" in sig.parameters, (
            f"update_campus_endpoint 应接受 background_tasks 参数"
        )

        await update_campus_endpoint("campus-1", request, body, bg)
        mock_audit.assert_not_awaited()
        assert len(bg.tasks) > 0

    @patch("api.v1.campuses.write_audit_log", new_callable=AsyncMock)
    @patch("api.v1.campuses.soft_delete_campus", new_callable=AsyncMock, return_value=True)
    @patch("api.v1.campuses.require_permission", new_callable=AsyncMock)
    async def test_delete_campus_uses_background_tasks(
        self, mock_perm, mock_delete, mock_audit
    ):
        """delete_campus 应通过 BackgroundTasks 写审计日志"""
        from api.v1.campuses import delete_campus_endpoint
        from starlette.background import BackgroundTasks

        request = _make_request()
        bg = BackgroundTasks()

        sig = inspect.signature(delete_campus_endpoint)
        assert "background_tasks" in sig.parameters, (
            f"delete_campus_endpoint 应接受 background_tasks 参数"
        )

        await delete_campus_endpoint("campus-1", request, bg)
        mock_audit.assert_not_awaited()
        assert len(bg.tasks) > 0
