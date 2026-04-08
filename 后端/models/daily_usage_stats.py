from sqlalchemy import Column, String, Integer, Date, PrimaryKeyConstraint

from models.base import Base


class DailyUsageStats(Base):
    __tablename__ = "daily_usage_stats"
    __table_args__ = (
        PrimaryKeyConstraint("date", "tenant_id", "campus_id", "event_type"),
    )

    date = Column(Date, nullable=False)
    tenant_id = Column(String(64), nullable=False)
    campus_id = Column(String(64))
    event_type = Column(String(64), nullable=False)
    count = Column(Integer, nullable=False, default=0)
