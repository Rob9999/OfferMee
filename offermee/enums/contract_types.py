from enum import Enum


class ContractType(Enum):
    CONTRACTOR = "Contractor"
    TEMPORARY_EMPLOYMENT = "ANÜ"
    PERMANENT = "Festanstellung"

    @classmethod
    def values(cls):
        return [e.value for e in cls]
