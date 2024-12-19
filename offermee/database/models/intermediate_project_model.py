from datetime import datetime
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from offermee.database.models.base_project_model import BaseProjectModel


class IntermediateProjectModel(BaseProjectModel):
    __tablename__ = "temp_projects"

    id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    is_saved = Column(Boolean, default=False)
    analysis = Column(JSON)
    analysis_date = Column(DateTime, default=datetime.utcnow)
