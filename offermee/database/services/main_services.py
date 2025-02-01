# offermee/database/model_services.py
from logging import Logger
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import UniqueConstraint, inspect
from sqlalchemy.orm import Session

from offermee.database.db_connection import session_scope
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
    session: Session,
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
    session: Session,
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


# -------------------------------------------------------------------------
# Internal code
# -------------------------------------------------------------------------
def _expunge(
    session: Session,
    instance: Any,
) -> Optional[Dict[str, Any]]:
    if not instance:
        return None
    expunged = instance.to_dict()
    session.expunge(instance)
    return expunged


def _expunge_all(
    session: Session,
    all,
) -> List[Dict[str, Any]]:
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


def _separate_relationship_data(
    model: Any,
    data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Separates flat column data from nested relationship data and odd fields (data that do not belong
    to the model and its related ones).

    :param session:      SQLAlchemy Session object
    :param model:        SQLAlchemy model class
    :param data:         Dictionary containing data that might include both direct columns and
                         relationship data
    :return:             A tuple with six elements:
                         1) flat_fields: dict of non-relational fields belonging to the model
                         2) relationships_dict_data: dict of nested single-relationship data
                         3) relationships_list_data: dict of nested list-relationship data
                         4) odd_fields: fields that do not match any column or relationship
    """
    mapper = inspect(model)

    flat_fields = {}
    relationships_dict_data = {}
    relationships_list_data = {}
    odd_fields = {}

    for key, value in data.items():
        if key in mapper.columns.keys():
            flat_fields[key] = value
        elif key in mapper.relationships.keys() and isinstance(value, dict):
            # Collect nested dicts for relationships
            relationships_dict_data[key] = value
        elif key in mapper.relationships.keys() and isinstance(value, list):
            # Collect nested lists for relationships
            relationships_list_data[key] = value
        else:
            # If key isn't a direct column or a nested dict/list for a relationship, treat it as odd
            odd_fields[key] = value

    return (
        flat_fields,
        relationships_dict_data,
        relationships_list_data,
        odd_fields,
    )


from sqlalchemy.orm import joinedload
from typing import Any, Dict, Optional


def _joined_load_by_id(session, model, record_id):
    """
    Eager-load (joined load) all relationships for `model`.
    Then fetch one record by ID. Return the record or None.
    """
    mapper = inspect(model)
    query = session.query(model)

    # For each relationship, apply a joinedload option
    for rel in mapper.relationships:
        # Optionally filter by only certain relationships
        # or skip certain ones if you don't want them all.
        query = query.options(joinedload(rel.key))

    return query.get(record_id)


def _build_nested_dict(record, visited=None) -> Dict[str, Any]:
    """
    Recursively build a dictionary for `record`,
    including all related objects.
    """
    if record is None:
        return {}

    if visited is None:
        visited = set()

    # Avoid infinite recursion: if we've seen this object before, stop.
    rec_id = (record.__class__, record.id)
    if rec_id in visited:
        return {}
    visited.add(rec_id)

    # Start with whatever your model's to_dict() does.
    # Or do it manually via object attributes.
    data = record.to_dict()

    mapper = inspect(record)
    for rel in mapper.relationships:
        rel_name = rel.key
        related_value = getattr(record, rel_name)

        if related_value is None:
            data[rel_name] = None
        elif isinstance(related_value, list):
            # This is a "one-to-many" or "many-to-many"
            data[rel_name] = [
                _build_nested_dict(child, visited)
                for child in related_value
                # If you expect large sets, you might want to limit or lazy-load here
            ]
        else:
            # This is a "many-to-one" or "one-to-one"
            data[rel_name] = _build_nested_dict(related_value, visited)

    return data


def _get_record_with_relations(session, model, record_id):
    """
    High-level function that:
      1) does a joined-load for the given model/record_id
      2) recursively builds a nested dict
    """
    record = _joined_load_by_id(session, model, record_id)
    if not record:
        return None

    return _build_nested_dict(record)


def _get_primary_keys(model: Any):
    """Retrieves information about the model's primary key column(s).

    Args:
        model (Any): _description_
    """
    mapper = inspect(model)
    # Bestimme Primärschlüssel-Felder
    # In vielen Fällen gibt es nur einen Primärschlüssel,
    # hier werden jedoch ggf. auch zusammengesetzte Primärschlüssel unterstützt.
    return [col.key for col in mapper.primary_key]


def _get_primary_keyed_record(
    session: Session, model: Any, data: Dict[str, Any], primary_keys: list
):
    if not primary_keys:
        return None
    # check for primary key constraints to determine if to update or to create
    check_if_exists_query = {}
    for primary_key in primary_keys:
        if primary_key in data.keys():
            check_if_exists_query[primary_key] = data.get(primary_key)
    if check_if_exists_query:
        return session.query(model).filter_by(**check_if_exists_query).first()
    return None


def _get_unique_key_constraints(model: Any) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Retrieves information about the model's unique table constraints and columns marked as unique."""

    mapper = inspect(model)

    # 1) Single unique key names
    single_unique_key_names = [
        col.key for col in mapper.columns if getattr(col, "unique", False) is True
    ]

    # 2) Multi unique constraints
    table = mapper.local_table
    multi_unique_constraints = []
    if table is not None:
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                # Spalten aus diesem UniqueConstraint
                constraint_cols = [c.name for c in constraint.columns]
                constraint_name = constraint.name or "unnamed_unique_constraint"

                if len(constraint_cols) > 1:
                    multi_unique_constraints.append(
                        {"name": constraint_name, "columns": constraint_cols}
                    )
                else:
                    # Falls nur eine Spalte in diesem Constraint:
                    single_col = constraint_cols[0]
                    if single_col not in single_unique_key_names:
                        single_unique_key_names.append(single_col)

    return multi_unique_constraints, single_unique_key_names


