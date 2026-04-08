"""Token 安全存储 — 操作系统密钥环 (keyring)"""
import keyring

SERVICE_NAME = "fablab-platform"


class TokenStorage:
    """JWT Token 安全存储（操作系统密钥环，不明文存储）"""

    def save_token(self, user_id: str, token: str) -> None:
        keyring.set_password(SERVICE_NAME, user_id, token)

    def get_token(self, user_id: str) -> str | None:
        return keyring.get_password(SERVICE_NAME, user_id)

    def delete_token(self, user_id: str) -> None:
        keyring.delete_password(SERVICE_NAME, user_id)
