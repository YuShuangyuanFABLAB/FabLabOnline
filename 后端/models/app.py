from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from models.base import Base


class App(Base):
    __tablename__ = "apps"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    app_key = Column(String(64), nullable=False, unique=True)
    app_secret_hash = Column(String(128), nullable=False)
    description = Column(String(512))
    status = Column(String(16), server_default="active")
    config = Column(JSONB, server_default="{}")

    _INIT_DEFAULTS = {"status": "active", "config": {}}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
