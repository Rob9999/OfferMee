from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
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
