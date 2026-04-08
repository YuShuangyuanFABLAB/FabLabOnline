from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base, TenantModel


class Tenant(Base, TenantModel):
    __tablename__ = "tenants"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    isolation_mode = Column(String(16), server_default="shared")
    status = Column(String(16), server_default="active")
    config = Column(JSONB, server_default="{}")

    _INIT_DEFAULTS = {"isolation_mode": "shared", "status": "active", "config": {}}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