def _get_unique_record(
    session: Session,
    model: Any,
    data: Dict[str, Any],
    unique_key_constraints: Tuple[List[Dict[str, Any]], List[str]],
):
    """
    Versucht für Single-Column-Constraints und Multi-Column-Constraints
    jeweils herauszufinden, ob es einen passenden Datensatz gibt.

    Gibt das erste gefundene Objekt zurück oder None, wenn keins passt.
    """
    if not unique_key_constraints:
        return None

    multi_unique_constraints, single_unique_keys = unique_key_constraints

    # 1) Single-Column-Unique-Check
    for col in single_unique_keys:
        if col in data:
            service_logger.debug(
                f"Checking single-unique col '{col}' with value {data[col]}"
            )
            record = session.query(model).filter_by(**{col: data[col]}).first()
            if record:
                return record

    # 2) Multi-Column-Constraints
    for muc in multi_unique_constraints:
        cols = muc.get("columns", [])
        # Prüfen, ob alle dieser Spalten im data-Dict vorhanden sind
        if all(c in data for c in cols):
            # Filter auf alle diese Spalten (UND-Verknüpfung)
            filter_kwargs = {c: data[c] for c in cols}
            service_logger.debug(
                f"Checking multi-unique '{muc['name']}' with columns {cols} -> {filter_kwargs}"
            )
            record = session.query(model).filter_by(**filter_kwargs).first()
            if record:
                return record

    # Nichts gefunden
    return None


