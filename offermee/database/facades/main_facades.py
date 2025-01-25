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
    def create(
        cls, data: Dict[str, Any], created_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Nimmt ein Dict entgegen und legt einen neuen Datensatz an.
        Gibt den neu erzeugten Datensatz als Dict zurück.
        """
        return cls.SERVICE.create(
            data=data,
            documents=data.get("documents", None),
            created_by=created_by,
        )

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Gibt den Freelancer als Dict zurück oder None, falls nicht gefunden.
        """
        return cls.SERVICE.get_by_id(record_id)

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Liste aller Freelancer (als Dict) zurückgeben, optional mit Limit.
        """
        return cls.SERVICE.get_all(limit=limit)

    @classmethod
    def get_all_by(
        cls, pattern: Dict[str, Any], limit: int = 1000
    ) -> List[Dict[str, Any]]:
        return cls.SERVICE.get_all_by(pattern=pattern, limit=limit)

    @classmethod
    def get_first_by(cls, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return cls.SERVICE.get_first_by(pattern=pattern)

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        """
        Aktualisiert einen Datensatz anhand seiner ID.
        Gibt das aktualisierte Objekt als Dict zurück oder None bei Nichtfinden.
        """
        return cls.SERVICE.update(
            record_id=record_id,
            data=data,
            documents=data.get("documents", None),
            updated_by=updated_by,
        )

    @classmethod
    def delete(
        cls, record_id: int, deleted_by: str = "system"
    ) -> bool:  # TODO soft_delete: bool = False,
        """
        Löscht einen Datensatz via Service. Gibt True/False zurück, je nach Erfolg.
        """
        return cls.SERVICE.delete(
            record_id, deleted_by=deleted_by
        )  # TODO soft_delete=soft_delete,


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
    HISTORY_TYPE = "WORKPACKAGE"
    DOCUMENT_TYPE = "WORKPACKAGE"


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
        return ReadService.get_documents_for(
            related_type=related_type, record_id=record_id
        )

    @staticmethod
    def get_history_for(hist_type: HistoryType, record_id: int) -> List[Dict[str, Any]]:
        """
        Liest alle History-Einträge aus, die mit einer bestimmten Instanz verknüpft sind.
        """
        return ReadService.get_history_for(hist_type=hist_type, record_id=record_id)

    @staticmethod
    def get_soft_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Gibt alle Soft-Skills (SkillModel.type == 'soft') zurück,
        die einer CapabilitiesModel-Instanz zugeordnet sind.
        Hinweis: In main_models.py verknüpfen wir CapabilitiesModel und SkillModel
        über die Tabelle `soft_skills`.
        """
        return ReadService.get_soft_skills(capabilities_id=capabilities_id)

    @staticmethod
    def get_soft_skills_list(capabilities_id: int) -> List[str]:
        """
        Gets a clean name list of all soft-skills.
        """
        soft_skills = ReadService.get_soft_skills(capabilities_id=capabilities_id)
        return [skill.get("name") for skill in soft_skills if skill]

    @staticmethod
    def get_tech_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        """
        Analog zu get_soft_skills, nur für tech_skills.
        """
        return ReadService.get_tech_skills(capabilities_id=capabilities_id)

    @staticmethod
    def get_tech_skills_list(capabilities_id: int) -> List[str]:
        """
        Gets a clean name list of all tech-skills.
        """
        tech_skills = ReadService.get_tech_skills(capabilities_id=capabilities_id)
        return [skill.get("name") for skill in tech_skills if skill]

    @staticmethod
    def get_freelancer_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a FreelancerModel instance by name.

        If no session is provided, a new one is created for this query.
        """
        return ReadService.get_freelancer_by_name(name=name)

    @staticmethod
    def get_cv_by_freelancer_id(freelancer_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a CVModel instance by freelancer_id.

        If no session is provided, a new one is created for this query.
        """
        return ReadService.get_cv_by_freelancer_id(freelancer_id=freelancer_id)

    @staticmethod
    def get_all_projects_from_db(
        project_status: ProjectStatus = ProjectStatus.NEW,
    ) -> List[Dict[str, Any]]:
        return ReadService.get_all_projects_from_db(project_status=project_status)

    @staticmethod
    def load_cv_from_db(freelancer_id: int):
        cv = ReadService.get_cv_by_freelancer_id(freelancer_id=freelancer_id)
        if not cv:
            return None
        try:
            return json.loads(cv.get("cv_structured_data"))
        except Exception as e1:
            try:
                return json.loads(cv.get("cv_structured_data").replace("'", '"'))
            except Exception as e2:
                facade_logger.error(
                    __name__,
                    f"Error parsing JSON CV for freelancer_id #{freelancer_id}: {e1} {e2}",
                )
                return None
