"""测试登录限流 — TDD RED"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestLoginRateLimit:
    """C3: 密码登录必须有失败次数限制"""

    @pytest.mark.asyncio
    async def test_login_returns_429_after_5_failures(self):
        """连续 5 次登录失败后返回 429 Too Many Requests"""
        from httpx import AsyncClient, ASGITransport
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            mock_redis = MagicMock()
            # 模拟已经失败 5 次
            mock_redis.get = AsyncMock(return_value=b"5")
            mock_redis.incr = AsyncMock(return_value=6)
            mock_redis.expire = AsyncMock()

            with patch("api.v1.auth.redis_client", mock_redis):
                resp = await client.post("/api/v1/auth/login", json={
                    "user_id": "admin",
                    "password": "wrong",
                })
                assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_login_records_failure_in_redis(self):
        """登录失败时 Redis 计数器递增"""
        from httpx import AsyncClient, ASGITransport
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)  # no existing count
            mock_redis.incr = AsyncMock(return_value=1)
            mock_redis.expire = AsyncMock()

            with patch("api.v1.auth.redis_client", mock_redis), \
                 patch("api.v1.auth.async_session") as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db.execute.return_value = mock_result

                await client.post("/api/v1/auth/login", json={
                    "user_id": "admin",
                    "password": "wrong",
                })

                mock_redis.incr.assert_called()
                mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_login_resets_counter_on_success(self):
        """登录成功时清除失败计数器"""
        from httpx import AsyncClient, ASGITransport
        from main import app
        from domains.identity.password import hash_password

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=None)  # no rate limit
            mock_redis.delete = AsyncMock()
            mock_sm = MagicMock()
            mock_sm.cache_user_status = AsyncMock()

            with patch("api.v1.auth.redis_client", mock_redis), \
                 patch("api.v1.auth.session_mgr", mock_sm), \
                 patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[{"role_id": "super_admin", "scope_id": "*"}]), \
                 patch("api.v1.auth.async_session") as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=False)

                mock_user = MagicMock()
                mock_user.id = "admin"
                mock_user.tenant_id = "default"
                mock_user.name = "Admin"
                mock_user.status = "active"

                pw_hash = hash_password("admin123")
                mock_pw = MagicMock()
                mock_pw.value = pw_hash

                mock_result_user = MagicMock()
                mock_result_user.scalar_one_or_none.return_value = mock_user
                mock_result_pw = MagicMock()
                mock_result_pw.scalar_one_or_none.return_value = mock_pw

                mock_db.execute.side_effect = [mock_result_user, mock_result_pw]

                resp = await client.post("/api/v1/auth/login", json={
                    "user_id": "admin",
                    "password": "admin123",
                })

                assert resp.status_code == 200
                mock_redis.delete.assert_called()

    @pytest.mark.asyncio
    async def test_login_allowed_before_5_failures(self):
        """失败次数 < 5 时允许继续尝试"""
        from httpx import AsyncClient, ASGITransport
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            mock_redis = MagicMock()
            mock_redis.get = AsyncMock(return_value=b"3")  # 3 failures so far
            mock_redis.incr = AsyncMock(return_value=4)
            mock_redis.expire = AsyncMock()

            with patch("api.v1.auth.redis_client", mock_redis), \
                 patch("api.v1.auth.async_session") as mock_session:
                mock_db = AsyncMock()
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
                mock_session.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db.execute.return_value = mock_result

                resp = await client.post("/api/v1/auth/login", json={
                    "user_id": "admin",
                    "password": "wrong",
                })
                # Should get 401 (auth failure), not 429 (rate limited)
                assert resp.status_code == 401
