"""
This module provides generic CRUD services for our SQLAlchemy models.
It includes helper functions for handling history, documents, relationship
data separation, and generic CRUD operations in a BaseService class.
All comments and code are in English.
"""

from datetime import datetime
import traceback
from typing import Any, Dict, List, Tuple, Optional, Set
from dateutil import parser

from sqlalchemy import DateTime, UniqueConstraint, inspect
from sqlalchemy.orm import Session, joinedload

from offermee.database.db_connection import session_scope
from offermee.database.models.main_models import (
    AddressModel,
    ContactModel,
    IndustryModel,
    RFPModel,
    RFPSource,
    RegionModel,
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

service_logger = CentralLogger.getLogger("service")


# ------------------------------------------------------------
# Helper Functions for History and Documents
# ------------------------------------------------------------


def create_history_entry(
    session: Session,
    related_type: str,
    related_id: int,
    description: str,
    created_by: str = "system",
) -> HistoryModel:
    """
    Creates a new history entry.
    """
    history = HistoryModel(
        related_type=related_type,
        related_id=related_id,
        description=description,
        event_date=datetime.utcnow(),
        created_by=created_by,
    )
    session.add(history)
    session.flush()  # Ensures history.id is set
    return history


def create_documents(
    session: Session,
    related_type: str,
    related_id: int,
    documents: List[Dict[str, Any]],
) -> List[DocumentModel]:
    """
    Creates document entries linked to a given related type and ID.
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
            document_schema_reference_id=doc_data.get("document_schema_reference_id"),
        )
        session.add(doc)
        created_docs.append(doc)
    session.flush()
    return created_docs


# ------------------------------------------------------------
# Internal Helper Functions
# ------------------------------------------------------------


def expunge_instance(instance: Any, session: Session) -> Optional[Dict[str, Any]]:
    """
    Returns the instance's dictionary representation and expunges it from the session.
    """
    if not instance:
        return None
    data = instance.to_dict()
    session.expunge(instance)
    return data


def expunge_all(instances: List[Any], session: Session) -> List[Dict[str, Any]]:
    """
    Returns a list of dictionary representations for all instances,
    expunging each one from the session.
    """
    result = []
    for instance in instances:
        if instance:
            result.append(instance.to_dict())
            session.expunge(instance)
    return result


def separate_relationship_data(
    model: Any, data: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Separates flat column data from nested relationship data and extraneous fields.

    :return: A tuple containing:
             - flat_fields: dict of direct model fields
             - relationships_dict_data: dict of single-relationship nested data (dict values)
             - relationships_list_data: dict of list-based relationship data
             - odd_fields: fields that do not match any column or relationship
    """
    mapper = inspect(model)
    flat_fields: Dict[str, Any] = {}
    relationships_dict_data: Dict[str, Any] = {}
    relationships_list_data: Dict[str, Any] = {}
    odd_fields: Dict[str, Any] = {}

    for key, value in data.items():
        # sanatize jsonized key name to ORMized one:
        key = key.replace("-", "_")
        if key in mapper.columns.keys():
            flat_fields[key] = value
        elif key in mapper.relationships.keys():
            if isinstance(value, dict):
                relationships_dict_data[key] = value
            elif isinstance(value, list):
                relationships_list_data[key] = value
            else:
                odd_fields[key] = value
        else:
            odd_fields[key] = value

    return flat_fields, relationships_dict_data, relationships_list_data, odd_fields


def joined_load_by_id(session: Session, model: Any, record_id: int) -> Optional[Any]:
    """
    Eager-loads all relationships for the given model record.
    """
    mapper = inspect(model)
    query = session.query(model)
    for rel_name in mapper.relationships.keys():
        rel_prop = getattr(model, rel_name).property
        query = query.options(joinedload(rel_prop))
    # Use session.get() when possible. Here we simulate a get with filtering by primary key.
    # Assuming primary key column is 'id'
    return query.filter(model.id == record_id).first()


def build_nested_dict(
    model: Any, record: Any, visited: Optional[Set[Tuple[Any, int]]] = None
) -> Dict[str, Any]:
    """
    Recursively builds a nested dictionary representing the record and its related objects.
    """
    if record is None:
        return {}
    if visited is None:
        visited = set()

    rec_id = (record.__class__, record.id)
    if rec_id in visited:
        return {}
    visited.add(rec_id)

    data = record.to_dict()
    mapper = inspect(model)
    for rel_name in mapper.relationships.keys():
        related_value = getattr(record, rel_name)
        rel_prop = getattr(model, rel_name).property
        related_model = rel_prop.mapper.class_
        if related_value is None:
            data[rel_name] = None
        elif isinstance(related_value, list):
            data[rel_name] = [
                build_nested_dict(related_model, child, visited)
                for child in related_value
            ]
        else:
            data[rel_name] = build_nested_dict(related_model, related_value, visited)
    return data


def get_record_with_relations(
    session: Session, model: Any, record_id: int
) -> Optional[Dict[str, Any]]:
    """
    Loads a record with all its relationships (via joined load) and returns a nested dictionary.
    """
    record = joined_load_by_id(session, model, record_id)
    if not record:
        return None
    return build_nested_dict(model, record)


def get_primary_keys(model: Any) -> List[str]:
    """
    Returns a list of primary key column names for the given model.
    """
    mapper = inspect(model)
    return [col.key for col in mapper.primary_key]


def get_primary_keyed_record(
    session: Session, model: Any, data: Dict[str, Any], primary_keys: List[str]
) -> Optional[Any]:
    """
    Checks if a record exists based on primary key values from data.
    """
    if not primary_keys:
        return None
    query_kwargs = {}
    for pk in primary_keys:
        if pk in data:
            query_kwargs[pk] = data.get(pk)
    if query_kwargs:
        return session.query(model).filter_by(**query_kwargs).first()
    return None


def get_unique_key_constraints(model: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Retrieves unique constraints for the model.

    :return: A tuple with:
             - List of multi-column unique constraints (each as a dict with name and columns)
             - List of single-column unique keys
    """
    mapper = inspect(model)
    single_unique_keys = [
        col.key for col in mapper.columns if getattr(col, "unique", False)
    ]
    multi_unique_constraints = []
    table = mapper.local_table
    if table is not None:
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                cols = [c.name for c in constraint.columns]
                constraint_name = constraint.name or "unnamed_unique_constraint"
                if len(cols) > 1:
                    multi_unique_constraints.append(
                        {"name": constraint_name, "columns": cols}
                    )
                else:
                    if cols[0] not in single_unique_keys:
                        single_unique_keys.append(cols[0])
    return multi_unique_constraints, single_unique_keys


def get_unique_record(
    session: Session,
    model: Any,
    data: Dict[str, Any],
    unique_key_constraints: Tuple[List[Dict[str, Any]], List[str]],
) -> Optional[Any]:
    """
    Attempts to find a unique record matching the provided data using both single-column
    and multi-column unique constraints.
    """
    if not unique_key_constraints:
        return None

    multi_constraints, single_unique_keys = unique_key_constraints

    # Single-column unique check
    for col in single_unique_keys:
        if col in data:
            service_logger.debug(
                f"Checking single-unique col '{col}' with value {data[col]}"
            )
            record = session.query(model).filter_by(**{col: data[col]}).first()
            if record:
                return record

    # Multi-column unique check
    for constraint in multi_constraints:
        cols = constraint.get("columns", [])
        if all(c in data for c in cols):
            filter_kwargs = {c: data[c] for c in cols}
            service_logger.debug(
                f"Checking multi-unique '{constraint['name']}' with columns {cols} -> {filter_kwargs}"
            )
            record = session.query(model).filter_by(**filter_kwargs).first()
            if record:
                return record

    return None


def get_new_skills(
    incoming_skills: List[Dict[str, Any]], existing_skills: List[SkillModel]
) -> List[Dict[str, Any]]:
    """
    Filters out incoming skills that already exist in the existing skills list.
    Comparison is based on 'name' and 'type'.
    """
    existing_set = {(skill.name, skill.type) for skill in existing_skills}
    new_skills = [
        skill
        for skill in incoming_skills
        if (skill.get("name"), skill.get("type")) not in existing_set
    ]
    return new_skills


# ------------------------------------------------------------
# Mappings for History and Document Types
# ------------------------------------------------------------

_HISTORY_TYPE_MAPPING = {
    AddressModel: HistoryType.ADDRESS,
    ContactModel: HistoryType.CONTACT,
    OfferModel: HistoryType.OFFER,
    ContractModel: HistoryType.CONTRACT,
    ApplicantModel: HistoryType.APPLICANT,
    CVModel: HistoryType.CV,
    RFPModel: HistoryType.RFP,
    ProjectModel: HistoryType.PROJECT,
    InterviewModel: HistoryType.INTERVIEW,
    CompanyModel: HistoryType.COMPANY,
    EmployeeModel: HistoryType.EMPLOYEE,
    WorkPackageModel: HistoryType.WORKPACKAGE,
    CapabilitiesModel: HistoryType.CAPABILITIES,
}


def get_history_type(model_cls: type) -> Optional[HistoryType]:
    """
    Retrieves the history type for the given model class.
    """
    return _HISTORY_TYPE_MAPPING.get(model_cls, None)


_DOCUMENT_RELATED_TYPE_MAPPING = {
    AddressModel: DocumentRelatedType.ADDRESS,
    ContactModel: DocumentRelatedType.CONTACT,
    OfferModel: DocumentRelatedType.OFFER,
    ContractModel: DocumentRelatedType.CONTRACT,
    ApplicantModel: DocumentRelatedType.APPLICANT,
    CVModel: DocumentRelatedType.CV,
    RFPModel: DocumentRelatedType.RFP,
    ProjectModel: DocumentRelatedType.PROJECT,
    InterviewModel: DocumentRelatedType.INTERVIEW,
    CompanyModel: DocumentRelatedType.COMPANY,
    EmployeeModel: DocumentRelatedType.EMPLOYEE,
    WorkPackageModel: DocumentRelatedType.WORKPACKAGE,
    CapabilitiesModel: DocumentRelatedType.CAPABILITIES,
}


def get_document_related_type(model_cls: type) -> Optional[DocumentRelatedType]:
    """
    Retrieves the document related type for the given model class.
    """
    return _DOCUMENT_RELATED_TYPE_MAPPING.get(model_cls, None)


def handle_related_data(
    session: Session,
    model: Any,
    instance: Any,
    relationships_data: Dict[str, Any],
    handled_by: str,
) -> None:
    """
    Processes nested relationship data (assumed to be one-to-one or one-to-many)
    and updates or creates related records.
    """
    for rel_name, rel_data in relationships_data.items():
        rel_prop = getattr(model, rel_name).property
        related_model = rel_prop.mapper.class_
        unique_constraints = get_unique_key_constraints(related_model)
        primary_keys = get_primary_keys(related_model)

        if isinstance(rel_data, dict):
            related_documents = rel_data.pop("documents", None)
            related_instance = get_primary_keyed_record(
                session=session,
                model=related_model,
                data=rel_data,
                primary_keys=primary_keys,
            )
            if related_instance:
                related_instance = update_record(
                    session=session,
                    model=related_model,
                    record_id=related_instance.id,
                    data=rel_data,
                    documents=related_documents,
                    updated_by=handled_by,
                )
            else:
                related_instance = get_unique_record(
                    session=session,
                    model=related_model,
                    data=rel_data,
                    unique_key_constraints=unique_constraints,
                )
                if related_instance:
                    related_instance = update_record(
                        session=session,
                        model=related_model,
                        record_id=related_instance.id,
                        data=rel_data,
                        documents=related_documents,
                        updated_by=handled_by,
                    )
                else:
                    related_instance = create_record(
                        session=session,
                        model=related_model,
                        data=rel_data,
                        documents=related_documents,
                        created_by=handled_by,
                    )
            service_logger.debug(
                f"Appending related instance '{related_model.__name__}' to relationship '{model.__name__}.{rel_name}'"
            )
            if rel_prop.uselist:
                getattr(instance, rel_name).append(related_instance)
            else:
                setattr(instance, rel_name, related_instance)
            session.flush()

        elif isinstance(rel_data, list):
            related_instances = getattr(instance, rel_name) or []
            for rel_item in rel_data:
                if isinstance(rel_item, dict):
                    related_instance = get_primary_keyed_record(
                        session=session,
                        model=related_model,
                        data=rel_item,
                        primary_keys=primary_keys,
                    )
                    if related_instance:
                        related_instance = update_record(
                            session=session,
                            model=related_model,
                            record_id=related_instance.id,
                            data=rel_item,
                            documents=None,
                            updated_by=handled_by,
                        )
                    else:
                        related_instance = get_unique_record(
                            session=session,
                            model=related_model,
                            data=rel_item,
                            unique_key_constraints=unique_constraints,
                        )
                        if related_instance:
                            related_instance = update_record(
                                session=session,
                                model=related_model,
                                record_id=related_instance.id,
                                data=rel_item,
                                documents=None,
                                updated_by=handled_by,
                            )
                        else:
                            related_instance = create_record(
                                session=session,
                                model=related_model,
                                data=rel_item,
                                documents=None,
                                created_by=handled_by,
                            )
                    related_instances.append(related_instance)
                    session.flush()
                else:
                    raise ValueError(
                        f"Unsupported list entry type for relationship '{rel_name}': {type(rel_item)}"
                    )
            setattr(instance, rel_name, related_instances)
            session.flush()
        else:
            raise ValueError(
                f"Unsupported type for relationship '{rel_name}': {type(rel_data)}"
            )


def update_record(
    session: Session,
    model: Any,
    record_id: int,
    data: Dict[str, Any],
    documents: Optional[List[Dict[str, Any]]] = None,
    updated_by: str = "system",
) -> Optional[Any]:
    """
    Updates a record (flat fields, history, documents, and relationships) for the given model.
    """
    service_logger.info(
        f"Request to update {model.__name__} with ID={record_id}. Data: {data}, Documents: {documents}"
    )
    instance = session.get(model, record_id)
    if not instance:
        service_logger.error(f"{model.__name__} with ID={record_id} not found.")
        return None

    flat_fields, rel_dict_data, rel_list_data, odd_fields = separate_relationship_data(
        model, data
    )

    # Update flat fields
    for key, value in flat_fields.items():
        col = getattr(model, key).property.columns[0]
        if isinstance(col.type, DateTime) and isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError as e:
                service_logger.error(f"Error parsing datetime for field {key}: {e}")
                continue
        setattr(instance, key, value)
        service_logger.debug(f"Set {key} to {value}")
    session.flush()

    # Process relationship data (both dict and list)
    handle_related_data(session, model, instance, rel_dict_data, handled_by=updated_by)
    handle_related_data(session, model, instance, rel_list_data, handled_by=updated_by)

    if odd_fields:
        msg = f"Odd fields found in {model.__name__} update (ID={record_id}): {odd_fields}"
        service_logger.error(msg)
        raise ValueError(msg)

    # Create history entry if applicable
    description = f"Updated {model.__name__} (ID={record_id}). Data: {data}"
    history_type = get_history_type(model)
    if history_type:
        create_history_entry(
            session,
            related_type=history_type,
            related_id=record_id,
            description=description,
            created_by=updated_by,
        )

    # Process documents if provided
    if documents:
        document_type = get_document_related_type(model)
        if document_type:
            create_documents(
                session,
                related_type=document_type,
                related_id=record_id,
                documents=documents,
            )

    service_logger.info(description)
    return instance


def create_record(
    session: Session,
    model: Any,
    data: Dict[str, Any],
    documents: Optional[List[Dict[str, Any]]] = None,
    created_by: str = "system",
) -> Any:
    """
    Creates a new record for the given model, including handling relationships, history, and documents.
    """
    service_logger.info(
        f"Request to create {model.__name__}. Data: {data}, Documents: {documents}"
    )

    flat_fields, rel_dict_data, rel_list_data, odd_fields = separate_relationship_data(
        model, data
    )

    instance = model(**flat_fields)
    session.add(instance)
    session.flush()  # Assign primary key
    record_id = instance.id

    # Process related data
    handle_related_data(session, model, instance, rel_dict_data, handled_by=created_by)
    handle_related_data(session, model, instance, rel_list_data, handled_by=created_by)

    if odd_fields:
        msg = f"Odd fields found in {model.__name__} creation (ID={record_id}): {odd_fields}"
        service_logger.error(msg)
        raise ValueError(msg)

    description = f"Created {model.__name__} (ID={record_id}). Data: {data}"
    history_type = get_history_type(model)
    if history_type:
        create_history_entry(
            session,
            related_type=history_type,
            related_id=record_id,
            description=description,
            created_by=created_by,
        )

    if documents:
        document_type = get_document_related_type(model)
        if document_type:
            create_documents(
                session,
                related_type=document_type,
                related_id=record_id,
                documents=documents,
            )

    service_logger.info(description)
    return instance


# ------------------------------------------------------------
# Base Service for Generic CRUD Operations
# ------------------------------------------------------------


class BaseService:
    """
    Provides generic CRUD methods for any model.
    Child classes should set the class variables:
      - MODEL: the SQLAlchemy model (e.g., AddressModel)
      - HISTORY_TYPE: the corresponding history type (if applicable)
      - DOCUMENT_TYPE: the corresponding document type (if applicable)
    """

    MODEL = None  # e.g., AddressModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None

    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            instance = create_record(
                session=session,
                model=cls.MODEL,
                data=data,
                documents=documents,
                created_by=created_by,
            )
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} not created. Data: {data}, Documents: {documents}"
                )
                return None
            session.commit()
            return expunge_instance(instance, session)

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a record by its ID.
        """
        with session_scope() as session:
            record = session.get(cls.MODEL, record_id)
            return expunge_instance(record, session)

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retrieves all records, with an optional limit.
        """
        with session_scope() as session:
            instances = session.query(cls.MODEL).limit(limit).all()
            return expunge_all(instances, session)

    @classmethod
    def get_all_by(
        cls, pattern: Dict[str, Any], limit: int = 1000
    ) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)
            instances = query.limit(limit).all()
            return expunge_all(instances, session)

    @classmethod
    def get_first_by(cls, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)
            instance = query.first()
            return expunge_instance(instance, session)

    @classmethod
    def get_by_id_with_relations(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a record by ID with all related objects loaded (eager loading).
        """
        with session_scope() as session:
            return get_record_with_relations(session, cls.MODEL, record_id)

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            instance = update_record(
                session=session,
                model=cls.MODEL,
                record_id=record_id,
                data=data,
                documents=documents,
                updated_by=updated_by,
            )
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found. Data: {data}, Documents: {documents}"
                )
                return None

            # Additional relationship-specific handling could go here if needed.
            session.commit()
            return expunge_instance(instance, session)

    @classmethod
    def delete(cls, record_id: int, deleted_by: str = "system") -> bool:
        """
        Deletes a record by its ID (hard delete). Prior to deletion, a history entry is created.
        """
        with session_scope() as session:
            instance = session.get(cls.MODEL, record_id)
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found."
                )
                return False

            description = f"Deleted {cls.MODEL.__name__} with ID={record_id}"
            create_history_entry(
                session, cls.HISTORY_TYPE, record_id, description, created_by=deleted_by
            )
            session.delete(instance)
            session.commit()
            service_logger.info(description)
            return True


