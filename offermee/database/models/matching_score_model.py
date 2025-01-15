from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
    UniqueConstraint,
)
from datetime import datetime
from offermee.database.database_manager import DatabaseManager
from sqlalchemy.orm import relationship

Base = DatabaseManager.Base


class MatchingScoreModel(Base):
    __tablename__ = "matching_scores"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    # Neuer FK:
    freelancer_id = Column(Integer, ForeignKey("freelancers.id"), nullable=False)

    matching_score = Column(Float, nullable=False, default=0.0)
    match_details = Column(JSON, nullable=True)
    matched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("ProjectModel", backref="matching_scores")
    # Neuer Relationship:
    freelancer = relationship("FreelancerModel", backref="matching_scores")

    __table_args__ = (
        UniqueConstraint(
            "project_id", "freelancer_id", name="uq_project_freelancer_score"
        ),
        Index("idx_project_freelancer_score", "project_id", "freelancer_id"),
    )
