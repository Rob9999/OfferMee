from asyncio import sleep
import datetime
from typing import Any, Dict, List
import streamlit as st
from offermee.config import Config
from offermee.dashboard.helpers.international import _T
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    join_container_path,
    log_debug,
    log_error,
    log_info,
    stop_if_not_logged_in,
)
from offermee.dashboard.widgets.selectors import render_freelancer_selection_form
from offermee.database.facades.main_facades import (
    CVFacade,
    CapabilitiesFacade,
    FreelancerFacade,
    ProjectFacade,
    ReadFacade,
)
from offermee.database.models.main_models import ProjectStatus
from offermee.enums.process_status import Status
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.matcher.price_matcher import PriceMatcher
from offermee.offers.generator import OfferGenerator
from offermee.offers.email_utils import EmailUtils
from offermee.utils.container import Container


def matches_render():
    """
    1. Select a candidate (freelancer)
    2. Check all rfps that has no offer yet
    3. Choose a rfp and write a offer using the freelancers template and conditions.
    3.1 Choose the best fit cv of the freelancer
    4. Send the offer plus the cv to the customer
    5. Repeat as long as matching rfps are available, may select another freelancer
    """
    page_title = _T("Projektmatcher & Angebotserstellung")
    st.header(page_title)
    stop_if_not_logged_in()
    log_info(__name__, "Visiting the side.")

    page_root = __name__
    container: Container = get_app_container()
    config = Config.get_instance().get_config_data()
    email_user = config.sender_email
    email_pass = config.sender_password
    server = config.smtp_server
    port = config.smtp_port
    operator = config.current_user

    # --- Initialize
    path_rfps_root = container.make_paths(
        join_container_path(page_root, "rfps"),
        typ=list,
        exists_ok=True,
        force_typ=True,
    )
    path_offers_root = container.make_paths(
        join_container_path(page_root, "offers"),
        typ=list,
        exists_ok=True,
        force_typ=True,
    )
    path_freelancers_root = container.make_paths(
        join_container_path(page_root, "freelancers"),
        typ=list,
        exists_ok=True,
        force_typ=True,
    )
    path_current_process = container.make_paths(
        join_container_path(page_root, "current_process"),
        typ=dict,
        exists_ok=True,
        force_typ=True,
    )

    rfps: List[Dict[str, Any]] = container.get_value(path_rfps_root, [])
    offers: List[Dict[str, Any]] = container.get_value(path_offers_root, [])
    freelancers: List[Dict[str, Any]] = container.get_value(path_freelancers_root, [])
    current_process: Dict[str, Any] = container.get_value(
        path_current_process, {"freelancer-id": None, "rfp-id": None, "cv-id": None}
    )
    print(any(rfp.get("status") in ["new", "analyzed", "validated"] for rfp in rfps))

    # Check if there is any new RFPs
    if (
        any(
            rfp.get("status") in [Status.NEW, Status.ANALYZED, Status.VALIDATED]
            for rfp in rfps
        )
        == False
    ):
        # fetch for new RFPs
        projects: List[Dict[str, Any]] = ProjectFacade.get_all_by(
            {"status": ProjectStatus.NEW}
        )
        projects_count = len(projects)
        for new_rfp in projects:
            new_rfp = {
                "data": new_rfp,
                "offered_cvs": [],
                "offer": None,
                "status": Status.NEW,
            }
            rfps.append(new_rfp)
        if projects_count <= 0:
            log_info(
                __name__, "No new projects in db. User must go to scrap some first."
            )
            st.warning(_T("No new RFPs stored, let’s start scraping projects!"))
            st.stop()
        else:
            log_info(__name__, f"Current new stored RFPs': {projects_count}")
            st.rerun()

    else:  # new RPS are available
        # get new RFPs
        new_rfps = [
            new_rfp
            for new_rfp in rfps
            if new_rfp.get("data", {}).get("status") == ProjectStatus.NEW
        ]
        st.success(f"{_T('Current new stored RFPs')}: {len(new_rfps)}")

        if not current_process.get("freelancer-id") or current_process.get(
            "freelancer-id"
        ) != st.session_state.get("selected_freelancer_id"):
            # select a freelancer first
            selected_freelancer_id = render_freelancer_selection_form(
                _T("Select to write offer for")
            )
            if selected_freelancer_id is None:
                return
            current_process["freelancer-id"] = selected_freelancer_id

        # get or create freelancer entry
        freelancer_entry = next(
            (
                f
                for f in freelancers
                if f.get("data", {}).get("id") == current_process.get("freelancer-id")
            ),
            None,
        )
        if freelancer_entry is None:
            freelancer_entry = {
                "data": FreelancerFacade.get_first_by(
                    {"id": current_process.get("freelancer-id")}
                ),
                "cvs": CVFacade.get_all_by(
                    {"freelancer_id": current_process.get("freelancer-id")}
                ),
            }
            freelancers.append(freelancer_entry)
        freelancer = freelancer_entry.get("data", None)
        if freelancer:
            capabilities_id = freelancer.get("capabilities_id")
            if capabilities_id is not None and not freelancer.get("capabilities", {}):
                # load capabilities
                capabilities = CapabilitiesFacade.get_by_id(capabilities_id)
                freelancer["capabilities"] = capabilities
                # load tech-skills
                capabilities["tech-skills"] = ReadFacade.get_tech_skills_list(
                    capabilities_id=capabilities_id
                )
        else:
            log_error(
                __name__,
                f"Unknwon freelancer #{current_process.get('freelancer-id')}. You may upload a CV first!",
            )
            st.error(
                f"{_T('Unknown freelancer')} #{current_process.get('freelancer-id')}. {_T('You may upload a CV first!')}"
            )
            st.stop()
        # log_debug(__name__, f"Fetched Freelancer:\n{freelancer}")
        freelancer_tech_skills = " ,".join(
            freelancer.get("capabilities", {}).get("tech-skills", [])
        )
        current_process["freelancer-tech-skills"] = freelancer_tech_skills
        st.write(f"{_T('Freelancer Tech-Skills')}:\n{freelancer_tech_skills}")
        freelancer_desired_rate = freelancer.get("desired_rate_min")
        current_process["freelance-desired-rate"] = freelancer_desired_rate
        log_info(
            __name__, f"Freelancer #{current_process.get('freelancer-id')} is found"
        )
        st.success(f"{_T('Freelancer')} {freelancer.get('name')} {_T('is found')}")
        for new_rfp_entry in new_rfps:
            new_rfp = new_rfp_entry.get("data")
            log_info(__name__, f"Matching project {new_rfp.get('title')}")
            match_score, skill_details = SkillMatcher.match_skills(
                new_rfp, freelancer_tech_skills
            )
            if new_rfp.get("hourly_rate"):
                if freelancer_desired_rate:
                    price_score = PriceMatcher.match_price(
                        new_rfp, freelancer_desired_rate
                    )
                else:
                    # freelancer would accept any rate
                    price_score = 1
            else:
                price_score = 0
            total_score = (match_score * 0.7) + (
                price_score * 0.3
            )  # Gewichtung anpassen

            st.subheader(new_rfp.get("title"))
            st.write(f"**{_T('Description')}:** {new_rfp.get('description')}")
            st.write(f"**{_T('Match Score')}:** {total_score:.2f}%")
            st.write(f"[{_T('Link to the Project')}]({new_rfp.get('original_link')})")

            with st.expander(_T("Details")):
                st.write(f"**{_T('Must-Have Skills')}:**")
                for skill, details in skill_details.items():
                    if (
                        details["matched"]
                        and new_rfp.get("must_haves")
                        and skill in new_rfp.get("must_haves").lower()
                    ):
                        st.write(f"- {skill} ({_T('Score')}: {details['score']})")
                st.write(f"**{_T('Nice-To-Have Skills')}:**")
                for skill, details in skill_details.items():
                    if (
                        details["matched"]
                        and new_rfp.get("nice_to_haves")
                        and skill in new_rfp.get("nice_to_haves").lower()
                    ):
                        st.write(f"- {skill} ({_T('Score')}: {details['score']})")
                st.write(f"**{_T('Preis-Matching-Score')}:** {price_score:.2f}%")

            if st.button(
                f"{_T('Make an offer for RFP')}: {new_rfp.get('title')}",
                key=f"make_offer_for_rfp_{new_rfp.get('id')}",
            ):
                current_process["rfp-id"] = new_rfp.get("id")

            if current_process.get("rfp-id") == new_rfp.get("id"):
                path_offer_process = join_container_path(
                    path_current_process,
                    f"offer_process_freelancer-id#{freelancer.get('id')}_rfp-id#{new_rfp.get('id')}",
                )
                path_hourly_rate_remote = join_container_path(
                    path_offer_process, f"hourly_rate_remote"
                )
                path_hourly_rate_onsite = join_container_path(
                    path_offer_process, f"hourly_rate_onsite"
                )
                path_daily_rate_onsite = join_container_path(
                    path_offer_process, f"daily_rate_onsite"
                )
                with st.container(key=f"offer_for_rfp_{new_rfp.get('id')}"):
                    freelancer_desired_rate_min = freelancer.get("desired_rate_min")
                    st.markdown(
                        f"***{_T('Making Offer for RFP')}: {new_rfp.get('title')}***"
                    )
                    container.set_value(
                        path_hourly_rate_remote,
                        st.number_input(
                            f"{_T('Hourly Rate remote in')} {_T('€')} {_T('plus VAT')}: ({_T('min')}) {freelancer_desired_rate_min:.2f}",
                            min_value=container.get_value(
                                path_hourly_rate_remote, freelancer_desired_rate_min
                            ),
                            format="%.2f",
                        ),
                    )
                    container.set_value(
                        path_hourly_rate_onsite,
                        st.number_input(
                            f"{_T('Hourly Rate onsite in')} {_T('€')} {_T('plus VAT')}: ({_T('min')} + 20%) {(freelancer_desired_rate_min*1.2):.2f}",
                            min_value=container.get_value(
                                path_hourly_rate_onsite,
                                freelancer_desired_rate_min * 1.2,
                            ),
                            format="%.2f",
                        ),
                    )
                    container.set_value(
                        path_daily_rate_onsite,
                        st.number_input(
                            f"{_T('Daily flat rate onsite throughout Germany (all-in) in')} {_T('€')} {_T('plus VAT')}: ({_T('min')} * 8h + 500 {_T('€')}) {(freelancer_desired_rate_min*8+500.00):.2f}",
                            min_value=container.get_value(
                                path_daily_rate_onsite,
                                freelancer_desired_rate_min * 8 + 500.00,
                            ),
                            format="%.2f",
                        ),
                    )
                    if st.button(_T("Apply")):
                        offer_content = OfferGenerator().generate_offer(
                            new_rfp,
                            freelancer,
                            {
                                "hourly_rate_remote": container.get_value(
                                    path_hourly_rate_remote, freelancer_desired_rate_min
                                ),
                                "hourly_rate_onsite": container.get_value(
                                    path_hourly_rate_onsite,
                                    freelancer_desired_rate_min * 1.2,
                                ),
                                "daily_rate_onsite_pauschal": container.get_value(
                                    path_daily_rate_onsite,
                                    freelancer_desired_rate_min * 8 + 500.00,
                                ),
                            },
                        )
                        final_content = st.text_area(
                            label=_T("Generated Offer"),
                            value=offer_content,
                            height=400,
                        )
                        log_info(__name__, f"Offering '{path_offer_process}' ...")

                        st.button(
                            label=_T("SEND"),
                            key=path_offer_process,
                            on_click=send_offer_callback,
                            args=(new_rfp_entry, new_rfp, final_content),
                        )


def send_offer_callback(new_rfp_entry, new_rfp, final_content):
    log_info(__name__, f"Generated offer: \n{final_content}")

    EmailUtils().send_email(
        new_rfp.get("contact_person"),
        f"Angebot für {new_rfp.get('title')}",
        final_content,
        True,
    )
    st.success(_T("Offer successfully sended!"))

    # Daten updaten:
    new_rfp["status"] = ProjectStatus.IN_PROGRESS
    new_rfp["offer_written"] = True
    new_rfp["offer"] = final_content
    new_rfp["sent"] = datetime.datetime.now()
    ProjectFacade.update(new_rfp.get("id"), new_rfp)
    new_rfp_entry["status"] = Status.SAVED
    # sleep(3)
