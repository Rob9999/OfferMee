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
)
from datetime import datetime
from offermee.database.database_manager import DatabaseManager
from sqlalchemy.orm import relationship

Base = DatabaseManager.Base


class MatchingScoreModel(Base):
    __tablename__ = "matching_scores"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    freelancer_id = Column(Integer)
    matching_score = Column(Float)
    match_details = Column(JSON)
    matched_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("BaseProjectModel", backref="matching_scores")
