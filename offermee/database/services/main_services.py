# offermee/database/model_services.py
import json
from logging import Logger
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum as PyEnum

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
    def create(
        cls,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
    ):
        """
        Erstellt einen neuen Datensatz des jeweiligen Models.
        Legt automatisch einen History-Eintrag an.
        Legt optional Dokumente an, falls `documents` gesetzt ist.
        """
        with session_scope() as session:
            instance = cls.MODEL(**data)
            session.add(instance)
            session.flush()

            # History-Eintrag anlegen
            description = f"Created {cls.MODEL.__name__} with ID={instance.id}"
            _create_history_entry(
                session,
                cls.HISTORY_TYPE,
                instance.id,
                description,
                created_by=created_by,
            )

            # Dokumente anlegen (optional)
            if documents:
                _create_documents(session, cls.DOCUMENT_TYPE, instance.id, documents)

            session.commit()
            service_logger.info(description)
            return instance

    @classmethod
    def get_by_id(cls, record_id: int):
        """
        Holt einen Datensatz anhand seiner ID.
        """
        with session_scope() as session:
            return session.query(cls.MODEL).get(record_id)

    @classmethod
    def get_all(cls, limit: int = 1000):
        """
        Holt alle Datensätze, optional mit Limit.
        """
        with session_scope() as session:
            return session.query(cls.MODEL).limit(limit).all()

    @classmethod
    def get_all_by(cls, limit: int = 1000, **pattern):
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            return query.limit(limit).all()

    @classmethod
    def get_first_by(cls, **pattern):
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            return query.first()

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
    ):
        """
        Aktualisiert einen bestehenden Datensatz anhand seiner ID.
        Legt automatisch einen History-Eintrag an.
        Falls `documents` übergeben wird, werden neue Dokumente angelegt.
        (Optional könnte man hier auch existierende Dokumente überschreiben / entfernen.)
        """
        with session_scope() as session:
            instance = session.query(cls.MODEL).get(record_id)
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found."
                )
                return None

            # Felder aktualisieren
            for k, v in data.items():
                setattr(instance, k, v)
            session.flush()

            # History-Eintrag
            description = f"Updated {cls.MODEL.__name__} with ID={record_id}"
            _create_history_entry(
                session,
                cls.HISTORY_TYPE,
                record_id,
                description,
                created_by=created_by,
            )

            # Dokumente hinzufügen
            if documents:
                _create_documents(session, cls.DOCUMENT_TYPE, record_id, documents)

            session.commit()
            service_logger.info(description)
            return instance

    @classmethod
    def delete(cls, record_id: int, created_by: str = "system"):
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
                created_by=created_by,
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
    HISTORY_TYPE = "WORK_PACKAGE"
    DOCUMENT_TYPE = "WORK_PACKAGE"


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
    ) -> List[DocumentModel]:
        """
        Liest alle Dokumente aus, die mit einer bestimmten Instanz verknüpft sind.
        """
        with session_scope() as session:
            documents = (
                session.query(DocumentModel)
                .filter_by(related_type=related_type, related_id=record_id)
                .all()
            )
            return documents

    @staticmethod
    def get_history_for(hist_type: HistoryType, record_id: int) -> List[HistoryModel]:
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
            return histories

    @staticmethod
    def get_soft_skills(capabilities_id: int) -> List[SkillModel]:
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
            return capabilities.soft_skills

    @staticmethod
    def get_tech_skills(capabilities_id: int) -> List[SkillModel]:
        """
        Analog zu get_soft_skills, nur für tech_skills.
        """
        with session_scope() as session:
            capabilities: CapabilitiesModel = session.query(CapabilitiesModel).get(
                capabilities_id
            )
            if not capabilities:
                return []
            return capabilities.tech_skills

    @staticmethod
    def get_freelancer_by_name(name: str) -> FreelancerModel:
        """
        Retrieve a FreelancerModel instance by name.

        If no session is provided, a new one is created for this query.
        """
        with session_scope() as session:
            try:
                return session.query(FreelancerModel).filter_by(name=name).first()
            except Exception as e:
                service_logger.error(f"Unable to get freelancer by name '{name}': {e}")
                return None

    @staticmethod
    def get_cv_by_freelancer_id(freelancer_id: int) -> CVModel:
        """
        Retrieve a CVModel instance by freelancer_id.

        If no session is provided, a new one is created for this query.
        """
        with session_scope() as session:
            try:
                return (
                    session.query(CVModel)
                    .filter_by(freelancer_id=freelancer_id)
                    .first()
                )
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
                for project in projects:
                    session.expunge(project)
                return projects
            except Exception as e:
                service_logger.error(
                    __name__,
                    f"Error loading projects from db for status {project_status}: {e}",
                )
                return None
