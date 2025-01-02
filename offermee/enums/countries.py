from enum import Enum


class Country(Enum):
    GERMANY = "Deutschland"
    AUSTRIA = "Österreich"
    SWITZERLAND = "Schweiz"
    DACH = "DACH"
    EU = "EU"
    EUROPE = "Europa"
    WORLD = "Erde"

    @classmethod
    def values(cls):
        return [e.value for e in cls]
