# offermee/database/model_services.py
import json
from logging import Logger
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import inspect

from offermee.database.db_connection import connect_to_db, session_scope
from offermee.database.models.main_models import (
    AddressModel,
    ContactModel,
    SchemaModel,
    DocumentModel,
    HistoryModel,
    SkillModel,
    CapabilitiesModel,
    FreelancerModel,
    CVModel,
    EmployeeModel,
    ApplicantModel,
    CompanyModel,
    ProjectModel,
    InterviewModel,
    ContractModel,
    WorkPackageModel,
    OfferModel,
    HistoryType,
    DocumentRelatedType,
    ProjectStatus,
)
from offermee.logger import CentralLogger

service_logger: Logger = CentralLogger.getLogger("service")

# ------------------------------------------------------------
# Hilfsfunktionen für Dokumente & Historien
# ------------------------------------------------------------


def _create_history_entry(
    session,
    related_type: str,
    related_id: int,
    description: str,
    created_by: str = "system",
):
    """
    Legt einen Eintrag in HistoryModel an.
    """
    history = HistoryModel(
        related_type=related_type,
        related_id=related_id,
        description=description,
        event_date=datetime.utcnow(),
        created_by=created_by,
    )
    session.add(history)
    session.flush()  # damit history.id gesetzt wird
    return history


def _create_documents(
    session,
    related_type: str,
    related_id: int,
    documents: List[Dict[str, Any]],
):
    """
    Legt Dokumente in DocumentModel an, verknüpft mit related_type und related_id.
    """
    created_docs = []
    for doc_data in documents:
        doc = DocumentModel(
            related_type=related_type,
            related_id=related_id,
            document_name=doc_data.get("document_name"),
            document_link=doc_data.get("document_link"),
            document_raw_text=doc_data.get("document_raw_text"),
            document_structured_text=doc_data.get("document_structured_text"),
            document_schema_reference=doc_data.get("document_schema_reference"),
        )
        session.add(doc)
        created_docs.append(doc)
    session.flush()
    return created_docs


# ------------------------------------------------------------
# Generische CRUD-Basis-Klasse
# ------------------------------------------------------------


