"""测试角色删除保护 — M6 TDD"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestDeleteRole:
    """DELETE /roles/{role_id} 必须保护系统角色"""

    @pytest.mark.asyncio
    async def test_delete_non_system_role_succeeds(self):
        """删除非系统角色成功"""
        from api.v1.roles import delete_role

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"

        mock_role = MagicMock()
        mock_role.id = "teacher"
        mock_role.is_system = False

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_role)
        ))
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.get_policy") as mock_policy:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_policy_inst = MagicMock()
            mock_policy_inst.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = mock_policy_inst

            result = await delete_role("teacher", request)
            assert result["success"] is True
            mock_db.delete.assert_called_once_with(mock_role)

    @pytest.mark.asyncio
    async def test_delete_system_role_forbidden(self):
        """删除系统角色返回 403"""
        from api.v1.roles import delete_role
        from fastapi import HTTPException

        request = MagicMock()
        request.state.user_id = "admin_001"
        request.state.tenant_id = "default"

        mock_role = MagicMock()
        mock_role.id = "super_admin"
        mock_role.is_system = True

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_role)
        ))

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.get_policy") as mock_policy:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_policy_inst = MagicMock()
            mock_policy_inst.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = mock_policy_inst

            with pytest.raises(HTTPException) as exc_info:
                await delete_role("super_admin", request)
            assert exc_info.value.status_code == 403
            assert "系统角色" in str(exc_info.value.detail)
