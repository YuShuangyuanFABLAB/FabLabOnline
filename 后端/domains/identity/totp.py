"""TOTP 二次验证模块 — 基于 pyotp 实现"""
import pyotp


def generate_totp_secret() -> str:
    """生成 Base32 编码的 TOTP 密钥"""
    return pyotp.random_base32()


def verify_totp_code(secret: str, code: str) -> bool:
    """验证 TOTP 码是否正确（允许前后 1 个窗口）"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def get_totp_uri(secret: str, user_id: str, issuer: str = "FabLab") -> str:
    """生成 otpauth:// URI，供 authenticator app 扫描"""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_id, issuer_name=issuer
    )
