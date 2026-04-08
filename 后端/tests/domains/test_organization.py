"""测试 tenant/campus/roles/audit domain 逻辑"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone


class TestTenantDomain:
    @pytest.mark.asyncio
    async def test_get_tenants_returns_list(self):
        """get_tenants 应返回租户列表"""
        from domains.organization.tenant import get_tenants
        with patch("domains.organization.tenant.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_tenant = MagicMock()
            mock_tenant.id = "t1"
            mock_tenant.name = "TestTenant"
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_tenant]
            mock_db.execute.return_value = mock_result

            result = await get_tenants()
            assert len(result) == 1
            assert result[0].id == "t1"

    @pytest.mark.asyncio
    async def test_create_tenant_commits(self):
        """create_tenant 应添加并提交"""
        from domains.organization.tenant import create_tenant
        with patch("domains.organization.tenant.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await create_tenant("t1", "MyTenant")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_tenant_sets_deleted_at(self):
        """软删除应设置 deleted_at"""
        from domains.organization.tenant import soft_delete_tenant
        with patch("domains.organization.tenant.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_tenant = MagicMock()
            mock_tenant.deleted_at = None
            mock_db.get.return_value = mock_tenant

            result = await soft_delete_tenant("t1")
            assert result is True
            mock_db.commit.assert_called_once()


class TestCampusDomain:
    @pytest.mark.asyncio
    async def test_get_campuses_filters_by_tenant(self):
        """get_campuses 应按 tenant_id 过滤"""
        from domains.organization.campus import get_campuses
        with patch("domains.organization.campus.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_campus = MagicMock()
            mock_campus.id = "c1"
            mock_campus.name = "Campus A"
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_campus]
            mock_db.execute.return_value = mock_result

            result = await get_campuses("t1")
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_campus_commits(self):
        """create_campus 应添加并提交"""
        from domains.organization.campus import create_campus
        with patch("domains.organization.campus.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await create_campus("t1", "c1", "Campus A")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_campus_returns_false_if_not_found(self):
        """删除不存在的校区应返回 False"""
        from domains.organization.campus import soft_delete_campus
        with patch("domains.organization.campus.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            result = await soft_delete_campus("nonexistent", "t1")
            assert result is False


class TestRolesDomain:
    @pytest.mark.asyncio
    async def test_assign_role_creates_and_invalidates_cache(self):
        """分配角色应创建 UserRole 并失效缓存"""
        from domains.access.roles import assign_role
        with patch("domains.access.roles.async_session") as mock_session, \
             patch("domains.access.policy.invalidate_permission_cache", new_callable=AsyncMock) as mock_inv:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await assign_role("u1", "super_admin")
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_inv.assert_called_once_with("u1")

    @pytest.mark.asyncio
    async def test_revoke_role_deletes_and_invalidates_cache(self):
        """撤销角色应删除 UserRole 并失效缓存"""
        from domains.access.roles import revoke_role
        with patch("domains.access.roles.async_session") as mock_session, \
             patch("domains.access.policy.invalidate_permission_cache", new_callable=AsyncMock) as mock_inv:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_ur
            mock_db.execute.return_value = mock_result

            result = await revoke_role("u1", "super_admin")
            assert result is True
            mock_db.delete.assert_called_once_with(mock_ur)
            mock_inv.assert_called_once_with("u1")

    @pytest.mark.asyncio
    async def test_revoke_role_returns_false_if_not_found(self):
        """撤销不存在的角色应返回 False"""
        from domains.access.roles import revoke_role
        with patch("domains.access.roles.async_session") as mock_session, \
             patch("domains.access.policy.invalidate_permission_cache", new_callable=AsyncMock) as mock_inv:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            result = await revoke_role("u1", "nonexistent")
            assert result is False
            mock_inv.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_roles_returns_list(self):
        """get_user_roles 应返回角色列表"""
        from domains.access.roles import get_user_roles
        with patch("domains.access.roles.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_ur = MagicMock()
            mock_ur.role_id = "super_admin"
            mock_ur.scope_id = "*"
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_ur]
            mock_db.execute.return_value = mock_result

            result = await get_user_roles("u1")
            assert len(result) == 1
            assert result[0]["role_id"] == "super_admin"


class TestAuditDomain:
    @pytest.mark.asyncio
    async def test_write_audit_log_commits(self):
        """审计日志应写入 DB 并提交"""
        from domains.access.audit import write_audit_log
        with patch("domains.access.audit.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            await write_audit_log(
                tenant_id="t1", user_id="u1",
                action="create", resource_type="campus",
                resource_id="c1",
            )
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_audit_log_handles_db_error(self):
        """DB 写入失败不应抛异常，记录日志即可"""
        from domains.access.audit import write_audit_log
        with patch("domains.access.audit.async_session") as mock_session, \
             patch("domains.access.audit.logger") as mock_logger:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_db.commit.side_effect = Exception("DB down")

            # 不应抛异常
            await write_audit_log(
                tenant_id="t1", user_id="u1",
                action="create", resource_type="campus",
            )
            mock_logger.error.assert_called_once()


class TestPermissionsDomain:
    @pytest.mark.asyncio
    async def test_get_role_permissions_returns_ids(self):
        """get_role_permissions 应返回权限 ID 列表"""
        from domains.access.permissions import get_role_permissions
        with patch("domains.access.permissions.async_session") as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_rp = MagicMock()
            mock_rp.permission_id = "user:read"
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_rp]
            mock_db.execute.return_value = mock_result

            result = await get_role_permissions("super_admin")
            assert "user:read" in result
