from enum import Enum


class Status(Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    EDIT = "edit"
    VALIDATED = "validated"
    SAVED = "saved"
    DISCARDED = "discarded"