class BaseService:
    """
    Bietet generische CRUD-Methoden für ein beliebiges Model.
    Erwartet, dass in den Kindklassen der Klassen-Variablen
    MODEL, HISTORY_TYPE und DOCUMENT_TYPE korrekt gesetzt sind.
    """

    MODEL = None  # z.B. AddressModel
    HISTORY_TYPE = None  # z.B. "ADDRESS" oder HistoryType.ADDRESS.value
    DOCUMENT_TYPE = None  # z.B. "ADDRESS" oder DocumentRelatedType.ADDRESS.value

    @classmethod
    def _expunge(cls, instance, session) -> Optional[Dict[str, Any]]:
        if not instance:
            return None
        expunged = instance.to_dict()
        session.expunge(instance)
        return expunged

    @classmethod
    def _expunge_all(cls, all, session) -> List[Dict[str, Any]]:
        if not all:
            return []
        all_expunged = []
        for one in all:
            if not one:
                continue
            one_expunged = one.to_dict()
            session.expunge(one)
            all_expunged.append(one_expunged)
        return all_expunged

    @classmethod
    def _separate_relationship_data(
        cls, data: Dict[str, Any], session
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Separates flat column data from nested relationship data.
        Returns tuple: (flat_fields, relationships_data)
        """
        mapper = inspect(cls.MODEL)
        flat_fields = {}
        relationships_data = {}
        # service_logger.debug(
        #    f"Mapper columns keys of {cls.MODEL.__name__}:\n{', '.join(mapper.columns.keys())}"
        # )
        # Loop through provided data and separate based on model structure
        for key, value in data.items():
            if key in mapper.columns.keys():
                flat_fields[key] = value
            elif key in mapper.relationships.keys() and isinstance(value, dict):
                # Collect nested dicts for relationships
                relationships_data[key] = value
            else:
                # If key isn't a direct column or a nested dict for a relationship, treat it as flat
                flat_fields[key] = value
        return flat_fields, relationships_data

    @classmethod
    def _get_new_skills(
        cls, incoming_skills: List[Dict[str, Any]], existing_skills: List[SkillModel]
    ) -> List[Dict[str, Any]]:
        """
        Filtert aus der Liste incoming_skills jene Skills heraus, die nicht in existing_skills vorkommen.
        Vergleicht hierbei anhand von 'name' und 'type'.
        """
        # Erstelle ein Set von Tupeln (name, type) für alle existierenden Skills
        existing_set = {(skill.name, skill.type) for skill in existing_skills}

        # Filtere die eingehenden Skills, die noch nicht existieren
        new_skills = [
            skill
            for skill in incoming_skills
            if (skill.get("name"), skill.get("type")) not in existing_set
        ]
        return new_skills

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            # service_logger.info(
            #    f"creating {cls.MODEL.__name__} entry with data:\n{data}"
            # )
            # Separate flat fields from nested relationship data
            flat_fields, relationships_data = cls._separate_relationship_data(
                data, session
            )
            # service_logger.info(
            #    f"Separated data for {cls.MODEL.__name__} entry creation to:\nFlattened Data:\n{flat_fields}\nReletionsshipdata:\n{relationships_data}"
            # )
            # Create main instance with flat fields
            instance = cls.MODEL(**flat_fields)
            session.add(instance)
            session.flush()  # Assigns primary key
            # service_logger.info(
            #    f"created {cls.MODEL.__name__} flat entry with flattened Data:\n{flat_fields}"
            # )

            # Process nested relationships with specialized handling
            for rel_name, rel_data in relationships_data.items():
                rel_prop = getattr(cls.MODEL, rel_name).property
                RelatedModel = rel_prop.mapper.class_
                # service_logger.info(
                #    f"creating nested {RelatedModel.__name__} entry with Reletionsshipdata:\n{rel_data}"
                # )
                if rel_name == "capabilities":
                    # Handle capabilities separately
                    cap_data = rel_data.copy()
                    soft_skills = cap_data.pop("soft_skills", [])
                    tech_skills = cap_data.pop("tech_skills", [])
                    capabilities_instance = RelatedModel(**cap_data)
                    session.add(capabilities_instance)
                    session.flush()

                    # Associate soft_skills
                    for skill_dict in soft_skills:
                        skill = (
                            session.query(SkillModel)
                            .filter_by(name=skill_dict["name"], type=skill_dict["type"])
                            .first()
                        )
                        if not skill:
                            skill = SkillModel(**skill_dict)
                            session.add(skill)
                            session.flush()
                        capabilities_instance.soft_skills.append(skill)
                        session.flush()

                    # Associate tech_skills
                    for skill_dict in tech_skills:
                        skill = (
                            session.query(SkillModel)
                            .filter_by(name=skill_dict["name"], type=skill_dict["type"])
                            .first()
                        )
                        if not skill:
                            skill = SkillModel(**skill_dict)
                            session.add(skill)
                            session.flush()
                        capabilities_instance.tech_skills.append(skill)
                        session.flush()

                    setattr(instance, rel_name, capabilities_instance)
                    session.flush()

                elif rel_name == "contact":
                    # Handle contact and nested address
                    contact_data = rel_data.copy()
                    address_data = contact_data.pop("address", None)
                    if address_data:
                        # Try to find existing address or create new
                        address_instance = (
                            session.query(AddressModel)
                            .filter_by(**address_data)
                            .first()
                        )
                        if not address_instance:
                            address_instance = AddressModel(**address_data)
                            session.add(address_instance)
                            session.flush()
                        contact_data["address_id"] = address_instance.id

                    contact_instance = RelatedModel(**contact_data)
                    session.add(contact_instance)
                    session.flush()
                    setattr(instance, rel_name, contact_instance)
                    session.flush()

                else:
                    # Fallback generic one-to-one creation
                    related_instance = RelatedModel(**rel_data)
                    session.add(related_instance)
                    session.flush()
                    setattr(instance, rel_name, related_instance)
                    session.flush()

            # History and Documents creation
            description = f"Created {cls.MODEL.__name__} with ID={instance.id}"
            _create_history_entry(
                session,
                cls.HISTORY_TYPE,
                instance.id,
                description,
                created_by=created_by,
            )
            if documents:
                _create_documents(session, cls.DOCUMENT_TYPE, instance.id, documents)
            session.commit()
            service_logger.info(description)
            return cls._expunge(instance, session=session)

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt einen Datensatz anhand seiner ID.
        """
        with session_scope() as session:
            record = session.query(cls.MODEL).get(record_id)
            return cls._expunge(record, session=session)

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Holt alle Datensätze, optional mit Limit.
        """
        with session_scope() as session:
            all = session.query(cls.MODEL).limit(limit).all()
            return cls._expunge_all(all, session=session)

    @classmethod
    def get_all_by(cls, limit: int = 1000, **pattern) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            all = query.limit(limit).all()
            return cls._expunge_all(all, session=session)

    @classmethod
    def get_first_by(cls, **pattern) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            first = query.first()
            return cls._expunge(first, session=session)

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            instance = session.query(cls.MODEL).get(record_id)
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found."
                )
                return None

            flat_fields, relationships_data = cls._separate_relationship_data(
                data, session
            )
            # Update flat fields
            for k, v in flat_fields.items():
                setattr(instance, k, v)
            session.flush()

            # Process nested relationships (one-to-one assumed) for updates
            for rel_name, rel_data in relationships_data.items():
                rel_prop = getattr(cls.MODEL, rel_name).property
                RelatedModel = rel_prop.mapper.class_
                # service_logger.info(
                #    f"updating nested {RelatedModel.__name__} entry with Reletionsshipdata:\n{rel_data}"
                # )
                if rel_name == "capabilities":
                    cap_data = rel_data.copy()
                    soft_skills = cap_data.pop("soft_skills", [])
                    tech_skills = cap_data.pop("tech_skills", [])
                    capabilities_instance = (
                        session.query(CapabilitiesModel).filter_by(**cap_data).first()
                    )
                    # Associate soft_skills
                    if not capabilities_instance:
                        capabilities_instance = RelatedModel(**cap_data)
                        session.add(capabilities_instance)
                        session.flush()
                    new_soft_skills = cls._get_new_skills(
                        soft_skills, capabilities_instance.soft_skills
                    )
                    for skill_dict in new_soft_skills:
                        skill = (
                            session.query(SkillModel)
                            .filter_by(name=skill_dict["name"], type=skill_dict["type"])
                            .first()
                        )
                        if not skill:
                            skill = SkillModel(**skill_dict)
                            session.add(skill)
                            session.flush()
                        capabilities_instance.soft_skills.append(skill)
                        session.flush()

                    # Associate tech_skills
                    new_tech_skills = cls._get_new_skills(
                        tech_skills, capabilities_instance.tech_skills
                    )
                    for skill_dict in new_tech_skills:
                        skill = (
                            session.query(SkillModel)
                            .filter_by(name=skill_dict["name"], type=skill_dict["type"])
                            .first()
                        )
                        if not skill:
                            skill = SkillModel(**skill_dict)
                            session.add(skill)
                            session.flush()
                        capabilities_instance.tech_skills.append(skill)
                        session.flush()

                    setattr(instance, rel_name, capabilities_instance)
                    session.flush()

                elif rel_name == "contact":
                    # Handle contact and nested address
                    contact_data = rel_data.copy()
                    address_data = contact_data.pop("address", None)
                    contact_instance = (
                        session.query(ContactModel).filter_by(**contact_data).first()
                    )
                    if not contact_instance:
                        contact_instance = RelatedModel(**contact_data)
                        session.add(contact_instance)
                        session.flush()

                    if address_data:
                        # Try to find existing address or create new
                        address_instance = (
                            session.query(AddressModel)
                            .filter_by(**address_data)
                            .first()
                        )
                        if not address_instance:
                            address_instance = AddressModel(**address_data)
                            session.add(address_instance)
                            session.flush()
                        contact_data["address_id"] = address_instance.id
                        session.flush()
                    setattr(instance, rel_name, contact_instance)
                    session.flush()

                else:
                    # Fallback generic one-to-one creation
                    related_instance = (
                        session.query(RelatedModel).filter_by(**rel_data).first()
                    )
                    if not related_instance:
                        related_instance = RelatedModel(**rel_data)
                        session.add(related_instance)
                        session.flush()
                    setattr(instance, rel_name, related_instance)
                    session.flush()

            # History and Documents handling as before
            description = f"Updated {cls.MODEL.__name__} with ID={record_id}"
            _create_history_entry(
                session,
                cls.HISTORY_TYPE,
                record_id,
                description,
                created_by=updated_by,
            )
            if documents:
                _create_documents(session, cls.DOCUMENT_TYPE, record_id, documents)
            session.commit()
            service_logger.info(description)
            return cls._expunge(instance, session=session)

    @classmethod
    def delete(
        cls, record_id: int, deleted_by: str = "system"
    ) -> bool:  # TODO  soft_delete: bool = False,
        """
        Löscht einen Datensatz anhand seiner ID (Hard Delete).
        Legt zuvor einen History-Eintrag an, um DSGVO-konform das Löschen zu dokumentieren.
        """
        with session_scope() as session:
            instance = session.query(cls.MODEL).get(record_id)
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found."
                )
                return False

            description = f"Deleted {cls.MODEL.__name__} with ID={record_id}"
            _create_history_entry(
                session,
                cls.HISTORY_TYPE,
                record_id,
                description,
                created_by=deleted_by,
            )

            session.delete(instance)
            session.commit()
            service_logger.info(description)
            return True


# ------------------------------------------------------------
# Einzelne Services pro Modell
# ------------------------------------------------------------


# Beispiel: Address
class AddressService(BaseService):
    MODEL = AddressModel
    # Du kannst hier "ADDRESS" (String) verwenden oder das Enum.
    HISTORY_TYPE = "ADDRESS"
    DOCUMENT_TYPE = "ADDRESS"


class ContactService(BaseService):
    MODEL = ContactModel
    HISTORY_TYPE = "CONTACT"
    DOCUMENT_TYPE = "CONTACT"


class SchemaService(BaseService):
    MODEL = SchemaModel
    HISTORY_TYPE = "SCHEMA"  # so etwas gibt es im Code noch nicht - ggf. anpassen
    DOCUMENT_TYPE = "SCHEMA"  # dito


class DocumentService(BaseService):
    MODEL = DocumentModel
    HISTORY_TYPE = "DOCUMENT"  # ggf. anpassen
    DOCUMENT_TYPE = "DOCUMENT"  # selten genutzt, da Documents zu sich selbst?


class HistoryService(BaseService):
    MODEL = HistoryModel
    HISTORY_TYPE = "HISTORY"
    DOCUMENT_TYPE = "HISTORY"


class SkillService(BaseService):
    MODEL = SkillModel
    HISTORY_TYPE = "SKILL"  # so etwas gibt es noch nicht - bei Bedarf anlegen
    DOCUMENT_TYPE = "SKILL"


class CapabilitiesService(BaseService):
    MODEL = CapabilitiesModel
    HISTORY_TYPE = "CAPABILITIES"
    DOCUMENT_TYPE = "CAPABILITIES"


class FreelancerService(BaseService):
    MODEL = FreelancerModel
    HISTORY_TYPE = "FREELANCER"
    DOCUMENT_TYPE = "FREELANCER"


class CVService(BaseService):
    MODEL = CVModel
    HISTORY_TYPE = "CV"
    DOCUMENT_TYPE = "CV"


class EmployeeService(BaseService):
    MODEL = EmployeeModel
    HISTORY_TYPE = "EMPLOYEE"
    DOCUMENT_TYPE = "EMPLOYEE"


class ApplicantService(BaseService):
    MODEL = ApplicantModel
    HISTORY_TYPE = "APPLICANT"
    DOCUMENT_TYPE = "APPLICANT"


class CompanyService(BaseService):
    MODEL = CompanyModel
    HISTORY_TYPE = "COMPANY"
    DOCUMENT_TYPE = "COMPANY"


class ProjectService(BaseService):
    MODEL = ProjectModel
    HISTORY_TYPE = "PROJECT"
    DOCUMENT_TYPE = "PROJECT"


class InterviewService(BaseService):
    MODEL = InterviewModel
    HISTORY_TYPE = "INTERVIEW"
    DOCUMENT_TYPE = "INTERVIEW"


class ContractService(BaseService):
    MODEL = ContractModel
    HISTORY_TYPE = "CONTRACT"
    DOCUMENT_TYPE = "CONTRACT"


class WorkPackageService(BaseService):
    MODEL = WorkPackageModel
    HISTORY_TYPE = "WORKPACKAGE"
    DOCUMENT_TYPE = "WORKPACKAGE"


class OfferService(BaseService):
    MODEL = OfferModel
    HISTORY_TYPE = "OFFER"
    DOCUMENT_TYPE = "OFFER"


# ----------------------------------------------------------
# SPEZIFISCHE Lese-Hilfsmethoden
# ----------------------------------------------------------


class ReadService:
    """
    Dienst-Klasse zum Auslesen spezieller verknüpfter Entitäten,
    z.B. Dokumente, History, Soft-/Tech-Skills etc.
    """

    @staticmethod
    def get_documents_for(
        related_type: DocumentRelatedType, record_id: int
    ) -> List[Dict[str, Any]]:
        """
        Liest alle Dokumente aus, die mit einer bestimmten Instanz verknüpft sind.
        """
        with session_scope() as session:
            documents = (
                session.query(DocumentModel)
                .filter_by(related_type=related_type, related_id=record_id)
                .all()
            )
            return BaseService._expunge_all(documents, session=session)

    @staticmethod
    def get_history_for(hist_type: HistoryType, record_id: int) -> List[Dict[str, Any]]:
        """
        Liest alle History-Einträge aus, die mit einer bestimmten Instanz verknüpft sind.
        """
        with session_scope() as session:
            if not hist_type:
                return []
            histories = (
                session.query(HistoryModel)
                .filter_by(related_type=hist_type, related_id=record_id)
                .all()
            )
            return BaseService._expunge_all(histories, session=session)

    @staticmethod
    def get_soft_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Gibt alle Soft-Skills (SkillModel.type == 'soft') zurück,
        die einer CapabilitiesModel-Instanz zugeordnet sind.
        Hinweis: In main_models.py verknüpfen wir CapabilitiesModel und SkillModel
        über die Tabelle `soft_skills`.
        """
        with session_scope() as session:
            capabilities: CapabilitiesModel = session.query(CapabilitiesModel).get(
                capabilities_id
            )
            if not capabilities:
                return []
            # Durch die Relationship in main_models.py können wir direkt zugreifen:
            #   capabilities.soft_skills -> List[SkillModel]
            # Alternativ könnte man filtern, wenn SkillModel.type == "soft"
            soft_skills = capabilities.soft_skills
            return BaseService._expunge_all(soft_skills, session=session)

    @staticmethod
    def get_tech_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Analog zu get_soft_skills, nur für tech_skills.
        """
        with session_scope() as session:
            capabilities: CapabilitiesModel = session.query(CapabilitiesModel).get(
                capabilities_id
            )
            if not capabilities:
                return []
            tech_skills = capabilities.tech_skills
            return BaseService._expunge_all(tech_skills, session=session)

    @staticmethod
    def get_freelancer_by_name(name: str) -> Dict[str, Any]:
        """
        Retrieve a FreelancerModel instance by name.

        If no session is provided, a new one is created for this query.
        """
        with session_scope() as session:
            try:
                freelencaer = (
                    session.query(FreelancerModel).filter_by(name=name).first()
                )
                return BaseService._expunge(freelencaer, session=session)
            except Exception as e:
                service_logger.error(f"Unable to get freelancer by name '{name}': {e}")
                return None

    @staticmethod
    def get_cv_by_freelancer_id(freelancer_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a CVModel instance by freelancer_id.

        If no session is provided, a new one is created for this query.
        """
        with session_scope() as session:
            try:
                cv = (
                    session.query(CVModel)
                    .filter_by(freelancer_id=freelancer_id)
                    .first()
                )
                return BaseService._expunge(cv, session=session)
            except Exception as e:
                service_logger.error(
                    f"Unable to get CV by freelancer id '{freelancer_id}': {e}"
                )
                return None

    @staticmethod
    def get_all_projects_from_db(
        project_status: ProjectStatus = ProjectStatus.NEW,
    ) -> list[ProjectModel]:
        with session_scope() as session:
            try:
                projects: list[ProjectModel] = (
                    session.query(ProjectModel)
                    .filter(ProjectModel.status == project_status)
                    .all()
                )
                return BaseService._expunge_all(projects, session=session)
            except Exception as e:
                service_logger.error(
                    __name__,
                    f"Error loading projects from db for status {project_status}: {e}",
                )
                return None
