import uuid
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP

# Import strictly from your existing file
from app.db.base import Base 

class ProjectDailyMetrics(Base):
    __tablename__ = "project_daily_metrics"
    
    # 🔴 THIS LINE FIXES YOUR ERROR
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    metric_date = Column(Date, nullable=False)
    work_role = Column(String, nullable=False, default="AGGREGATE")
    
    # Aggregated Stats
    tasks_completed = Column(Integer, nullable=False, default=0)
    active_users_count = Column(Integer, nullable=False, default=0)
    total_hours_worked = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Benchmarks
    avg_productivity_score = Column(Numeric(5, 2), nullable=True)
    avg_hours_worked_per_user = Column(Numeric(5, 2), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )