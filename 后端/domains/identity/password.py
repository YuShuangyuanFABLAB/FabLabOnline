"""密码哈希模块 — PBKDF2-SHA256 + 随机盐，兼容旧版 SHA-256"""
import hashlib
import json
import os
import secrets

ITERATIONS = 480000
ALGORITHM = "pbkdf2_sha256"
SALT_BYTES = 32


def hash_password(password: str) -> dict:
    """使用 PBKDF2-SHA256 + 随机盐哈希密码。

    Returns:
        dict: {"algorithm", "salt", "iterations", "hash"} — 存入 configs 表 value 列
    """
    salt = secrets.token_hex(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return {
        "algorithm": ALGORITHM,
        "salt": salt,
        "iterations": ITERATIONS,
        "hash": dk.hex(),
    }


def verify_password(password: str, stored) -> bool:
    """验证密码是否匹配存储值。

    Args:
        password: 用户输入的明文密码
        stored: configs 表中存储的值，支持以下格式：
            - dict: {"algorithm": "pbkdf2_sha256", "salt": ..., "iterations": ..., "hash": ...}
            - str (JSON): 上面的 dict 序列化为 JSON 字符串
            - str (64 hex): 旧版 SHA-256 无盐哈希（过渡兼容）
    """
    # 解析存储值
    if isinstance(stored, dict):
        record = stored
    elif isinstance(stored, str):
        # 尝试解析为 JSON
        try:
            record = json.loads(stored)
        except (json.JSONDecodeError, TypeError):
            # 不是 JSON → 旧版 SHA-256 hex 字符串
            return _verify_legacy_sha256(password, stored)
    else:
        return False

    # PBKDF2 验证
    if not isinstance(record, dict):
        return False

    algorithm = record.get("algorithm", "")
    if algorithm == ALGORITHM:
        salt = record.get("salt", "")
        iterations = record.get("iterations", ITERATIONS)
        expected = record.get("hash", "")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
        return secrets.compare_digest(dk.hex(), expected)

    return False


def _verify_legacy_sha256(password: str, hex_hash: str) -> bool:
    """兼容旧版 SHA-256 无盐哈希（过渡期使用）。"""
    if len(hex_hash) != 64:
        return False
    computed = hashlib.sha256(password.encode()).hexdigest()
    return secrets.compare_digest(computed, hex_hash.strip('"'))
