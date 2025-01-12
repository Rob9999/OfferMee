from sqlalchemy import Column, Integer, String, Float, Text
from offermee.database.database_manager import DatabaseManager

Base = DatabaseManager.Base


class FreelancerModel(Base):
    __tablename__ = "freelancers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    soft_skills = Column(String, nullable=True)
    tech_skills = Column(String, nullable=True)

    desired_rate_min = Column(Float, nullable=True)  # Desired hourly minimum rate
    desired_rate_max = Column(Float, nullable=True)  # Desired hourly maximum rate
    offer_template = Column(Text, nullable=True)  # Offer template

    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    country = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    website = Column(String, nullable=False)
