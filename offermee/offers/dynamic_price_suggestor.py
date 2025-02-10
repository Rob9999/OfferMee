# dynamic_price_suggestions.py

from offermee.database.models.main_models import Industry, Region

# Mappings for region and industry multipliers
# The values provided below are sample multipliers based on general assumptions.
# Adjust these values according to real-world benchmark data as needed.

REGION_MULTIPLIERS = {
    "German": 1.1,  # German states (e.g., higher cost of living in some areas)
    "DACH": 1.05,  # DACH countries (Germany, Austria, Switzerland) might be slightly lower
    "EU": 1.0,  # EU baseline
    "Earth": 0.95,  # Other parts of Earth might have lower rates
    "Space": 2.0,  # Space work (e.g., LEO or Moon) involves extreme logistics and costs
    "Other": 1.0,  # Default multiplier for undefined regions
}

INDUSTRY_MULTIPLIERS = {
    Industry.INFORMATION_TECHNOLOGY: 1.1,  # High demand in IT
    Industry.FINANCE: 1.15,  # Finance may command higher rates
    Industry.HEALTHCARE: 1.1,
    Industry.EDUCATION: 0.95,
    Industry.RETAIL: 0.9,
    Industry.MANUFACTURING: 0.95,
    Industry.TRANSPORTATION: 1.0,
    Industry.ENERGY: 1.05,
    Industry.AGRICULTURE: 0.85,
    Industry.TELECOMMUNICATIONS: 1.1,
    Industry.REAL_ESTATE: 1.0,
    Industry.HOSPITALITY: 0.9,
    Industry.CONSTRUCTION: 0.95,
    Industry.ENTERTAINMENT: 1.0,
    Industry.AUTOMOTIVE: 1.0,
    Industry.FOOD_AND_BEVERAGE: 0.9,
    Industry.CHEMICALS: 1.0,
    Industry.AEROSPACE: 1.2,  # Aerospace can be a high-cost industry
    Industry.BIOTECHNOLOGY: 1.1,
    Industry.INSURANCE: 1.0,
    Industry.MEDIA: 1.0,
    Industry.LEGAL: 1.1,
    Industry.ENVIRONMENTAL: 1.0,
    Industry.SPORTS: 1.0,
    Industry.GOVERNMENT: 0.95,
    Industry.OTHER: 1.0,
}


class DynamicPriceSuggester:
    @staticmethod
    def get_suggested_rates(freelancer: dict, rfp: dict) -> dict:
        # Example: Base rate taken from freelancer data
        base_rate = freelancer.get("desired_rate_min", 0.0)

        # Retrieve industry and region from RFP (defaulting to OTHER if not provided)
        industry = rfp.get("industry", Industry.OTHER)
        region = rfp.get("region", Region.OTHER)

        # Lookup multipliers from the mappings
        # For Region, we use the 'group' property (e.g., "German", "DACH", "EU", etc.)
        regional_multiplier = REGION_MULTIPLIERS.get(region.group, 1.0)
        # For Industry, the key is the enum member itself.
        industry_multiplier = INDUSTRY_MULTIPLIERS.get(industry, 1.0)

        # Adjust the complexity multiplier based on the project complexity (if provided)
        complexity_multiplier = 1.0
        if rfp.get("complexity") == "high":
            complexity_multiplier = 1.2
        elif rfp.get("complexity") == "medium":
            complexity_multiplier = 1.1

        # Calculate dynamic suggestions
        hourly_rate_remote = (
            base_rate
            * regional_multiplier
            * industry_multiplier
            * complexity_multiplier
        )
        # Onsite work includes additional expenses (e.g., travel, accommodation)
        hourly_rate_onsite = hourly_rate_remote * 1.2
        # Daily flat rate is based on an 8-hour workday plus fixed travel/other costs
        daily_flat_rate_onsite = hourly_rate_remote * 8 + 500
        # Yearly flat rate is based on a typical 1680 working hours per year
        yearly_flat_rate_onsite = hourly_rate_onsite * 1680

        return {
            "hourly_rate_remote": round(hourly_rate_remote, 2),
            "hourly_rate_onsite": round(hourly_rate_onsite, 2),
            "daily_flat_rate_onsite": round(daily_flat_rate_onsite, 2),
            "yearly_flat_rate_onsite": round(yearly_flat_rate_onsite, 2),
        }