# ------------------------------------------------------------
# Specific Service Classes per Model
# ------------------------------------------------------------


class AddressService(BaseService):
    MODEL = AddressModel
    HISTORY_TYPE = HistoryType.ADDRESS
    DOCUMENT_TYPE = DocumentRelatedType.ADDRESS


class ContactService(BaseService):
    MODEL = ContactModel
    HISTORY_TYPE = HistoryType.CONTACT
    DOCUMENT_TYPE = DocumentRelatedType.CONTACT


class SchemaService(BaseService):
    MODEL = SchemaModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class DocumentService(BaseService):
    MODEL = DocumentModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class HistoryService(BaseService):
    MODEL = HistoryModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class SkillService(BaseService):
    MODEL = SkillModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class CapabilitiesService(BaseService):
    MODEL = CapabilitiesModel
    HISTORY_TYPE = HistoryType.CAPABILITIES
    DOCUMENT_TYPE = DocumentRelatedType.CAPABILITIES


class FreelancerService(BaseService):
    MODEL = FreelancerModel
    HISTORY_TYPE = HistoryType.FREELANCER
    DOCUMENT_TYPE = DocumentRelatedType.FREELANCER


class CVService(BaseService):
    MODEL = CVModel
    HISTORY_TYPE = HistoryType.CV
    DOCUMENT_TYPE = DocumentRelatedType.CV


