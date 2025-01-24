from enum import Enum


class Status(Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    VALIDATED = "validated"
    SAVED = "saved"
    DISCARDED = "discarded"
