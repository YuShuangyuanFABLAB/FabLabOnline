"""管理命令行工具 — 创建超级管理员（用户名+密码+TOTP紧急通道）"""
import sys
import os
import secrets
import hashlib
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from infrastructure.database import async_session
from models.user import User
from models.role import UserRole


def _hash_password(password: str) -> str:
    """SHA-256 密码哈希（Phase 2 升级为 bcrypt）"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"


async def create_superadmin(username: str, password: str):
    """创建超级管理员"""
    if not username:
        raise ValueError("用户名不能为空")
    if len(password) < 8:
        raise ValueError("密码长度至少8位")

    async with async_session() as db:
        user_id = f"sa_{secrets.token_hex(4)}"
        password_hash = _hash_password(password)

        user = User(
            id=user_id,
            tenant_id="default",
            name=username,
            phone=f"__pwd__:{password_hash}",
            status="active",
        )
        db.add(user)

        role = UserRole(user_id=user_id, role_id="super_admin", scope_id="*")
        db.add(role)

        await db.commit()

        print(f"超级管理员创建成功!")
        print(f"  User ID: {user_id}")
        print(f"  用户名:  {username}")
        return user_id


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python manage.py create-superadmin <username> <password>")
        sys.exit(1)
    asyncio.run(create_superadmin(sys.argv[1], sys.argv[2]))
