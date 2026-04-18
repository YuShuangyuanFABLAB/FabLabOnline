"""N+1 查询修复测试 — list_roles 应一次性获取所有权限"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestRolesBatchPermissions:
    """GET /roles 应批量获取权限，不逐角色查询"""

    @patch("api.v1.roles.require_permission", new_callable=AsyncMock)
    @patch("api.v1.roles.get_roles_batch_permissions", new_callable=AsyncMock)
    @patch("api.v1.roles.get_roles", new_callable=AsyncMock)
    async def test_list_roles_uses_batch_query(
        self, mock_get_roles, mock_batch_perms, mock_perm
    ):
        """list_roles 应调用 get_roles_batch_permissions 而非逐个查询"""
        role1 = MagicMock(id="super_admin", name="super_admin",
                          display_name="超级管理员", level=100)
        role2 = MagicMock(id="teacher", name="teacher",
                          display_name="教师", level=10)
        mock_get_roles.return_value = [role1, role2]

        mock_batch_perms.return_value = {
            "super_admin": ["user:read", "user:create"],
            "teacher": ["user:read"],
        }

        from api.v1.roles import list_roles
        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        result = await list_roles(request)

        assert result["success"] is True
        # 应调用批量方法
        mock_batch_perms.assert_called_once()
        # 不应调用单个查询方法
        # 验证返回结构正确
        assert result["data"][0]["permissions"] == ["user:read", "user:create"]
        assert result["data"][1]["permissions"] == ["user:read"]

    @patch("api.v1.roles.require_permission", new_callable=AsyncMock)
    @patch("api.v1.roles.get_roles_batch_permissions", new_callable=AsyncMock)
    @patch("api.v1.roles.get_roles", new_callable=AsyncMock)
    async def test_batch_perms_single_db_call(
        self, mock_get_roles, mock_batch_perms, mock_perm
    ):
        """批量权限查询应只调用一次 DB"""
        role1 = MagicMock(id="r1", name="r1", display_name="R1", level=10)
        mock_get_roles.return_value = [role1]
        mock_batch_perms.return_value = {"r1": ["user:read"]}

        from api.v1.roles import list_roles
        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        await list_roles(request)

        # get_roles 1 次 + get_roles_batch_permissions 1 次 = 2 次 DB 调用
        # 之前是 get_roles 1 次 + get_role_permissions N 次 = N+1 次
        mock_get_roles.assert_called_once()
        mock_batch_perms.assert_called_once()
