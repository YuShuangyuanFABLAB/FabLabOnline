"""测试 manage.py CLI — 创建超级管理员"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_create_superadmin_creates_user_with_role():
    """create_superadmin 应创建用户并分配 super_admin 角色"""
    with patch("manage.async_session") as mock_session_cls:
        mock_db = AsyncMock()
        mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        import asyncio
        from manage import create_superadmin

        result = asyncio.run(create_superadmin("admin", "test_password_123"))

        # 验证 db.add 被调用（添加 User 和 UserRole）
        assert mock_db.add.call_count == 2
        # 验证 commit 被调用
        mock_db.commit.assert_called_once()


def test_create_superadmin_rejects_short_password():
    """密码太短应报错"""
    from manage import create_superadmin
    import asyncio

    with pytest.raises(ValueError, match="密码"):
        asyncio.run(create_superadmin("admin", "123"))


def test_create_superadmin_rejects_empty_username():
    """用户名为空应报错"""
    from manage import create_superadmin
    import asyncio

    with pytest.raises(ValueError, match="用户名"):
        asyncio.run(create_superadmin("", "test_password_123"))
