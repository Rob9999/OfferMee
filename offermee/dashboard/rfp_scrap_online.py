import streamlit as st
from offermee.scraper.upwork import UpworkScraper
from offermee.utils.international import _T
from offermee.dashboard.helpers.web_dashboard import log_info
from offermee.database.db_connection import connect_to_db
from offermee.enums.contract_types import ContractType
from offermee.enums.countries import Country
from offermee.enums.sites import Site
from offermee.scraper.freelancermap import FreelanceMapScraper


def get_title() -> str:
    return _T("Find Online")


def rfp_scrap_online_render():
    st.header(_T("Scrap Requests For Proposal (RFPs) Online"))

    # Platform selection
    platforms = ["FreelancerMap", "Upwork"]  # Add more platforms later
    platform = st.selectbox("Select Platform:", platforms)

    # Search parameters
    # Query
    query = st.text_input("Search terms (e.g., Python Developer)")
    # Location (City)
    location = st.text_input("Location (optional)")
    # Countries [Germany, Austria, Switzerland, Europe, Earth :) ]
    country_selection = st.selectbox("Select Country:", Country.values())
    # Contract Types [Contractor, Temporary Employment, Permanent Employment]
    contract_type_selection = st.selectbox(
        "Select Contract Type:", ContractType.values()
    )
    # Site ["remote", "onsite", "hybrid"]
    site_selection = st.selectbox("Select Site:", Site.values())

    max_pages = st.number_input("Max. Number of Pages", min_value=1, value=3)
    max_results = st.number_input("Max. Projects", min_value=1, value=10)
    min_hourly_rate = st.number_input("Min. Hourly Rate (€)", min_value=0, value=50)
    max_hourly_rate = st.number_input("Max. Hourly Rate (€)", min_value=0, value=100)

    # Execute scraper
    if st.button("Start Scraping"):
        if platform == "FreelancerMap":
            scraper = FreelanceMapScraper()  # "https://www.freelancermap.de"
            rfps = scraper.fetch_paginated(
                query=query,
                categories=None,
                contract_types=ContractType(contract_type_selection).name,
                remote=Site(site_selection).name,
                industries=None,
                matching_skills=None,
                countries=Country(country_selection).name,
                states=None,
                sort=1,
                max_pages=max_pages,
                max_results=max_results,
                progress=st.progress(0),
            )
            # log_debug(__name__, f"Found Projects:\n{projects}")
            # Display and save results
            if rfps:
                st.success(f"{_T('RFPs found')}: {len(rfps)}")
                for rfp in rfps:
                    st.subheader(rfp.get("title", ""))
                    st.write(f"Description: {rfp.get('description', '')}")
                    st.write(f"[Link to Project]({rfp.get('link', '')})")
            else:
                st.warning(_T("No RFPs found."))
        elif platform == "Upwork":
            scraper = UpworkScraper()
            rfps = scraper.fetch_paginated(
                query=query,
                max_pages=max_pages,
                max_results=max_results,
                progress=st.progress(0),
            )
            # Display and save results
            if rfps:
                st.success(f"{_T('RFPs found')}: {len(rfps)}")
                for rfp in rfps:
                    st.subheader(rfp.get("title", ""))
                    st.write(f"Description: {rfp.get('description', '')}")
                    st.write(f"[Link to Project]({rfp.get('link', '')})")
            else:
                st.warning(_T("No RFPs found."))
