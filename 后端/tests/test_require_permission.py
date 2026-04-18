"""权限检查辅助函数 require_permission 测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


class TestRequirePermission:
    """require_permission 应封装重复的权限检查样板代码"""

    async def test_raises_403_on_denied(self):
        """无权限时应抛出 HTTPException 403"""
        from domains.access.policy import require_permission

        request = MagicMock()
        request.state.user_id = "teacher1"
        request.state.tenant_id = "default"

        with patch("domains.access.policy.get_policy") as mock_get_policy:
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=False)
            mock_get_policy.return_value = policy

            with pytest.raises(HTTPException) as exc_info:
                await require_permission(request, "create", "user")
            assert exc_info.value.status_code == 403

    async def test_passes_on_allowed(self):
        """有权限时应正常返回，不抛异常"""
        from domains.access.policy import require_permission

        request = MagicMock()
        request.state.user_id = "admin1"
        request.state.tenant_id = "default"

        with patch("domains.access.policy.get_policy") as mock_get_policy:
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_get_policy.return_value = policy

            # 不应抛出异常
            await require_permission(request, "read", "user")

    async def test_passes_correct_params(self):
        """应正确传递 user_id, action, resource, PermissionContext"""
        from domains.access.policy import require_permission, PermissionContext

        request = MagicMock()
        request.state.user_id = "admin1"
        request.state.tenant_id = "default"

        with patch("domains.access.policy.get_policy") as mock_get_policy:
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_get_policy.return_value = policy

            await require_permission(request, "update", "campus")

            policy.check_permission.assert_called_once()
            call_args = policy.check_permission.call_args
            assert call_args[0][0] == "admin1"   # user_id
            assert call_args[0][1] == "update"    # action
            assert call_args[0][2] == "campus"    # resource
            ctx = call_args[0][3]
            assert isinstance(ctx, PermissionContext)
            assert ctx.tenant_id == "default"
