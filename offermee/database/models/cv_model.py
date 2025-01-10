from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from offermee.database.database_manager import DatabaseManager

Base = DatabaseManager.Base


class CVModel(Base):
    __tablename__ = "cvs"
    id = Column(Integer, primary_key=True)
    freelancer_id = Column(Integer, ForeignKey("freelancers.id"))
    name = Column(String, nullable=False)
    raw_text = Column(Text)  # the original text of the CV
    structured_data = Column(Text)  # JSON-Text of the structured CV data

    freelancer = relationship("FreelancerModel", backref="cv")
