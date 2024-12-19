from enum import Enum


class OfferStatus(Enum):
    DRAFT = "Entwurf"
    SENT = "Gesendet"
    ACCEPTED = "Akzeptiert"
    REJECTED = "Abgelehnt"