def _get_new_skills(
    incoming_skills: List[Dict[str, Any]], existing_skills: List[SkillModel]
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


_history_type_mapping = {
    AddressModel: HistoryType.ADDRESS,
    ContactModel: HistoryType.CONTACT,
    OfferModel: HistoryType.OFFER,
    ContractModel: HistoryType.CONTRACT,
    ApplicantModel: HistoryType.APPLICATION,
    CVModel: HistoryType.CV,
    ProjectModel: HistoryType.PROJECT,
    InterviewModel: HistoryType.INTERVIEW,
    CompanyModel: HistoryType.COMPANY,
    EmployeeModel: HistoryType.EMPLOYEE,
    WorkPackageModel: HistoryType.WORKPACKAGE,
    CapabilitiesModel: HistoryType.CAPABILITIES,
}


def _get_history_type(model_cls: type) -> Optional[HistoryType]:
    return _history_type_mapping.get(model_cls, None)


_document_related_type_mapping = {
    AddressModel: DocumentRelatedType.ADDRESS,
    ContactModel: DocumentRelatedType.CONTACT,
    OfferModel: DocumentRelatedType.OFFER,
    ContractModel: DocumentRelatedType.CONTRACT,
    ApplicantModel: DocumentRelatedType.APPLICATION,
    CVModel: DocumentRelatedType.CV,
    ProjectModel: DocumentRelatedType.PROJECT,
    InterviewModel: DocumentRelatedType.INTERVIEW,
    CompanyModel: DocumentRelatedType.COMPANY,
    EmployeeModel: DocumentRelatedType.EMPLOYEE,
    WorkPackageModel: DocumentRelatedType.WORKPACKAGE,
    CapabilitiesModel: DocumentRelatedType.CAPABILITIES,
}


def _get_document_related_type(model_cls: type) -> Optional[DocumentRelatedType]:
    return _document_related_type_mapping.get(model_cls, None)


def _handle_related_data(
    session: Session,
    model: Any,
    instance: Any,
    relationships_data: Dict[str, Any],
    handled_by: str,
):
    # Process nested relationships (one-to-one assumed) for updates
    for rel_name, rel_data in relationships_data.items():
        rel_prop = getattr(model, rel_name).property
        related_model = rel_prop.mapper.class_
        unique_key_constraints = _get_unique_key_constraints(model=related_model)
        primary_keys = _get_primary_keys(model=related_model)
        if isinstance(rel_data, dict):
            related_documents = (
                rel_data.pop("documents") if rel_data.get("documents") else None
            )
            # identify by primary keys constraints
            related_instance = _get_primary_keyed_record(
                session=session,
                model=related_model,
                data=rel_data,
                primary_keys=primary_keys,
            )
            if related_instance:
                related_instance = _update(
                    session=session,
                    model=related_model,
                    record_id=related_instance.id,
                    data=rel_data,
                    documents=related_documents,
                    updated_by=handled_by,
                )
            else:
                # identify by unique key constraints
                related_instance = _get_unique_record(
                    session=session,
                    model=related_model,
                    data=rel_data,
                    unique_key_constraints=unique_key_constraints,
                )
                if related_instance:
                    related_instance = _update(
                        session=session,
                        model=related_model,
                        record_id=related_instance.id,
                        data=rel_data,
                        documents=related_documents,
                        updated_by=handled_by,
                    )
                else:
                    # is a create related data request
                    related_instance = _create(
                        session=session,
                        model=related_model,
                        data=rel_data,
                        documents=related_documents,
                        created_by=handled_by,
                    )
            service_logger.debug(
                f"Appending related instance '{related_model.__name__}' to relation '{model.__name__}.{rel_name}' ..."
            )
            rel = inspect(model).relationships[rel_name]  # get relationship-definition
            if rel.uselist:
                # list relationship (One-to-Many / Many-to-Many)
                getattr(instance, rel_name).append(related_instance)
            else:
                # single relationship (One-to-One / Many-to-One)
                setattr(instance, rel_name, related_instance)
            service_logger.debug(
                f"Appended related instance '{related_model.__name__}' to relation '{model.__name__}.{rel_name}'."
            )
            session.flush()

        elif isinstance(rel_data, list):
            related_instances = getattr(instance, rel_name)
            if not related_instances:
                related_instances = []
            unique_key_constraints = _get_unique_key_constraints(model=related_model)
            primary_keys = _get_primary_keys(model=related_model)
            for rel_list_entry in rel_data:
                if isinstance(rel_list_entry, dict):
                    # identify by primary keys constraints
                    related_instance = _get_primary_keyed_record(
                        session=session,
                        model=related_model,
                        data=rel_list_entry,
                        primary_keys=primary_keys,
                    )
                    if related_instance:
                        related_instance = _update(
                            session=session,
                            model=related_model,
                            record_id=related_instance.id,
                            data=rel_list_entry,
                            documents=None,
                            updated_by=handled_by,
                        )
                    else:
                        # identify by unique key constraints
                        related_instance = _get_unique_record(
                            session=session,
                            model=related_model,
                            data=rel_list_entry,
                            unique_key_constraints=unique_key_constraints,
                        )
                        if related_instance:
                            related_instance = _update(
                                session=session,
                                model=related_model,
                                record_id=related_instance.id,
                                data=rel_list_entry,
                                documents=None,
                                updated_by=handled_by,
                            )
                        else:
                            # is a create related data request
                            related_instance = _create(
                                session=session,
                                model=related_model,
                                data=rel_list_entry,
                                documents=None,
                                created_by=handled_by,
                            )
                    related_instances.append(related_instance)
                    session.flush()
                else:
                    raise ValueError(
                        f"Unsupported list entry type: type '{type(rel_list_entry)}' of name '{rel_name}[]' with data '{rel_list_entry}'."
                    )
            service_logger.debug(
                f"Appending related instance '{related_model.__name__}' to relation '{model.__name__}.{rel_name}' ... "
            )
            setattr(instance, rel_name, related_instances)
            service_logger.debug(
                f"Appended related instance '{related_model.__name__}' to relation '{model.__name__}.{rel_name}'."
            )
            session.flush()

        else:
            raise ValueError(
                f"Unsupported value type: type '{type(rel_data)}' of name '{rel_name}' with data '{rel_data}'."
            )


def _update(
    session: Session,
    model: Any,  # the model
    record_id: int,
    data: Dict[str, Any],
    documents: Optional[List[Dict[str, Any]]] = None,
    updated_by: str = "system",
) -> Any:  # The Model
    """Basic model update (flat + history + documents)

    Args:
        session (Session): _description_
        model (Any): _description_
        data (Dict[str, Any]): _description_
        documents (Optional[List[Dict[str, Any]]], optional): _description_. Defaults to None.
        updated_by (str, optional): _description_. Defaults to "system".

    Returns:
        Any: _description_
    """
    service_logger.info(
        f"Request to update {model.__name__} with ID={record_id}:\nData:\n{data}\nDocuments\n{documents}"
    )
    instance = session.query(model).get(record_id)
    if not instance:
        service_logger.error(f"{model.__name__} with ID={record_id} not found.")
        return None

    # 1. separate into flat, related and odd data
    flat_fields, relationships_dict_data, relationships_list_data, odd_fields = (
        _separate_relationship_data(
            model=model,
            data=data,
        )
    )

    # 2. Update flat fields
    for k, v in flat_fields.items():
        setattr(instance, k, v)
        print(f"Set {k} to {v}")
    session.flush()

    # 3.1 Update or create related dict data
    _handle_related_data(
        session=session,
        model=model,
        instance=instance,
        relationships_data=relationships_dict_data,
        handled_by=updated_by,
    )

    # 3.2 Update or create related list data
    _handle_related_data(
        session=session,
        model=model,
        instance=instance,
        relationships_data=relationships_list_data,
        handled_by=updated_by,
    )

    # 4. Handle odd data
    if odd_fields:
        msg = f"{model.__name__} with ID={record_id} odd fields found:\n{odd_fields}"
        service_logger.error(msg)
        raise ValueError(msg)

    # 5. Handle History
    description = (
        f"Updated {model.__name__} with ID={record_id}:" f"\nModel Data:\n{data}"
    )
    # find history type from model
    history_type = _get_history_type(model_cls=model)
    if history_type:
        _create_history_entry(
            session=session,
            related_type=history_type,
            related_id=record_id,
            description=description,
            created_by=updated_by,
        )

    # 6. Handle Documents
    if documents:
        # find document type from model
        document_type = _get_document_related_type(model_cls=model)
        if document_type:
            _create_documents(
                session=session,
                related_type=document_type,
                related_id=record_id,
                documents=documents,
            )

    # session.commit()
    service_logger.info(description)
    return instance


def _create(
    session: Session,
    model: Any,  # the Model
    data: Dict[str, Any],
    documents: Optional[List[Dict[str, Any]]] = None,
    created_by: str = "system",
) -> Any:
    service_logger.info(
        f"Request to create {model.__name__}:\nData:\n{data}\nDocuments\n{documents}"
    )

    # 1. separate into flat, related and odd data
    flat_fields, relationships_dict_data, relationships_list_data, odd_fields = (
        _separate_relationship_data(
            model=model,
            data=data,
        )
    )

    # 2. Create main instance with flat fields
    instance = model(**flat_fields)
    session.add(instance)
    session.flush()  # Assigns primary key
    record_id = instance.id

    # 3.1 Update or create related data
    _handle_related_data(
        session=session,
        model=model,
        instance=instance,
        relationships_data=relationships_dict_data,
        handled_by=created_by,
    )

    # 3.2 Update or create related data
    _handle_related_data(
        session=session,
        model=model,
        instance=instance,
        relationships_data=relationships_list_data,
        handled_by=created_by,
    )

    # 4. Handle odd data
    if odd_fields:
        msg = f"{model.__name__} with ID={record_id} odd fields found:\n{odd_fields}"
        service_logger.error(msg)
        raise ValueError(msg)

    # 5. Handle History
    description = (
        f"Created {model.__name__} with ID={record_id}" f"\nModel Data:\n{data}"
    )
    # find history type from model
    history_type = _get_history_type(model_cls=model)
    if history_type:
        _create_history_entry(
            session=session,
            related_type=history_type,
            related_id=record_id,
            description=description,
            created_by=created_by,
        )

    # 6. Handle Documents
    if documents:
        # find document type from model
        document_type = _get_document_related_type(model_cls=model)
        if document_type:
            if documents:
                _create_documents(
                    session=session,
                    related_type=document_type,
                    related_id=record_id,
                    documents=documents,
                )

    # session.commit()
    service_logger.info(description)
    return instance


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

    # ----------------------------------------------------------------------------
    # CRUDs
    # -----------------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        created_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:

            instance = _create(
                session=session,
                model=cls.MODEL,
                data=data,
                documents=documents,
                created_by=created_by,
            )

            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} not created. Unable to create or upadte:\n{data}\n{documents}"
                )
                return None

            session.commit()
            return _expunge(
                session=session,
                instance=instance,
            )

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt einen Datensatz anhand seiner ID.
        """
        with session_scope() as session:
            record = session.query(cls.MODEL).get(record_id)
            return _expunge(
                session=session,
                instance=record,
            )

    @classmethod
    def get_all(cls, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Holt alle Datensätze, optional mit Limit.
        """
        with session_scope() as session:
            all = session.query(cls.MODEL).limit(limit).all()
            return _expunge_all(
                session=session,
                all=all,
            )

    @classmethod
    def get_all_by(
        cls, pattern: Dict[str, Any], limit: int = 1000
    ) -> List[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            all = query.limit(limit).all()
            return _expunge_all(
                session=session,
                all=all,
            )

    @classmethod
    def get_first_by(cls, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with session_scope() as session:
            query = session.query(cls.MODEL)

            # Dynamisch Filter anwenden
            for key, value in pattern.items():
                query = query.filter(getattr(cls.MODEL, key) == value)

            first = query.first()
            return _expunge(
                session=session,
                instance=first,
            )

    @classmethod
    def get_by_id_with_relations(cls, record_id: int):
        """Eager loading"""
        with session_scope as session:
            return _get_record_with_relations(
                session=session,
                model=cls.MODEL,
                record_id=record_id,
            )

    @classmethod
    def update(
        cls,
        record_id: int,
        data: Dict[str, Any],
        documents: Optional[List[Dict[str, Any]]] = None,
        updated_by: str = "system",
    ) -> Optional[Dict[str, Any]]:
        with session_scope() as session:

            instance = _update(
                session=session,
                model=cls.MODEL,
                record_id=record_id,
                data=data,
                documents=documents,
                updated_by=updated_by,
            )
            if not instance:
                service_logger.error(
                    f"{cls.MODEL.__name__} with ID={record_id} not found. Unable to update:\n{data}\n{documents}"
                )
                return None

            rel_name = ""
            rel_data = {}
            related_model = None
            if rel_name == "":
                pass
            elif rel_name == "capabilities":
                cap_data = rel_data.copy()
                soft_skills = cap_data.pop("soft_skills", [])
                tech_skills = cap_data.pop("tech_skills", [])
                capabilities_instance = (
                    session.query(CapabilitiesModel).filter_by(**cap_data).first()
                )
                # Associate soft_skills
                if not capabilities_instance:
                    capabilities_instance = related_model(**cap_data)
                    session.add(capabilities_instance)
                    session.flush()
                new_soft_skills = _get_new_skills(
                    incoming_skills=soft_skills,
                    existing_skills=capabilities_instance.soft_skills,
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
                new_tech_skills = _get_new_skills(
                    incoming_skills=tech_skills,
                    existing_skills=capabilities_instance.tech_skills,
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
                    contact_instance = related_model(**contact_data)
                    session.add(contact_instance)
                    session.flush()

                if address_data:
                    # Try to find existing address or create new
                    address_instance = (
                        session.query(AddressModel).filter_by(**address_data).first()
                    )
                    if not address_instance:
                        address_instance = AddressModel(**address_data)
                        session.add(address_instance)
                        session.flush()
                    contact_data["address_id"] = address_instance.id
                    session.flush()
                setattr(instance, rel_name, contact_instance)
                session.flush()
            elif rel_name == "offers":
                service_logger.debug(
                    f"Updating or Creating an Offer by {cls.MODEL.__name__} with ID={record_id}"
                )
                # handle offer
                offer_data: Dict[str, Any] = rel_data.copy()
                offer_search = {}
                offer_id = offer_data.get("id")
                if offer_id:
                    offer_search["id"] = offer_id
                offer_project_id = offer_data.get("project_id")
                if offer_project_id:
                    offer_search["project_id"] = offer_project_id
                offer_number = offer_data.get("offer_number")
                if offer_number:
                    offer_search["offer_number"] = offer_number
                offer_instance = (
                    session.query(OfferModel).filter_by(**offer_search).first()
                )
                if not offer_instance:
                    offer_instance = related_model(**offer_data)
                    session.add(offer_instance)
                    session.flush()
                setattr(instance, rel_name, offer_instance)
                session.flush()
            else:
                # Fallback generic one-to-one creation
                related_instance = (
                    session.query(related_model).filter_by(**rel_data).first()
                )
                if not related_instance:
                    related_instance = related_model(**rel_data)
                    session.add(related_instance)
                    session.flush()
                setattr(instance, rel_name, related_instance)
                session.flush()

            session.commit()
            return _expunge(
                session=session,
                instance=instance,
            )

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
            return _expunge_all(
                session=session,
                all=documents,
            )

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
            return _expunge_all(
                session=session,
                all=histories,
            )

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
            return _expunge_all(
                session=session,
                all=soft_skills,
            )

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
            return _expunge_all(
                session=session,
                all=tech_skills,
            )

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
                return _expunge(
                    session=session,
                    instance=freelencaer,
                )
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
                return _expunge(
                    session=session,
                    instance=cv,
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
                return _expunge_all(
                    session=session,
                    all=projects,
                )
            except Exception as e:
                service_logger.error(
                    __name__,
                    f"Error loading projects from db for status {project_status}: {e}",
                )
                return None
