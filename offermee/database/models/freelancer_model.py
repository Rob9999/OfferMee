from sqlalchemy import Column, Integer, String, Float
from offermee.database.database_manager import DatabaseManager
from sqlalchemy.ext.declarative import declarative_base

Base = DatabaseManager.Base


class FreelancerModel(Base):
    __tablename__ = "freelancers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    skills = Column(String, nullable=True)  # Kommagetrennte Liste
    desired_rate = Column(Float, nullable=True)  # Gewünschter Stundensatz
