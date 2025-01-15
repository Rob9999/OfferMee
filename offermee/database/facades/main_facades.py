# offermee/database/facades/freelancer_facade.py
import json
from typing import Dict, Any, List, Optional

from offermee.database.models.main_models import (
    DocumentRelatedType,
    HistoryType,
    ProjectStatus,
)
from offermee.database.services.main_services import (
    AddressService,
    ApplicantService,
    BaseService,
    CapabilitiesService,
    CompanyService,
    ContactService,
    ContractService,
    DocumentService,
    EmployeeService,
    FreelancerService,
    CVService,
    HistoryService,
    InterviewService,
    OfferService,
    ProjectService,
    ReadService,
    SchemaService,
    SkillService,
    WorkPackageService,
)
from offermee.logger import CentralLogger

facade_logger = CentralLogger.getLogger(__name__)


class BaseFacade:
    """
    Bietet generische CRUD-Methoden für ein beliebigen Service.
    Erwartet, dass in den Kindklassen der Klassen-Variablen
    SERVICE, HISTORY_TYPE und DOCUMENT_TYPE korrekt gesetzt sind.
    """

    SERVICE: BaseService = None  # z.B. AddressService
    HISTORY_TYPE = None  # z.B. "ADDRESS" oder HistoryType.ADDRESS.value
    DOCUMENT_TYPE = None  # z.B. "ADDRESS" oder DocumentRelatedType.ADDRESS.value

    @classmethod
    def create(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Nimmt ein Dict entgegen und legt einen neuen Datensatz an.
        Gibt den neu erzeugten Datensatz als Dict zurück.
        """
        created_obj = cls.SERVICE.create(
            data=data,
            documents=data.get("documents", None),
            created_by=data.get("created_by", "system"),
        )
        return created_obj.to_dict()

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Gibt den Freelancer als Dict zurück oder None, falls nicht gefunden.
        """
        obj = cls.SERVICE.get_by_id(record_id)
        if obj:
            return obj.to_dict()
        return None

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Liste aller Freelancer (als Dict) zurückgeben, optional mit Limit.
        """
        objects = cls.SERVICE.get_all(limit=limit)
        return [o.to_dict() for o in objects]

    @classmethod
    def get_all_by(cls, pattern: Dict[str, Any], limit: int = 1000):
        return cls.SERVICE.get_all_by(limit=limit, pattern=pattern)

    @classmethod
    def get_first_by(cls, pattern: Dict[str, Any]):
        return cls.SERVICE.get_first_by(pattern=pattern)

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Aktualisiert einen Datensatz anhand seiner ID.
        Gibt das aktualisierte Objekt als Dict zurück oder None bei Nichtfinden.
        """
        updated_obj = cls.SERVICE.update(
            record_id=record_id,
            data=data,
            documents=data.get("documents", None),
            created_by=data.get("updated_by", "system"),
        )
        if updated_obj:
            return updated_obj.to_dict()
        return None

    @classmethod
    def delete(cls, record_id: int) -> bool:
        """
        Löscht einen Datensatz via Service. Gibt True/False zurück, je nach Erfolg.
        """
        return cls.SERVICE.delete(record_id, created_by="system")


# ------------------------------------------------------------
# Einzelne Facades pro Modell
# ------------------------------------------------------------


# Beispiel: Address
class AddressFacade(BaseFacade):
    SERVICE = AddressService
    # Du kannst hier "ADDRESS" (String) verwenden oder das Enum.
    HISTORY_TYPE = "ADDRESS"
    DOCUMENT_TYPE = "ADDRESS"


class ContactFacade(BaseFacade):
    SERVICE = ContactService
    HISTORY_TYPE = "CONTACT"
    DOCUMENT_TYPE = "CONTACT"


class SchemaFacade(BaseFacade):
    SERVICE = SchemaService
    HISTORY_TYPE = "SCHEMA"  # so etwas gibt es im Code noch nicht - ggf. anpassen
    DOCUMENT_TYPE = "SCHEMA"  # dito


class DocumentFacade(BaseFacade):
    SERVICE = DocumentService
    HISTORY_TYPE = "DOCUMENT"  # ggf. anpassen
    DOCUMENT_TYPE = "DOCUMENT"  # selten genutzt, da Documents zu sich selbst?


class HistoryFacade(BaseFacade):
    SERVICE = HistoryService
    HISTORY_TYPE = "HISTORY"
    DOCUMENT_TYPE = "HISTORY"


class SkillFacade(BaseFacade):
    SERVICE = SkillService
    HISTORY_TYPE = "SKILL"  # so etwas gibt es noch nicht - bei Bedarf anlegen
    DOCUMENT_TYPE = "SKILL"


class CapabilitiesFacade(BaseFacade):
    SERVICE = CapabilitiesService
    HISTORY_TYPE = "CAPABILITIES"
    DOCUMENT_TYPE = "CAPABILITIES"


class FreelancerFacade(BaseFacade):
    SERVICE = FreelancerService
    HISTORY_TYPE = "FREELANCER"
    DOCUMENT_TYPE = "FREELANCER"


class CVFacade(BaseFacade):
    SERVICE = CVService
    HISTORY_TYPE = "CV"
    DOCUMENT_TYPE = "CV"


class EmployeeFacade(BaseFacade):
    SERVICE = EmployeeService
    HISTORY_TYPE = "EMPLOYEE"
    DOCUMENT_TYPE = "EMPLOYEE"


class ApplicantFacade(BaseFacade):
    SERVICE = ApplicantService
    HISTORY_TYPE = "APPLICANT"
    DOCUMENT_TYPE = "APPLICANT"


class CompanyFacade(BaseFacade):
    SERVICE = CompanyService
    HISTORY_TYPE = "COMPANY"
    DOCUMENT_TYPE = "COMPANY"


class ProjectFacade(BaseFacade):
    SERVICE = ProjectService
    HISTORY_TYPE = "PROJECT"
    DOCUMENT_TYPE = "PROJECT"


class InterviewFacade(BaseFacade):
    SERVICE = InterviewService
    HISTORY_TYPE = "INTERVIEW"
    DOCUMENT_TYPE = "INTERVIEW"


class ContractFacade(BaseFacade):
    SERVICE = ContractService
    HISTORY_TYPE = "CONTRACT"
    DOCUMENT_TYPE = "CONTRACT"


class WorkPackageFacade(BaseFacade):
    SERVICE = WorkPackageService
    HISTORY_TYPE = "WORK_PACKAGE"
    DOCUMENT_TYPE = "WORK_PACKAGE"


class OfferFacade(BaseFacade):
    SERVICE = OfferService
    HISTORY_TYPE = "OFFER"
    DOCUMENT_TYPE = "OFFER"


# ----------------------------------------------------------
# SPEZIFISCHE Lese-Hilfsmethoden
# ----------------------------------------------------------


class ReadFacade:
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
        documents = ReadService.get_documents_for(
            related_type=related_type, record_id=record_id
        )
        return [d.to_dict() for d in documents]

    @staticmethod
    def get_history_for(hist_type: HistoryType, record_id: int) -> List[Dict[str, Any]]:
        """
        Liest alle History-Einträge aus, die mit einer bestimmten Instanz verknüpft sind.
        """
        histories = ReadService.get_history_for(
            hist_type=hist_type, record_id=record_id
        )
        return [r.to_dict() for r in histories]

    @staticmethod
    def get_soft_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Gibt alle Soft-Skills (SkillModel.type == 'soft') zurück,
        die einer CapabilitiesModel-Instanz zugeordnet sind.
        Hinweis: In main_models.py verknüpfen wir CapabilitiesModel und SkillModel
        über die Tabelle `soft_skills`.
        """
        soft_skills = ReadService.get_soft_skills(capabilities_id=capabilities_id)
        return [r.to_dict() for r in soft_skills]

    @staticmethod
    def get_tech_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Analog zu get_soft_skills, nur für tech_skills.
        """
        tech_skills = ReadService.get_tech_skills(capabilities_id=capabilities_id)
        return [r.to_dict() for r in tech_skills]

    @staticmethod
    def get_freelancer_by_name(name: str) -> Dict[str, Any]:
        """
        Retrieve a FreelancerModel instance by name.

        If no session is provided, a new one is created for this query.
        """
        freelancer = ReadService.get_freelancer_by_name(name=name)
        if freelancer:
            return freelancer.to_dict()
        return None

    @staticmethod
    def get_cv_by_freelancer_id(freelancer_id: int) -> Dict[str, Any]:
        """
        Retrieve a CVModel instance by freelancer_id.

        If no session is provided, a new one is created for this query.
        """
        cv = ReadService.get_cv_by_freelancer_id(freelancer_id=freelancer_id)
        if cv:
            return cv.to_dict()
        return None

    @staticmethod
    def get_all_projects_from_db(
        project_status: ProjectStatus = ProjectStatus.NEW,
    ) -> List[Dict[str, Any]]:
        projects = ReadService.get_all_projects_from_db(project_status=project_status)
        return [r.to_dict() for r in projects]

    @staticmethod
    def load_cv_from_db(freelancer_id: int):
        cv = ReadService.get_cv_by_freelancer_id(freelancer_id=freelancer_id)
        if not cv:
            return None
        try:
            return json.loads(cv.structured_data)
        except Exception as e1:
            try:
                return json.loads(cv.structured_data.replace("'", '"'))
            except Exception as e2:
                facade_logger.error(
                    __name__,
                    f"Error parsing JSON CV for freelancer_id #{freelancer_id}: {e1} {e2}",
                )
                return None
