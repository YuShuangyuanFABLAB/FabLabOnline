"""Phase 4C 前后端对齐测试 — H6/H5/H4"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════
# H6: GET /roles 返回 permissions 字段
# ═══════════════════════════════════════════════════════════════


class TestRolesReturnPermissions:
    """GET /roles 应返回每个角色的 permissions 数组"""

    @pytest.mark.asyncio
    async def test_list_roles_includes_permissions(self):
        """每个角色应附带 permissions: string[]"""
        from api.v1.roles import list_roles

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        # Mock 角色
        role_super = MagicMock()
        role_super.id = "super_admin"
        role_super.name = "super_admin"
        role_super.display_name = "超级管理员"
        role_super.level = 100

        role_teacher = MagicMock()
        role_teacher.id = "teacher"
        role_teacher.name = "teacher"
        role_teacher.display_name = "教师"
        role_teacher.level = 10

        with patch("api.v1.roles.get_roles", new_callable=AsyncMock) as mock_get_roles, \
             patch("api.v1.roles.get_role_permissions", new_callable=AsyncMock) as mock_get_perms, \
             patch("api.v1.roles.get_policy") as mock_policy:

            mock_get_roles.return_value = [role_super, role_teacher]
            mock_get_perms.side_effect = [
                ["user:read", "user:create"],
                ["user:read"],
            ]
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            result = await list_roles(request)

        assert result["success"] is True
        roles_data = result["data"]
        assert len(roles_data) == 2
        # super_admin 应有 permissions 数组
        assert roles_data[0]["id"] == "super_admin"
        assert roles_data[0]["permissions"] == ["user:read", "user:create"]
        # teacher 应有 permissions 数组
        assert roles_data[1]["id"] == "teacher"
        assert roles_data[1]["permissions"] == ["user:read"]


# ═══════════════════════════════════════════════════════════════
# H5: PUT /apps/{id}/status — 应用状态切换
# ═══════════════════════════════════════════════════════════════


class TestAppsToggleStatus:
    """PUT /apps/{id}/status — 切换应用启用/禁用"""

    @pytest.mark.asyncio
    async def test_toggle_app_status_to_disabled(self):
        """将应用状态从 active 改为 disabled"""
        from api.v1.apps import toggle_app_status
        from pydantic import BaseModel

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}

        # Mock DB
        mock_app = MagicMock()
        mock_app.id = "ppt-generator"
        mock_app.name = "PPT生成器"
        mock_app.status = "active"

        with patch("api.v1.apps.async_session") as mock_session, \
             patch("api.v1.apps.get_policy") as mock_policy, \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock):

            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_app
            mock_db.execute.return_value = mock_result

            result = await toggle_app_status("ppt-generator", request, status="disabled")

        assert result["success"] is True
        assert result["data"]["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_toggle_app_status_not_found(self):
        """应用不存在返回 404"""
        from api.v1.apps import toggle_app_status
        from fastapi import HTTPException

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}

        with patch("api.v1.apps.async_session") as mock_session, \
             patch("api.v1.apps.get_policy") as mock_policy, \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock):

            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await toggle_app_status("nonexistent", request, status="disabled")
            assert exc_info.value.status_code == 404


# ═══════════════════════════════════════════════════════════════
# H4: POST /roles + PUT /roles/{id} — 角色创建与更新
# ═══════════════════════════════════════════════════════════════


class TestRolesCreateAndUpdate:
    """POST /roles 创建角色 + PUT /roles/{id} 更新角色"""

    @pytest.mark.asyncio
    async def test_create_role(self):
        """POST /roles 创建自定义角色"""
        from api.v1.roles import create_role

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.get_policy") as mock_policy, \
             patch("api.v1.roles.write_audit_log", new_callable=AsyncMock):

            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await create_role(
                request,
                name="lab_manager",
                display_name="实验室管理员",
                permission_ids=["user:read", "campus:read"],
            )

        assert result["success"] is True
        assert result["data"]["name"] == "lab_manager"
        assert result["data"]["permissions"] == ["user:read", "campus:read"]

    @pytest.mark.asyncio
    async def test_create_role_with_empty_name_rejected(self):
        """角色名不能为空"""
        from api.v1.roles import create_role
        from fastapi import HTTPException

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        with patch("api.v1.roles.get_policy") as mock_policy:
            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            with pytest.raises(HTTPException) as exc_info:
                await create_role(request, name="", display_name="X", permission_ids=[])
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_role_name_and_permissions(self):
        """PUT /roles/{id} 更新角色名和权限"""
        from api.v1.roles import update_role

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        # Mock existing role
        mock_role = MagicMock()
        mock_role.id = "teacher"
        mock_role.name = "teacher"
        mock_role.display_name = "教师"
        mock_role.is_system = False

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.get_policy") as mock_policy, \
             patch("api.v1.roles.write_audit_log", new_callable=AsyncMock):

            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_role
            mock_db.execute.return_value = mock_result

            result = await update_role(
                "teacher",
                request,
                name="instructor",
                display_name="指导教师",
                permission_ids=["user:read", "campus:read", "campus:update"],
            )

        assert result["success"] is True
        assert result["data"]["name"] == "instructor"
        assert result["data"]["permissions"] == ["user:read", "campus:read", "campus:update"]

    @pytest.mark.asyncio
    async def test_update_system_role_rejected(self):
        """系统角色禁止修改"""
        from api.v1.roles import update_role
        from fastapi import HTTPException

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        mock_role = MagicMock()
        mock_role.id = "super_admin"
        mock_role.is_system = True

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.get_policy") as mock_policy:

            policy = MagicMock()
            policy.check_permission = AsyncMock(return_value=True)
            mock_policy.return_value = policy

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_role
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await update_role("super_admin", request, name="x", display_name="x", permission_ids=[])
            assert exc_info.value.status_code == 403
