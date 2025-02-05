# dynamic_price_suggestions.py
from offermee.utils.config import Config
import datetime

from offermee.database.models.main_models import Industry


class DynamicPriceSuggester:

    @staticmethod
    def get_suggested_rates(freelancer: dict, rfp: dict) -> dict:
        # Beispiel: Basispreis aus Freelancer-Daten
        base_rate = freelancer.get("desired_rate_min", 0.0)

        industry = rfp.get("industry", Industry.OTHER)

        region = rfp.get("region")

        # Abrufen von Benchmark-Daten aus der Konfiguration oder externer Quelle
        # (hier als Beispiel fest kodierte Multiplikatoren)
        regional_multiplier = 1.1  # z.B. höher in bestimmten Regionen
        industry_multiplier = 1.05  # z.B. nach Branchenbenchmarks
        complexity_multiplier = 1.0
        if rfp.get("complexity") == "high":
            complexity_multiplier = 1.2
        elif rfp.get("complexity") == "medium":
            complexity_multiplier = 1.1

        # Calcuate dynamic suggestions
        hourly_rate_remote = (
            base_rate
            * regional_multiplier
            * industry_multiplier
            * complexity_multiplier
        )
        hourly_rate_onsite = (
            hourly_rate_remote * 1.2
        )  # remote +20% (Hotel, Flight, Train, Bus, Taxi, Food, Drink)
        daily_flat_rate_onsite = (  # hourly_rate_remote * 8h + 500 (Flight, Train, Bus, Taxi, Food, Drink)
            hourly_rate_remote * 8 + 500
        )
        yearly_flat_rate_onsite = (  # hourly_rate_onsite * 1680 h
            hourly_rate_onsite * 1680
        )

        return {
            "hourly_rate_remote": round(hourly_rate_remote, 2),
            "hourly_rate_onsite": round(hourly_rate_onsite, 2),
            "daily_flat_rate_onsite": round(daily_flat_rate_onsite, 2),
            "yearly_flat_rate_onsite": round(yearly_flat_rate_onsite, 2),
        }
