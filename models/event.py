from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from models.base import Base


class Event(Base):
    __tablename__ = "events"
    # 分区表主键必须包含分区键 timestamp
    event_seq = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    event_version = Column(Integer, nullable=False, default=1)
    event_source = Column(String(16), nullable=False, server_default="client")
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    tenant_id = Column(String(64), nullable=False)
    campus_id = Column(String(64))
    user_id = Column(String(64), nullable=False)
    app_id = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False)
    trace_id = Column(String(64))

    __table_args__ = (
        Index("idx_events_tenant_time", "tenant_id", "timestamp"),
        Index("idx_events_type", "event_type"),
        Index("idx_events_tenant_type_time", "tenant_id", "event_type", "timestamp"),
        Index("idx_events_user", "user_id"),
        Index("idx_events_source", "event_source"),
    )


class EventConsumer(Base):
    __tablename__ = "event_consumers"

    consumer_name = Column(String(64), primary_key=True)
    last_event_seq = Column(BigInteger, nullable=False, server_default="0")
    version = Column(Integer, nullable=False, server_default="0")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    _INIT_DEFAULTS = {"last_event_seq": 0, "version": 0}

    def __init__(self, **kwargs):
        for key, val in self._INIT_DEFAULTS.items():
            kwargs.setdefault(key, val)
        super().__init__(**kwargs)
