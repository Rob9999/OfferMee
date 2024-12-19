from sqlalchemy import (
    Column,
    Enum,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from offermee.database.models.enums.project_status import ProjectStatus

from offermee.database.database_manager import DatabaseManager

Base = DatabaseManager.Base


class BaseProjectModel(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    must_haves = Column(Text)
    nice_to_haves = Column(Text)
    tasks = Column(Text)
    hourly_rate = Column(Float)
    other_conditions = Column(Text)
    contact_person = Column(String)
    provider = Column(String)
    start_date = Column(Date)
    original_link = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW)
