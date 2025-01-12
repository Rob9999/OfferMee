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
    location = Column(String)  # Expected: Remote, On-site, Hybrid, or None
    must_haves = Column(Text)  # Can store JSON string or comma-separated values
    nice_to_haves = Column(Text)
    tasks = Column(Text)
    responsibilities = Column(Text)
    hourly_rate = Column(Float)  # Corresponds to max-hourly-rate
    other_conditions = Column(Text)
    contact_person = Column(String)
    provider = Column(String)  # Project provider
    provider_link = Column(String)  # Project provider link
    start_date = Column(Date)
    end_date = Column(Date)
    duration = Column(String)  # Duration in months or appropriate format
    extension_option = Column(String)  # Expected: Yes, No, or None
    original_link = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW)
