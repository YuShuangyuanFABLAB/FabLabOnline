"""Phase 4C 前后端对齐测试 — H6/H5/H4"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.background import BackgroundTasks


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
             patch("api.v1.roles.get_roles_batch_permissions", new_callable=AsyncMock) as mock_batch_perms, \
             patch("api.v1.roles.require_permission", new_callable=AsyncMock):

            mock_get_roles.return_value = [role_super, role_teacher]
            mock_batch_perms.return_value = {
                "super_admin": ["user:read", "user:create"],
                "teacher": ["user:read"],
            }

            result = await list_roles(request)

        assert result["success"] is True
        roles_data = result["data"]
        assert len(roles_data) == 2
        assert roles_data[0]["id"] == "super_admin"
        assert roles_data[0]["permissions"] == ["user:read", "user:create"]
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

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test"}

        mock_app = MagicMock()
        mock_app.id = "ppt-generator"
        mock_app.name = "PPT生成器"
        mock_app.status = "active"

        with patch("api.v1.apps.async_session") as mock_session, \
             patch("api.v1.apps.require_permission", new_callable=AsyncMock), \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock):

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_app
            mock_db.execute.return_value = mock_result

            result = await toggle_app_status("ppt-generator", request, status="disabled", background_tasks=BackgroundTasks())

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
             patch("api.v1.apps.require_permission", new_callable=AsyncMock), \
             patch("api.v1.apps.write_audit_log", new_callable=AsyncMock):

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await toggle_app_status("nonexistent", request, status="disabled", background_tasks=BackgroundTasks())
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
             patch("api.v1.roles.require_permission", new_callable=AsyncMock), \
             patch("api.v1.roles.write_audit_log", new_callable=AsyncMock):

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await create_role(
                request,
                background_tasks=BackgroundTasks(),
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

        with patch("api.v1.roles.require_permission", new_callable=AsyncMock):
            with pytest.raises(HTTPException) as exc_info:
                await create_role(request, background_tasks=BackgroundTasks(), name="", display_name="X", permission_ids=[])
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_role_name_and_permissions(self):
        """PUT /roles/{id} 更新角色名和权限"""
        from api.v1.roles import update_role

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        mock_role = MagicMock()
        mock_role.id = "teacher"
        mock_role.name = "teacher"
        mock_role.display_name = "教师"
        mock_role.is_system = False

        with patch("api.v1.roles.async_session") as mock_session, \
             patch("api.v1.roles.require_permission", new_callable=AsyncMock), \
             patch("api.v1.roles.write_audit_log", new_callable=AsyncMock):

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_role
            mock_db.execute.return_value = mock_result

            result = await update_role(
                "teacher",
                request,
                background_tasks=BackgroundTasks(),
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
             patch("api.v1.roles.require_permission", new_callable=AsyncMock):

            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_role
            mock_db.execute.return_value = mock_result

            with pytest.raises(HTTPException) as exc_info:
                await update_role("super_admin", request, background_tasks=BackgroundTasks(), name="x", display_name="x", permission_ids=[])
            assert exc_info.value.status_code == 403