class EmployeeService(BaseService):
    MODEL = EmployeeModel
    HISTORY_TYPE = HistoryType.EMPLOYEE
    DOCUMENT_TYPE = DocumentRelatedType.EMPLOYEE


class ApplicantService(BaseService):
    MODEL = ApplicantModel
    HISTORY_TYPE = HistoryType.APPLICANT
    DOCUMENT_TYPE = DocumentRelatedType.APPLICANT


class IndustryService(BaseService):
    MODEL = IndustryModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class RegionService(BaseService):
    MODEL = RegionModel
    HISTORY_TYPE = None
    DOCUMENT_TYPE = None


class CompanyService(BaseService):
    MODEL = CompanyModel
    HISTORY_TYPE = HistoryType.COMPANY
    DOCUMENT_TYPE = DocumentRelatedType.COMPANY


class RFPService(BaseService):
    MODEL = RFPModel
    HISTORY_TYPE = HistoryType.RFP
    DOCUMENT_TYPE = DocumentRelatedType.RFP


class ProjectService(BaseService):
    MODEL = ProjectModel
    HISTORY_TYPE = HistoryType.PROJECT
    DOCUMENT_TYPE = DocumentRelatedType.PROJECT


class InterviewService(BaseService):
    MODEL = InterviewModel
    HISTORY_TYPE = HistoryType.INTERVIEW
    DOCUMENT_TYPE = DocumentRelatedType.INTERVIEW


