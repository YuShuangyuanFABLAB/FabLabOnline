from sqlalchemy import Column, String, DateTime
from models.base import Base, TenantModel


class User(Base, TenantModel):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    campus_id = Column(String(64))
    wechat_openid = Column(String(128), unique=True)
    wechat_unionid = Column(String(128))
    name = Column(String(64), nullable=False)
    phone = Column(String(20))
    avatar_url = Column(String(512))
    status = Column(String(16), server_default="active")
    last_login_at = Column(DateTime(timezone=True))

    _INIT_DEFAULTS = {"status": "active"}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
