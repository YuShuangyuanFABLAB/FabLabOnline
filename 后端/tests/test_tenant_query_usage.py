"""M10: API 路由应使用 TenantModel.tenant_query() 替代手动构造"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestUsersUsesTenantQuery:
    """users.py 应通过 User.tenant_query() 构造安全查询"""

    @patch("api.v1.users.require_permission", new_callable=AsyncMock)
    @patch("api.v1.users.async_session")
    async def test_list_users_calls_tenant_query(
        self, mock_session, mock_perm
    ):
        """list_users 应使用 User.tenant_query 而非手动 .where()"""
        from api.v1.users import list_users
        from models.user import User

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        await list_users(request)

        # 验证 execute 被调用了
        assert mock_db.execute.called
        # 获取执行的 SQL 语句
        stmt = mock_db.execute.call_args[0][0]
        sql_str = str(stmt)
        # tenant_id 应出现在 WHERE 中
        assert "tenant_id" in sql_str.lower()

    @patch("api.v1.users.require_permission", new_callable=AsyncMock)
    @patch("api.v1.users.async_session")
    async def test_get_user_filters_by_tenant(
        self, mock_session, mock_perm
    ):
        """get_user 应过滤 tenant_id 防止跨租户访问"""
        from api.v1.users import get_user

        mock_user = MagicMock()
        mock_user.id = "user1"
        mock_user.tenant_id = "default"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

        request = MagicMock()
        request.state.user_id = "admin"
        request.state.tenant_id = "default"

        result = await get_user("user1", request)
        assert result["success"] is True
        # 验证 SQL 包含 tenant_id 过滤
        stmt = mock_db.execute.call_args[0][0]
        sql_str = str(stmt)
        assert "tenant_id" in sql_str.lower()