class ContractService(BaseService):
    MODEL = ContractModel
    HISTORY_TYPE = HistoryType.CONTRACT
    DOCUMENT_TYPE = DocumentRelatedType.CONTRACT


class WorkPackageService(BaseService):
    MODEL = WorkPackageModel
    HISTORY_TYPE = HistoryType.WORKPACKAGE
    DOCUMENT_TYPE = DocumentRelatedType.WORKPACKAGE


class OfferService(BaseService):
    MODEL = OfferModel
    HISTORY_TYPE = HistoryType.OFFER
    DOCUMENT_TYPE = DocumentRelatedType.OFFER


# ------------------------------------------------------------
# Additional Read and Transform Services
# ------------------------------------------------------------


class ReadService:
    """
    Service class for retrieving related entities such as documents, history, and skills.
    """

    @staticmethod
    def get_documents_for(
        related_type: DocumentRelatedType, record_id: int
    ) -> List[Dict[str, Any]]:
        with session_scope() as session:
            docs = (
                session.query(DocumentModel)
                .filter_by(related_type=related_type, related_id=record_id)
                .all()
            )
            return expunge_all(docs, session)

    @staticmethod
    def get_history_for(hist_type: HistoryType, record_id: int) -> List[Dict[str, Any]]:
        with session_scope() as session:
            if not hist_type:
                return []
            histories = (
                session.query(HistoryModel)
                .filter_by(related_type=hist_type, related_id=record_id)
                .all()
            )
            return expunge_all(histories, session)

    @staticmethod
    def get_soft_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        with session_scope() as session:
            capabilities: CapabilitiesModel = session.get(
                CapabilitiesModel, capabilities_id
            )
            if not capabilities:
                return []
            return expunge_all(capabilities.soft_skills, session)

    @staticmethod
    def get_tech_skills(capabilities_id: int) -> List[Dict[str, Any]]:
        with session_scope() as session:
            capabilities: CapabilitiesModel = session.get(
                CapabilitiesModel, capabilities_id
            )
            if not capabilities:
                return []
            return expunge_all(capabilities.tech_skills, session)

    @staticmethod
    def get_freelancer_by_name(name: str) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            try:
                freelancer = session.query(FreelancerModel).filter_by(name=name).first()
                return expunge_instance(freelancer, session)
            except Exception as e:
                service_logger.error(f"Unable to get freelancer by name '{name}': {e}")
                return None

    @staticmethod
    def get_cv_by_freelancer_id(freelancer_id: int) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            try:
                cv = (
                    session.query(CVModel)
                    .filter_by(freelancer_id=freelancer_id)
                    .first()
                )
                return expunge_instance(cv, session)
            except Exception as e:
                service_logger.error(
                    f"Unable to get CV by freelancer id '{freelancer_id}': {e}"
                )
                return None

    @staticmethod
    def get_all_projects_from_db(
        project_status: ProjectStatus = ProjectStatus.NEW,
    ) -> Optional[List[Dict[str, Any]]]:
        with session_scope() as session:
            try:
                projects = (
                    session.query(ProjectModel)
                    .filter(ProjectModel.status == project_status)
                    .all()
                )
                return expunge_all(projects, session)
            except Exception as e:
                service_logger.error(
                    f"Error loading projects from DB for status {project_status}: {e}"
                )
                return None

    @staticmethod
    def get_source_rule_unique_rfp_record(
        source: RFPSource,
        contact_person_email: Optional[str] = None,
        title: Optional[str] = None,
        original_link: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Gets depending on the source rule an unique rfp record.

            required_fields_map = {
                RFPSource.EMAIL: {"contact_person_email": contact_person_email, "title": title},
                RFPSource.ONLINE: {"original_link": original_link},
                RFPSource.MANUAL: {"provider": provider, "title": title},
            }

        Args:
            source (RFPSource): The RFPSource.
            contact_person_email (Optional[str], optional): The RFP contact person email. Defaults to None.
            title (Optional[str], optional): The RFP title. Defaults to None.
            original_link (Optional[str], optional): The RFP original link. Defaults to None.
            provider (Optional[str], optional): The RFP provider. Defaults to None.

        Raises:
            ValueError: If the source is unknown.
            ValueError: IF one of the mandatory arguments depending on the source rule above are missing.
            error: Any error. (traceback will be printed.)

        Returns:
            Optional[Dict[str, Any]]: The indentified rfp or None if none.
        """
        try:
            # Mapping which defines the required fields and their values depending on the source
            required_fields_map = {
                RFPSource.EMAIL: {
                    "contact_person_email": contact_person_email,
                    "title": title,
                },
                RFPSource.ONLINE: {"original_link": original_link},
                RFPSource.MANUAL: {"provider": provider, "title": title},
            }

            # Check if the provided source value is valid
            if source not in required_fields_map:
                raise ValueError(f"Unknown RFP source: {source}")

            # Validate the required parameters
            required_fields = required_fields_map[source]
            for field_name, value in required_fields.items():
                if not value:
                    raise ValueError(
                        f"If matching for {source}, argument '{field_name}' must not be None"
                    )

            # Use the validated dictionary as query parameters
            return RFPService.get_first_by(pattern=required_fields)
        except Exception as error:
            service_logger.error(
                f"Error retrieving RFP record for source: {source}, query: {required_fields}. Exception: {error}"
            )
            traceback.print_exception(type(error), error, error.__traceback__)
            raise error  # do not hide critical exceptions here


class TransformService:
    """
    Provides helper functions for transforming data, such as date parsing and converting lists to text.
    """

    @classmethod
    def parse_date(cls, date_str: str) -> Optional[Any]:
        """
        Parses a date string (formats like "dd.mm.yyyy" or "mm.yyyy") and returns a date object.
        """
        if not date_str:
            return None
        try:
            return parser.parse(date_str, dayfirst=True).date()
        except Exception as e:
            service_logger.error(f"Error parsing date '{date_str}': {e}")
            return None

    @classmethod
    def convert_list_to_text(cls, lst: List[str]) -> str:
        """
        Converts a list of strings to a comma-separated string.
        """
        if not lst:
            return ""
        return ", ".join(lst)

    @classmethod
    def create_project_from_rfp(
        cls,
        rfp: Dict[str, Any],
        company_id: Optional[int] = None,
        created_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Creates a ProjectModel record from an RFP dictionary.
        """
        project = ProjectModel()
        project.title = rfp.get("title")
        project.description = rfp.get("description")
        project.location = str(rfp.get("location")) if rfp.get("location") else None

        company: Optional[Dict[str, Any]] = None
        if company_id:
            company = CompanyService.get_by_id(record_id=company_id)
        if not company:
            company_data = {
                "name": rfp.get("provider"),
                "industries": [rfp.get("industry")],
                "regions": [rfp.get("region")],
                "website": rfp.get("provider_link"),
            }
            company_id = CompanyService.create(
                data=company_data, documents=None, created_by=created_by
            )
        project.company_id = company_id

        project.must_haves = cls.convert_list_to_text(rfp.get("must_have_requirements"))
        project.nice_to_haves = cls.convert_list_to_text(
            rfp.get("nice_to_have_requirements")
        )
        project.tasks = cls.convert_list_to_text(rfp.get("tasks"))
        project.responsibilities = cls.convert_list_to_text(rfp.get("responsibilities"))
        project.hourly_rate = rfp.get("max_hourly_rate")
        project.other_conditions = rfp.get("other_conditions")
        project.contact_person = rfp.get("contact_person")
        project.contact_person_email = rfp.get("contact_person_email")
        project.provider = rfp.get("provider")
        project.provider_link = rfp.get("provider_link")
        project.original_link = rfp.get("original_link")
        project.start_date = cls.parse_date(rfp.get("start_date"))
        project.end_date = cls.parse_date(rfp.get("end_date"))

        if rfp.get("duration"):
            project.duration = str(rfp.get("duration"))
        elif project.start_date and project.end_date:
            delta_months = (project.end_date.year - project.start_date.year) * 12 + (
                project.end_date.month - project.start_date.month
            )
            project.duration = str(delta_months)
        else:
            project.duration = None

        project.extension_option = (
            str(rfp.get("extension_option")) if rfp.get("extension_option") else None
        )
        project.status = ProjectStatus.NEW
        project_data = project.to_dict()
        project_data.pop("id")
        return ProjectService.create(
            data=project_data,
            created_by=created_by,
        )
