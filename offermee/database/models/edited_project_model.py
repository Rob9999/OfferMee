from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
)
from datetime import datetime
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.enums.offer_status import OfferStatus


class EditedProjectModel(BaseProjectModel):
    __tablename__ = "edited_projects"

    id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    offer_written = Column(Boolean, default=False)
    offer = Column(Text)
    commented = Column(Boolean, default=False)
    comment = Column(Text)
    offer_status = Column(Enum(OfferStatus), default=OfferStatus.DRAFT)
    # FIELDS FOR TRACKING & FOLLOW-UPS
    sent_date = Column(DateTime, default=None)  # When was the offer sent?
    followup_count = Column(Integer, default=0)  # How many follow-ups were sent?
    last_followup_date = Column(
        DateTime, default=None
    )  # When was the last follow-up sent?
    opened = Column(Boolean, default=False)  # Was the offer opened/read?
    opened_date = Column(
        DateTime, default=None
    )  # When was the offer opened for the first time?
