import uuid
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Numeric, Enum as SqEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from app.db.base import Base
from app.models.user_quality import QualityRating # Ensure this Import works

class ProjectQualityCurrent(Base):
    __tablename__ = "project_quality_current"

    # Using project_id as PK since one project has only one "Current" status
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True)
    
    rating = Column(SqEnum(QualityRating), nullable=False) # GOOD, BAD, AVERAGE
    quality_score = Column(Numeric(5, 2), nullable=True)
    
    # Counters for the dashboard charts
    good_count = Column(Integer, nullable=False, default=0)
    average_count = Column(Integer, nullable=False, default=0)
    bad_count = Column(Integer, nullable=False, default=0)
    
    derived_from = Column(String, nullable=False, default="AUTO_AGGREGATE")
    last_computed_at = Column(TIMESTAMP(timezone=True), nullable=False)
    
    is_override = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    
    assessed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )