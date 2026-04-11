"""测试 PBKDF2 密码哈希 — TDD RED"""
import pytest
import hashlib
import os


class TestPasswordHashing:
    """C2: 密码必须使用 PBKDF2 + 随机盐，替代无盐 SHA-256"""

    def test_hash_password_returns_dict_with_required_fields(self):
        """hash_password 返回包含 algorithm, salt, iterations, hash 的字典"""
        from domains.identity.password import hash_password
        result = hash_password("admin123")
        assert "algorithm" in result
        assert "salt" in result
        assert "iterations" in result
        assert "hash" in result

    def test_hash_password_uses_pbkdf2_sha256(self):
        """hash_password 使用 pbkdf2_sha256 算法"""
        from domains.identity.password import hash_password
        result = hash_password("admin123")
        assert result["algorithm"] == "pbkdf2_sha256"

    def test_hash_password_uses_high_iterations(self):
        """hash_password 使用至少 480000 次迭代"""
        from domains.identity.password import hash_password
        result = hash_password("admin123")
        assert result["iterations"] >= 480000

    def test_hash_password_generates_random_salt(self):
        """每次调用生成不同的盐"""
        from domains.identity.password import hash_password
        r1 = hash_password("admin123")
        r2 = hash_password("admin123")
        assert r1["salt"] != r2["salt"]
        assert r1["hash"] != r2["hash"]

    def test_verify_password_correct(self):
        """verify_password 对正确密码返回 True"""
        from domains.identity.password import hash_password, verify_password
        result = hash_password("admin123")
        assert verify_password("admin123", result) is True

    def test_verify_password_wrong(self):
        """verify_password 对错误密码返回 False"""
        from domains.identity.password import hash_password, verify_password
        result = hash_password("admin123")
        assert verify_password("wrong_password", result) is False

    def test_verify_password_accepts_json_string(self):
        """verify_password 接受 JSON 字符串格式的存储值（configs 表兼容）"""
        import json
        from domains.identity.password import hash_password, verify_password
        result = hash_password("admin123")
        # configs 表中 value 是 JSONB，存储为 JSON 字符串
        stored_as_string = json.dumps(result)
        assert verify_password("admin123", stored_as_string) is True
        assert verify_password("wrong", stored_as_string) is False

    def test_verify_password_accepts_dict(self):
        """verify_password 直接接受 dict 格式"""
        from domains.identity.password import hash_password, verify_password
        result = hash_password("admin123")
        assert verify_password("admin123", result) is True

    def test_verify_password_legacy_sha256_still_works(self):
        """verify_password 对旧版 SHA-256 格式仍然兼容（过渡期）"""
        from domains.identity.password import verify_password
        # 旧格式：纯 hex 字符串（64 字符）
        legacy_hash = hashlib.sha256("admin123".encode()).hexdigest()
        assert verify_password("admin123", legacy_hash) is True
        assert verify_password("wrong", legacy_hash) is False
