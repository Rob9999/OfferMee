import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    Date,
    Boolean,
    Enum,
    JSON,
    ForeignKey,
    Table,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from offermee.database.database_manager import DatabaseManager

Base = DatabaseManager.Base


class LocationType(PyEnum):
    Remote = "Remote"
    OnSite = "On-site"
    Hybrid = "Hybrid"


class YesNoOption(PyEnum):
    Yes = "Yes"
    No = "No"


class ProjectStatus(PyEnum):
    NEW = "NEW"
    OFFER_SENT = "OFFER_SENT"
    INTERVIEW = "INTERVIEW"
    CONTRACT_SIGNED = "CONTRACT_SIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class OfferStatus(PyEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    FOLLOW_UP = "FOLLOW_UP"
    FINALIZED = "FINALIZED"


class TaskStatus(PyEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"


class DocumentRelatedType(PyEnum):
    ADDRESS = "ADDRESS"
    CONTACT = "CONTACT"
    REQUEST = "REQUEST"
    OFFER = "OFFER"
    CONTRACT = "CONTRACT"
    APPLICATION = "APPLICATION"
    CV = "CV"
    PROJECT = "PROJECT"
    INTERVIEW = "INTERVIEW"
    COMPANY = "COMPANY"
    EMPLOYEE = "EMPLOYEE"
    WORKPACKAGE = "WORKPACKAGE"
    CAPABILITIES = "CAPABILITIES"


class ContactRole(PyEnum):
    BUSINESS = "BUSINESS"
    EMPLOYEE = "EMPLOYEE"
    FREELANCER = "FREELANCER"
    APPLICANT = "APPLICANT"
    COMPANY = "COMPANY"
    SUPPLIER = "SUPPLIER"


class ProjectRole(PyEnum):
    PROJECT_MANAGER = "PROJECT_MANAGER"
    PRODUCT_OWNER = "PRODUCT_OWNER"
    STAKE_HOLDER = "STAKE_HOLDER"
    ARCHITECT = "ARCHITECT"
    DEVELOPER = "DEVELOPER"
    ASSISTANT = "ASSISTANT"


class HistoryType(PyEnum):
    ADDRESS = "ADDRESS"
    CONTACT = "CONTACT"
    REQUEST = "REQUEST"
    OFFER = "OFFER"
    CONTRACT = "CONTRACT"
    APPLICATION = "APPLICATION"
    CV = "CV"
    PROJECT = "PROJECT"
    INTERVIEW = "INTERVIEW"
    COMPANY = "COMPANY"
    EMPLOYEE = "EMPLOYEE"
    WORKPACKAGE = "WORKPACKAGE"
    CAPABILITIES = "CAPABILITIES"


# Main Models
class AddressModel(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    zip_code = Column(String, nullable=False, index=True)
    country = Column(String, nullable=False)
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'ADDRESS', foreign(DocumentModel.related_id)  == AddressModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'ADDRESS', foreign(HistoryModel.related_id) == AddressModel.id)",
        viewonly=True,
    )
    __table_args__ = (
        UniqueConstraint(
            "street", "city", "zip_code", "country", name="unique_address"
        ),
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class ContactModel(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True, index=True)
    type = Column(Enum(ContactRole), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    address = relationship("AddressModel")
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'CONTACT', foreign(DocumentModel.related_id)  == ContactModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'CONTACT', foreign(HistoryModel.related_id) == ContactModel.id)",
        viewonly=True,
    )
    __table_args__ = (Index("idx_contact_name", "first_name", "last_name"),)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class SchemaModel(Base):
    __tablename__ = "schemas"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    schema_definition = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    related_type = Column(Enum(DocumentRelatedType), nullable=False)
    related_id = Column(Integer, nullable=False)
    document_name = Column(String, nullable=False)
    document_link = Column(String, nullable=False)
    document_raw_text = Column(Text, nullable=True)
    document_structured_text = Column(JSON, nullable=True)
    document_schema_reference = Column(
        Integer, ForeignKey("schemas.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "related_type", "related_id", "document_name", name="unique_document"
        ),
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class HistoryModel(Base):
    __tablename__ = "histories"
    id = Column(Integer, primary_key=True)
    related_type = Column(Enum(HistoryType), nullable=False)
    related_id = Column(Integer, nullable=False)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class SkillModel(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)

    capabilities_soft = relationship(
        "CapabilitiesModel",
        secondary="soft_skills",
        back_populates="soft_skills",
    )
    capabilities_tech = relationship(
        "CapabilitiesModel",
        secondary="tech_skills",
        back_populates="tech_skills",
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


soft_skills_table = Table(
    "soft_skills",
    Base.metadata,
    Column("capabilities_id", Integer, ForeignKey("capabilities.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)

tech_skills_table = Table(
    "tech_skills",
    Base.metadata,
    Column("capabilities_id", Integer, ForeignKey("capabilities.id"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id"), primary_key=True),
)


class CapabilitiesModel(Base):
    __tablename__ = "capabilities"
    id = Column(Integer, primary_key=True)
    soft_skills = relationship(
        "SkillModel",
        secondary=soft_skills_table,
        back_populates="capabilities_soft",
    )
    tech_skills = relationship(
        "SkillModel",
        secondary=tech_skills_table,
        back_populates="capabilities_tech",
    )

    roles = Column(
        String, nullable=True
    )  # Comma separated classification (recommendation)

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'CAPABILITIES', foreign(DocumentModel.related_id)  == CapabilitiesModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'CAPABILITIES', foreign(HistoryModel.related_id) == CapabilitiesModel.id)",
        viewonly=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class FreelancerModel(Base):
    __tablename__ = "freelancers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=False)

    capabilities_id = Column(Integer, ForeignKey("capabilities.id"))
    capabilities = relationship("CapabilitiesModel")

    role = Column(String, nullable=False)

    availability = Column(String, nullable=True)
    desired_rate_min = Column(Float, nullable=True)
    desired_rate_max = Column(Float, nullable=True)
    offer_template = Column(Text, nullable=True)
    preferred_language = Column(String, nullable=True)
    preferred_currency = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="CASCADE"))
    contact = relationship("ContactModel")

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'FREELANCER', foreign(DocumentModel.related_id)  == FreelancerModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'FREELANCER', foreign(HistoryModel.related_id) == FreelancerModel.id)",
        viewonly=True,
    )
    __table_args__ = (Index("idx_freelancer_name", "name"),)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class CVModel(Base):
    __tablename__ = "cvs"
    id = Column(Integer, primary_key=True)
    freelancer_id = Column(Integer, ForeignKey("freelancers.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    applicant_id = Column(Integer, ForeignKey("applicants.id"))
    name = Column(String, nullable=False)
    cv_raw_text = Column(Text, nullable=False)  # Raw text extracted from the document
    cv_structured_data = Column(
        JSON, nullable=False
    )  # Structured representation of the document
    cv_schema_reference = Column(
        Integer, ForeignKey("schemas.id"), nullable=False
    )  # Link to schema
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'CV', foreign(DocumentModel.related_id)  == CVModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'CV', foreign(HistoryModel.related_id) == CVModel.id)",
        viewonly=True,
    )
    freelancer = relationship("FreelancerModel", backref="cv")

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class EmployeeModel(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    capabilities_id = Column(Integer, ForeignKey("capabilities.id"))
    capabilities = relationship("CapabilitiesModel")

    role = Column(String, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact_id = Column(Integer, ForeignKey("contacts.id"))
    contact = relationship("ContactModel")

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'EMPLOYEE', foreign(DocumentModel.related_id)  == EmployeeModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'EMPLOYEE', foreign(HistoryModel.related_id) == EmployeeModel.id)",
        viewonly=True,
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class ApplicantModel(Base):
    __tablename__ = "applicants"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    capabilities_id = Column(Integer, ForeignKey("capabilities.id"))
    capabilities = relationship("CapabilitiesModel")

    role_interest = Column(String, nullable=True)

    availability = Column(String, nullable=True)
    salary_interest = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact_id = Column(Integer, ForeignKey("contacts.id"))
    contact = relationship("ContactModel")

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'APPLICANT', foreign(DocumentModel.related_id)  == ApplicantModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'APPLICANT', foreign(HistoryModel.related_id) == ApplicantModel.id)",
        viewonly=True,
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class CompanyModel(
    Base
):  # die Company der Angebot gesendet wird, für die Projekt abgearbeitet wird, zu der Interesse Kontakt besteht, zu der geschäftlicher Konatkt besteht
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=False)

    contact_id = Column(Integer, ForeignKey("contacts.id"))
    contact = relationship("ContactModel")

    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'COMPANY', foreign(DocumentModel.related_id)  == CompanyModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'COMPANY', foreign(HistoryModel.related_id) == CompanyModel.id)",
        viewonly=True,
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class RFPModel(Base):
    """
    This model represents the JSON schema "Request For Proposal" in a relational database.
    All fields from the schema are stored in a single table "rfps".
    The columns reflect the properties defined in the JSON schema, including descriptions.
    """

    __tablename__ = "rfps"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # "title" (required, non-null)
    project_title = Column(String, nullable=False, comment="The project title")

    # "description" (optional)
    description = Column(
        Text,
        nullable=True,
        comment="The project description (summarized, up to 20 lines)",
    )

    # "location" (required, can be null in the schema)
    location = Column(
        Enum(LocationType),
        nullable=True,
        comment="Expected working modality: Remote, On-site or Hybrid",
    )

    # "must-have-requirements" (required, array not null -> default=list)
    must_have_requirements = Column(
        JSON,  # oder JSONB, wenn Postgres
        nullable=False,
        default=list,
        comment="Mandatory requirements for the project",
    )

    # "nice-to-have-requirements" (required, array not null -> default=list)
    nice_to_have_requirements = Column(
        JSON, nullable=False, default=list, comment="Desirable additional requirements"
    )

    # "tasks" (required, array not null -> default=list)
    tasks = Column(
        JSON, nullable=False, default=list, comment="List of tasks in the project"
    )

    # "responsibilities" (required, array not null -> default=list)
    responsibilities = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of responsibilities in the project",
    )

    # "max-hourly-rate" (required, but can be null)
    max_hourly_rate = Column(
        Float, nullable=True, comment="Maximum hourly rate (if available)"
    )

    # "other-conditions" (required, can be null)
    other_conditions = Column(
        Text, nullable=True, comment="Other conditions or requirements"
    )

    # "contact-person" (required, can be null)
    contact_person = Column(
        String, nullable=True, comment="Contact person for the project"
    )

    # "contact-person-email" (optional)
    contact_person_email = Column(
        String,
        nullable=True,
        comment="Email of the contact person for the project (if available)",
    )

    # "project-provider" (required, can be null)
    provider = Column(String, nullable=True, comment="Project provider (if available)")

    # "project-provider-link" (required, format=uri, can be null)
    provider_link = Column(
        String, nullable=True, comment="Link to the project provider (if available)"
    )

    # "start-date" (required, can be null; format dd.mm.yyyy or mm.yyyy)
    start_date = Column(
        String, nullable=True, comment="Start date in format dd.mm.yyyy or mm.yyyy"
    )

    # "end-date" (optional, can be null; same format)
    end_date = Column(
        String, nullable=True, comment="End date in format dd.mm.yyyy or mm.yyyy"
    )

    # "duration" (optional, integer | null, minimum=1)
    duration = Column(Integer, nullable=True, comment="Duration in months")

    # "extension-option" (optional, can be "Yes", "No", or null)
    extension_option = Column(
        Enum(YesNoOption),
        nullable=True,
        comment="Option to extend the project duration",
    )

    # "original-link" (required, format=uri, can be null)
    original_link = Column(
        String, nullable=True, comment="Link to the original source of the project"
    )

    def to_dict(self):
        """Convert the model instance into a dictionary of column values."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        """Convert the model instance into a JSON string."""
        return json.dumps(self.to_dict())


class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    must_haves = Column(Text)  # Comma-separated values
    nice_to_haves = Column(Text)  # Comma-separated values
    tasks = Column(Text)
    responsibilities = Column(Text)
    hourly_rate = Column(Float)  # Corresponds to max-hourly-rate
    other_conditions = Column(Text)
    contact_person = Column(String)
    contact_person_email = Column(String)
    provider = Column(String)  # Project provider
    provider_link = Column(String)  # Project provider link
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    duration = Column(String)  # Duration in months or appropriate format
    extension_option = Column(String)  # Expected: Yes, No, or None
    original_link = Column(String, unique=True)

    status = Column(Enum(ProjectStatus), default=ProjectStatus.NEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    address_id = Column(Integer, ForeignKey("addresses.id"))

    address = relationship("AddressModel")
    interviews = relationship("InterviewModel", back_populates="project")
    contracts = relationship("ContractModel", back_populates="project")
    workpackages = relationship("WorkPackageModel", back_populates="project")
    offers = relationship("OfferModel", back_populates="project")
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'PROJECT', foreign(DocumentModel.related_id)  == ProjectModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'PROJECT', foreign(HistoryModel.related_id) == ProjectModel.id)",
        viewonly=True,
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class InterviewModel(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    date = Column(DateTime, nullable=False)
    interviewer = Column(String, nullable=False)
    notes = Column(Text)
    rating = Column(Float)
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'INTERVIEW', foreign(DocumentModel.related_id)  == InterviewModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'INTERVIEW', foreign(HistoryModel.related_id) == InterviewModel.id)",
        viewonly=True,
    )
    project = relationship("ProjectModel", back_populates="interviews")

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class ContractModel(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    contract_date = Column(DateTime, nullable=False)
    signed_by_client = Column(Boolean, default=False)
    signed_by_freelancer = Column(Boolean, default=False)

    project = relationship("ProjectModel", back_populates="contracts")
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'CONTRACT', foreign(DocumentModel.related_id)  == ContractModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'CONTRACT', foreign(HistoryModel.related_id) == ContractModel.id)",
        viewonly=True,
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class WorkPackageModel(Base):
    __tablename__ = "workpackages"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'WORKPACKAGE', foreign(DocumentModel.related_id)  == WorkPackageModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'WORKPACKAGE', foreign(HistoryModel.related_id) == WorkPackageModel.id)",
        viewonly=True,
    )
    project = relationship("ProjectModel", back_populates="workpackages")

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class OfferModel(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    offer_number = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(Enum(OfferStatus), default=OfferStatus.DRAFT)
    offer_contact_person = Column(String, nullable=False)
    offer_contact_person_email = Column(String, nullable=False)
    offer_text = Column(Text, nullable=True)  # To store detailed offer text if needed
    sent_date = Column(DateTime, nullable=True)
    last_follow_up_date = Column(DateTime, nullable=True)
    follow_up_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents = relationship(
        "DocumentModel",
        primaryjoin="and_(DocumentModel.related_type == 'OFFER', foreign(DocumentModel.related_id)  == OfferModel.id)",
        viewonly=True,
    )
    histories = relationship(
        "HistoryModel",
        primaryjoin="and_(HistoryModel.related_type == 'OFFER', foreign(HistoryModel.related_id) == OfferModel.id)",
        viewonly=True,
    )
    project = relationship("ProjectModel", back_populates="offers")

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())
