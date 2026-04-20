"""Task A: 生产配置验证增强 — validate_production() 更多检查"""
import pytest
from unittest.mock import patch

from config.settings import Settings


class TestValidateProduction:
    """生产模式下的配置校验"""

    def _make_settings(self, **overrides):
        """创建测试用 Settings 实例"""
        defaults = {
            "DEBUG": False,
            "JWT_SECRET_KEY": "a" * 32,
            "ADMIN_PASSWORD": "StrongPass123",
            "CORS_ORIGINS": "https://fablab.example.com",
            "DOCS_ENABLED": False,
            "WECHAT_APP_ID": "",
            "WECHAT_APP_SECRET": "",
        }
        defaults.update(overrides)
        return Settings(**defaults, _env_file=None)

    # --- ADMIN_PASSWORD ---

    def test_empty_admin_password_warns(self):
        """ADMIN_PASSWORD 为空时应记录警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(ADMIN_PASSWORD="")
            s.validate_production()
        mock_logger.warning.assert_any_call("ADMIN_PASSWORD 未设置，将使用默认密码")

    def test_set_admin_password_no_warning(self):
        """ADMIN_PASSWORD 已设置时不应有警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(ADMIN_PASSWORD="MySecret123")
            s.validate_production()
        calls = [c.args[0] for c in mock_logger.warning.call_args_list]
        assert not any("ADMIN_PASSWORD" in c for c in calls)

    # --- DOCS_ENABLED ---

    def test_docs_enabled_in_production_warns(self):
        """生产环境 DOCS_ENABLED=True 时应记录警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(DOCS_ENABLED=True)
            s.validate_production()
        mock_logger.warning.assert_any_call("生产环境建议关闭 API 文档 (DOCS_ENABLED=false)")

    def test_docs_disabled_no_warning(self):
        """DOCS_ENABLED=False 时不应有文档警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(DOCS_ENABLED=False)
            s.validate_production()
        calls = [c.args[0] for c in mock_logger.warning.call_args_list]
        assert not any("DOCS_ENABLED" in c for c in calls)

    # --- CORS_ORIGINS ---

    def test_empty_cors_origins_warns(self):
        """CORS_ORIGINS 为空时应记录警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(CORS_ORIGINS="")
            s.validate_production()
        mock_logger.warning.assert_any_call("CORS_ORIGINS 为空，仅允许 localhost 访问")

    def test_set_cors_origins_no_warning(self):
        """CORS_ORIGINS 已设置时不应有警告"""
        with patch("config.settings.logger") as mock_logger:
            s = self._make_settings(CORS_ORIGINS="https://fablab.example.com")
            s.validate_production()
        calls = [c.args[0] for c in mock_logger.warning.call_args_list]
        assert not any("CORS_ORIGINS" in c for c in calls)

    # --- WeChat partial config ---

    def test_wechat_partial_config_raises(self):
        """微信配置部分填写时应抛出 ValueError"""
        s = self._make_settings(WECHAT_APP_ID="wx123", WECHAT_APP_SECRET="")
        with pytest.raises(ValueError, match="微信配置"):
            s.validate_production()

    def test_wechat_full_config_ok(self):
        """微信配置全部填写时不应抛出"""
        s = self._make_settings(WECHAT_APP_ID="wx123", WECHAT_APP_SECRET="secret")
        s.validate_production()  # 不应抛出

    def test_wechat_both_empty_ok(self):
        """微信配置全部为空时不应抛出"""
        s = self._make_settings(WECHAT_APP_ID="", WECHAT_APP_SECRET="")
        s.validate_production()  # 不应抛出

    # --- DEBUG mode skips checks ---

    def test_debug_mode_skips_validation(self):
        """DEBUG=True 时 validate_production 不检查（保留原行为）"""
        s = Settings(
            DEBUG=True,
            JWT_SECRET_KEY="change-me-in-production",
            _env_file=None,
        )
        s.validate_production()  # 不应抛出

    # --- Existing JWT checks still work ---

    def test_jwt_default_key_raises(self):
        """JWT_SECRET_KEY 为默认值时应抛出"""
        s = self._make_settings(JWT_SECRET_KEY="change-me-in-production")
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            s.validate_production()

    def test_jwt_short_key_raises(self):
        """JWT_SECRET_KEY 太短时应抛出"""
        s = self._make_settings(JWT_SECRET_KEY="short")
        with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
            s.validate_production()
