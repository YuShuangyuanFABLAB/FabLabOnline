from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base, TenantModel


class Campus(Base, TenantModel):
    __tablename__ = "campuses"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    parent_id = Column(String(64))
    campus_level = Column(String(16), server_default="branch")
    status = Column(String(16), server_default="active")
    config = Column(JSONB, server_default="{}")

    _INIT_DEFAULTS = {"campus_level": "branch", "status": "active", "config": {}}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
