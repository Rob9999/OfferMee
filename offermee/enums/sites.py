from enum import Enum


class Site(Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"

    @classmethod
    def values(cls):
        return [e.value for e in cls]
