from sqlalchemy import Column, String, Integer, Boolean, PrimaryKeyConstraint

from models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64))
    name = Column(String(64), nullable=False)
    display_name = Column(String(128), nullable=False)
    description = Column(String(512))
    level = Column(Integer, nullable=False, default=0)
    is_system = Column(Boolean, server_default="false")

    _INIT_DEFAULTS = {"is_system": False}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(128), primary_key=True)
    resource = Column(String(64), nullable=False)
    action = Column(String(16), nullable=False)
    display_name = Column(String(128), nullable=False)
    description = Column(String(512))


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        PrimaryKeyConstraint("role_id", "permission_id"),
    )

    role_id = Column(String(64), nullable=False)
    permission_id = Column(String(128), nullable=False)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "role_id", "scope_id"),
    )

    user_id = Column(String(64), nullable=False)
    role_id = Column(String(64), nullable=False)
    scope_id = Column(String(64), nullable=False, server_default="*")

    _INIT_DEFAULTS = {"scope_id": "*"}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
