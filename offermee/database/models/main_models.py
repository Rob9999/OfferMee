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
from offermee.utils.international import _T

# Annahme: _T ist definiert, z.B.:
# from your_translation_module import _T

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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    street = Column(String, nullable=False, info={"label": _T("Street")})
    city = Column(String, nullable=False, info={"label": _T("City")})
    zip_code = Column(
        String, nullable=False, index=True, info={"label": _T("Zip Code")}
    )
    country = Column(String, nullable=False, info={"label": _T("Country")})
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    first_name = Column(String, nullable=False, info={"label": _T("First Name")})
    last_name = Column(String, nullable=False, info={"label": _T("Last Name")})
    phone = Column(String, nullable=False, unique=True, info={"label": _T("Phone")})
    email = Column(
        String, nullable=False, unique=True, index=True, info={"label": _T("Email")}
    )
    type = Column(Enum(ContactRole), nullable=False, info={"label": _T("Type")})
    address_id = Column(
        Integer,
        ForeignKey("addresses.id", ondelete="SET NULL"),
        info={"label": _T("Address ID")},
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, info={"label": _T("Name")})
    description = Column(Text, nullable=True, info={"label": _T("Description")})
    # must be unique and shall never be overwritten, because data depends on it
    schema_definition = Column(
        JSON, nullable=False, unique=True, info={"label": _T("Schema Definition")}
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    related_type = Column(
        Enum(DocumentRelatedType), nullable=False, info={"label": _T("Related Type")}
    )
    related_id = Column(Integer, nullable=False, info={"label": _T("Related ID")})
    document_name = Column(String, nullable=False, info={"label": _T("Document Name")})
    document_link = Column(String, nullable=False, info={"label": _T("Document Link")})
    document_raw_text = Column(
        Text, nullable=True, info={"label": _T("Document Raw Text")}
    )
    document_structured_text = Column(
        JSON, nullable=True, info={"label": _T("Document Structured Text")}
    )
    document_schema_reference_id = Column(
        Integer,
        ForeignKey("schemas.id", ondelete="SET NULL"),
        nullable=True,
        info={"label": _T("Document Schema Reference ID")},
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )

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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    related_type = Column(
        Enum(HistoryType), nullable=False, info={"label": _T("Related Type")}
    )
    related_id = Column(Integer, nullable=False, info={"label": _T("Related ID")})
    description = Column(Text, info={"label": _T("Description")})
    event_date = Column(DateTime, nullable=False, info={"label": _T("Event Date")})
    created_by = Column(String, nullable=False, info={"label": _T("Created By")})
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class SkillModel(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, unique=True, info={"label": _T("Name")})
    type = Column(String, nullable=False, info={"label": _T("Type")})

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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
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
        String, nullable=True, info={"label": _T("Roles")}
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
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class FreelancerModel(Base):
    __tablename__ = "freelancers"
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, info={"label": _T("Name")})
    website = Column(String, nullable=False, info={"label": _T("Website")})
    capabilities_id = Column(
        Integer, ForeignKey("capabilities.id"), info={"label": _T("Capabilities ID")}
    )
    capabilities = relationship("CapabilitiesModel")
    role = Column(String, nullable=False, info={"label": _T("Role")})
    availability = Column(String, nullable=True, info={"label": _T("Availability")})
    desired_rate_min = Column(
        Float, nullable=True, info={"label": _T("Desired Rate Min")}
    )
    desired_rate_max = Column(
        Float, nullable=True, info={"label": _T("Desired Rate Max")}
    )
    offer_template = Column(Text, nullable=True, info={"label": _T("Offer Template")})
    preferred_language = Column(
        String, nullable=True, info={"label": _T("Preferred Language")}
    )
    preferred_currency = Column(
        String, nullable=True, info={"label": _T("Preferred Currency")}
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
    contact_id = Column(
        Integer,
        ForeignKey("contacts.id", ondelete="CASCADE"),
        info={"label": _T("Contact ID")},
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    freelancer_id = Column(
        Integer, ForeignKey("freelancers.id"), info={"label": _T("Freelancer ID")}
    )
    employee_id = Column(
        Integer, ForeignKey("employees.id"), info={"label": _T("Employee ID")}
    )
    applicant_id = Column(
        Integer, ForeignKey("applicants.id"), info={"label": _T("Applicant ID")}
    )
    name = Column(String, nullable=False, info={"label": _T("Name")})
    cv_raw_text = Column(
        Text, nullable=False, info={"label": _T("CV Raw Text")}
    )  # Raw text extracted from the document
    cv_structured_data = Column(
        JSON, nullable=False, info={"label": _T("CV Structured Data")}
    )  # Structured representation of the document
    cv_schema_reference_id = Column(
        Integer,
        ForeignKey("schemas.id"),
        nullable=False,
        info={"label": _T("CV Schema Reference ID")},
    )  # Link to schema
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, info={"label": _T("Name")})
    capabilities_id = Column(
        Integer, ForeignKey("capabilities.id"), info={"label": _T("Capabilities ID")}
    )
    capabilities = relationship("CapabilitiesModel")
    role = Column(String, nullable=False, info={"label": _T("Role")})
    start_date = Column(Date, nullable=False, info={"label": _T("Start Date")})
    end_date = Column(Date, nullable=True, info={"label": _T("End Date")})
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
    contact_id = Column(
        Integer, ForeignKey("contacts.id"), info={"label": _T("Contact ID")}
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, info={"label": _T("Name")})
    capabilities_id = Column(
        Integer, ForeignKey("capabilities.id"), info={"label": _T("Capabilities ID")}
    )
    capabilities = relationship("CapabilitiesModel")
    role_interest = Column(String, nullable=True, info={"label": _T("Role Interest")})
    availability = Column(String, nullable=True, info={"label": _T("Availability")})
    salary_interest = Column(
        String, nullable=True, info={"label": _T("Salary Interest")}
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
    contact_id = Column(
        Integer, ForeignKey("contacts.id"), info={"label": _T("Contact ID")}
    )
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


class CompanyModel(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    name = Column(String, nullable=False, info={"label": _T("Name")})
    website = Column(String, nullable=False, info={"label": _T("Website")})
    contact_id = Column(
        Integer, ForeignKey("contacts.id"), info={"label": _T("Contact ID")}
    )
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

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info={"label": _T("ID"), "read_only": True},
    )
    # "title" (required, non-null)
    project_title = Column(
        String,
        nullable=False,
        comment="The project title",
        info={"label": _T("Project Title")},
    )
    # "description" (optional)
    description = Column(
        Text,
        nullable=True,
        comment="The project description (summarized, up to 20 lines)",
        info={"label": _T("Description")},
    )
    # "location" (required, can be null in the schema)
    location = Column(
        Enum(LocationType),
        nullable=True,
        comment="Expected working modality: Remote, On-site or Hybrid",
        info={"label": _T("Location")},
    )
    # "must-have-requirements" (required, array not null -> default=list)
    must_have_requirements = Column(
        JSON,  # or JSONB if Postgres
        nullable=False,
        default=list,
        comment="Mandatory requirements for the project",
        info={"label": _T("Must-have Requirements")},
    )
    # "nice-to-have-requirements" (required, array not null -> default=list)
    nice_to_have_requirements = Column(
        JSON,
        nullable=False,
        default=list,
        comment="Desirable additional requirements",
        info={"label": _T("Nice-to-have Requirements")},
    )
    # "tasks" (required, array not null -> default=list)
    tasks = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of tasks in the project",
        info={"label": _T("Tasks")},
    )
    # "responsibilities" (required, array not null -> default=list)
    responsibilities = Column(
        JSON,
        nullable=False,
        default=list,
        comment="List of responsibilities in the project",
        info={"label": _T("Responsibilities")},
    )
    # "max-hourly-rate" (required, but can be null)
    max_hourly_rate = Column(
        Float,
        nullable=True,
        comment="Maximum hourly rate (if available)",
        info={"label": _T("Max Hourly Rate")},
    )
    # "other-conditions" (required, can be null)
    other_conditions = Column(
        Text,
        nullable=True,
        comment="Other conditions or requirements",
        info={"label": _T("Other Conditions")},
    )
    # "contact-person" (required, can be null)
    contact_person = Column(
        String,
        nullable=True,
        comment="Contact person for the project",
        info={"label": _T("Contact Person")},
    )
    # "contact-person-email" (optional)
    contact_person_email = Column(
        String,
        nullable=True,
        comment="Email of the contact person for the project (if available)",
        info={"label": _T("Contact Person Email")},
    )
    # "project-provider" (required, can be null)
    provider = Column(
        String,
        nullable=True,
        comment="Project provider (if available)",
        info={"label": _T("Provider")},
    )
    # "project-provider-link" (required, format=uri, can be null)
    provider_link = Column(
        String,
        nullable=True,
        comment="Link to the project provider (if available)",
        info={"label": _T("Provider Link")},
    )
    # "start-date" (required, can be null; format dd.mm.yyyy or mm.yyyy)
    start_date = Column(
        String,
        nullable=True,
        comment="Start date in format dd.mm.yyyy or mm.yyyy",
        info={"label": _T("Start Date")},
    )
    # "end-date" (optional, can be null; same format)
    end_date = Column(
        String,
        nullable=True,
        comment="End date in format dd.mm.yyyy or mm.yyyy",
        info={"label": _T("End Date")},
    )
    # "duration" (optional, integer | null, minimum=1)
    duration = Column(
        Integer,
        nullable=True,
        comment="Duration in months",
        info={"label": _T("Duration")},
    )
    # "extension-option" (optional, can be "Yes", "No", or null)
    extension_option = Column(
        Enum(YesNoOption),
        nullable=True,
        comment="Option to extend the project duration",
        info={"label": _T("Extension Option")},
    )
    # "original-link" (required, format=uri, can be null)
    original_link = Column(
        String,
        nullable=True,
        comment="Link to the original source of the project",
        info={"label": _T("Original Link")},
    )

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class ProjectModel(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    title = Column(String, nullable=False, info={"label": _T("Title")})
    description = Column(Text, info={"label": _T("Description")})
    location = Column(String, info={"label": _T("Location")})
    must_haves = Column(
        Text, info={"label": _T("Must Haves")}
    )  # Comma-separated values
    nice_to_haves = Column(
        Text, info={"label": _T("Nice to Haves")}
    )  # Comma-separated values
    tasks = Column(Text, info={"label": _T("Tasks")})
    responsibilities = Column(Text, info={"label": _T("Responsibilities")})
    hourly_rate = Column(
        Float, info={"label": _T("Hourly Rate")}
    )  # Corresponds to max-hourly-rate
    other_conditions = Column(Text, info={"label": _T("Other Conditions")})
    contact_person = Column(String, info={"label": _T("Contact Person")})
    contact_person_email = Column(String, info={"label": _T("Contact Person Email")})
    provider = Column(String, info={"label": _T("Provider")})  # Project provider
    provider_link = Column(
        String, info={"label": _T("Provider Link")}
    )  # Project provider link
    start_date = Column(Date, nullable=False, info={"label": _T("Start Date")})
    end_date = Column(Date, info={"label": _T("End Date")})
    duration = Column(
        String, info={"label": _T("Duration")}
    )  # Duration in months or appropriate format
    extension_option = Column(
        String, info={"label": _T("Extension Option")}
    )  # Expected: Yes, No, or None
    original_link = Column(String, unique=True, info={"label": _T("Original Link")})
    status = Column(
        Enum(ProjectStatus), default=ProjectStatus.NEW, info={"label": _T("Status")}
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
    address_id = Column(
        Integer, ForeignKey("addresses.id"), info={"label": _T("Address ID")}
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    project_id = Column(
        Integer, ForeignKey("projects.id"), info={"label": _T("Project ID")}
    )
    date = Column(DateTime, nullable=False, info={"label": _T("Date")})
    interviewer = Column(String, nullable=False, info={"label": _T("Interviewer")})
    notes = Column(Text, info={"label": _T("Notes")})
    rating = Column(Float, info={"label": _T("Rating")})
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    project_id = Column(
        Integer, ForeignKey("projects.id"), info={"label": _T("Project ID")}
    )
    contract_date = Column(
        DateTime, nullable=False, info={"label": _T("Contract Date")}
    )
    signed_by_client = Column(
        Boolean, default=False, info={"label": _T("Signed by Client")}
    )
    signed_by_freelancer = Column(
        Boolean, default=False, info={"label": _T("Signed by Freelancer")}
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    project_id = Column(
        Integer, ForeignKey("projects.id"), info={"label": _T("Project ID")}
    )
    title = Column(String, nullable=False, info={"label": _T("Title")})
    description = Column(Text, info={"label": _T("Description")})
    start_date = Column(Date, info={"label": _T("Start Date")})
    end_date = Column(Date, info={"label": _T("End Date")})
    status = Column(
        Enum(TaskStatus), default=TaskStatus.OPEN, info={"label": _T("Status")}
    )
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
    id = Column(Integer, primary_key=True, info={"label": _T("ID"), "read_only": True})
    project_id = Column(
        Integer, ForeignKey("projects.id"), info={"label": _T("Project ID")}
    )
    offer_number = Column(String, nullable=False, info={"label": _T("Offer Number")})
    title = Column(String, nullable=False, info={"label": _T("Title")})
    status = Column(
        Enum(OfferStatus), default=OfferStatus.DRAFT, info={"label": _T("Status")}
    )
    offer_contact_person = Column(
        String, nullable=False, info={"label": _T("Offer Contact Person")}
    )
    offer_contact_person_email = Column(
        String, nullable=False, info={"label": _T("Offer Contact Person Email")}
    )
    offer_text = Column(
        Text, nullable=True, info={"label": _T("Offer Text")}
    )  # To store detailed offer text if needed
    sent_date = Column(DateTime, nullable=True, info={"label": _T("Sent Date")})
    last_follow_up_date = Column(
        DateTime, nullable=True, info={"label": _T("Last Follow Up Date")}
    )
    follow_up_count = Column(
        Integer, default=0, nullable=False, info={"label": _T("Follow Up Count")}
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        info={"label": _T("Created At"), "read_only": True},
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        info={"label": _T("Updated At"), "read_only": True},
    )
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
