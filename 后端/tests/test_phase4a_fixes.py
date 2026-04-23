"""Phase 4A 快速修复测试 — C1/C3/H1/H9/H8"""
import ast
import os

from unittest.mock import AsyncMock, MagicMock, patch


# ── C1: Cookie SameSite 必须为 strict ──


class TestSameSiteStrict:
    """C1: Cookie 的 SameSite 属性必须为 strict"""

    @patch("api.v1.auth.redis_client")
    @patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[])
    @patch("api.v1.auth.verify_password", return_value=True)
    @patch("api.v1.auth.token_mgr")
    @patch("api.v1.auth.session_mgr")
    @patch("api.v1.auth.async_session")
    async def test_login_cookie_samesite_strict(
        self, mock_db, mock_session, mock_token, mock_verify,
        mock_roles, mock_redis
    ):
        """登录端点 set_cookie 的 samesite 必须为 strict"""
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_token.create_token = MagicMock(return_value="jwt-token")
        mock_session.cache_user_status = AsyncMock()

        user = MagicMock()
        user.id = "admin"
        user.name = "管理员"
        user.tenant_id = "default"
        user.status = "active"
        user.deleted_at = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)

        pw_config = MagicMock()
        pw_config.value = '{"algorithm":"pbkdf2_sha256","salt":"s","iterations":480000,"hash":"h"}'
        pw_result = MagicMock()
        pw_result.scalar_one_or_none = MagicMock(return_value=pw_config)

        totp_result = MagicMock()
        totp_result.scalar_one_or_none = MagicMock(return_value=None)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.execute = AsyncMock(side_effect=[mock_result, pw_result, totp_result])
        mock_ctx.commit = AsyncMock()
        mock_db.return_value = mock_ctx

        from api.v1.auth import password_login, LoginRequest
        body = LoginRequest(user_id="admin", password="admin123")
        response = await password_login(body)

        # 检查 cookies
        cookie_headers = [
            v for k, v in response.headers.items() if k.lower() == "set-cookie"
        ]
        assert len(cookie_headers) > 0, "登录响应必须设置 Cookie"
        cookie_str = cookie_headers[0]
        assert "samesite=strict" in cookie_str.lower(), (
            f"Cookie SameSite 必须为 strict，实际: {cookie_str}"
        )


# ── C3: init_db.py 不应输出明文密码 ──


class TestInitDbNoPasswordLeak:
    """C3: init_db.py 的 print 输出不能包含明文密码"""

    def test_seed_data_print_no_password(self):
        """seed_data 完成后的 print 不应包含 admin123"""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "init_db.py"
        )
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "seed_data":
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Name) and func.id == "print":
                            for arg in child.args:
                                if isinstance(arg, ast.Constant):
                                    text = str(arg.value)
                                    assert "admin123" not in text, (
                                        f"seed_data 的 print 不应包含明文密码: {text}"
                                    )


# ── H1: users.py 不应有重复 router 定义 ──


class TestNoDuplicateRouter:
    """H1: users.py 中 router = APIRouter(...) 只能出现一次"""

    def test_users_single_router_definition(self):
        """users.py 中 APIRouter 只实例化一次"""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "api", "v1", "users.py"
        )
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()

        router_count = source.count("router = APIRouter(")
        assert router_count == 1, (
            f"users.py 中 router = APIRouter(...) 出现了 {router_count} 次，应该只有 1 次"
        )


# ── H9: callback 端点不应在 response body 中返回 token ──


class TestCallbackNoTokenLeak:
    """H9: 微信 OAuth callback 不应在 response body 中泄露 token"""

    @patch("api.v1.auth.get_user_roles", new_callable=AsyncMock, return_value=[])
    @patch("api.v1.auth.oauth")
    @patch("api.v1.auth.token_mgr")
    @patch("api.v1.auth.session_mgr")
    @patch("api.v1.auth.async_session")
    async def test_callback_no_token_in_body(
        self, mock_db, mock_session, mock_token, mock_oauth, mock_roles
    ):
        """callback 响应的 JSON body 中不应包含 token 字段"""
        mock_oauth.handle_callback = AsyncMock(
            return_value={"openid": "test-openid", "unionid": None}
        )
        mock_oauth.set_session_token = AsyncMock()
        mock_token.create_token = MagicMock(return_value="jwt-token-12345")
        mock_session.cache_user_status = AsyncMock()

        user = MagicMock(
            id="u_abc123", name="微信用户", tenant_id="default",
            wechat_openid="test-openid",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_ctx.commit = AsyncMock()
        mock_ctx.refresh = AsyncMock()
        mock_db.return_value = mock_ctx

        from api.v1.auth import wechat_callback
        result = await wechat_callback(code="test-code", state="test-state")

        data = result.get("data", result) if isinstance(result, dict) else {}
        assert "token" not in data, (
            f"callback 响应不应包含 token 字段，实际: {data}"
        )


# ── H8: manage.py 必须使用 PBKDF2 而非 SHA-256 ──


class TestManagePyPBKDF2:
    """H8: manage.py 的密码哈希必须使用 PBKDF2-SHA256"""

    def test_manage_imports_password_module(self):
        """manage.py 必须导入 domains.identity.password"""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "manage.py"
        )
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()

        assert "from domains.identity.password import" in source or \
               "from domains.identity.password" in source, (
            "manage.py 必须导入 domains.identity.password 模块使用 PBKDF2"
        )

    def test_manage_no_sha256_hash(self):
        """manage.py 不应有自实现的 SHA-256 哈希函数"""
        source_path = os.path.join(
            os.path.dirname(__file__), "..", "manage.py"
        )
        with open(source_path, "r", encoding="utf-8") as f:
            source = f.read()

        assert "def _hash_password" not in source, (
            "manage.py 不应自定义 _hash_password 函数，应使用 domains.identity.password.hash_password"
        )

    def test_manage_password_hash_format(self):
        """manage.py 使用的 hash_password 生成 PBKDF2 格式"""
        from domains.identity.password import hash_password
        result = hash_password("test_password")
        assert result["algorithm"] == "pbkdf2_sha256"
        assert result["iterations"] == 480000
        assert len(result["salt"]) == 64  # 32 bytes hex
        assert len(result["hash"]) == 64  # sha256 hex
