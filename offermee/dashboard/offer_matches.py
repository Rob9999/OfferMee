from asyncio import sleep
import datetime
import json
from typing import Any, Dict, List, Optional
import streamlit as st
from offermee.config import Config
from offermee.exporter.pdf_exporter import export_cv_to_pdf
from offermee.utils.international import _T
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
from offermee.database.models.main_models import OfferStatus, ProjectStatus
from offermee.enums.process_status import Status
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.matcher.price_matcher import PriceMatcher
from offermee.offers.generator import OfferGenerator
from offermee.utils.email_utils import EmailUtils
from offermee.utils.container import Container


def get_title() -> str:
    return _T("Project Matcher & Offer Creation")


def offer_matcher_render():
    """
    1. Select a candidate (freelancer)
    2. Check all rfps that has no offer yet
    3. Choose a rfp and write a offer using the freelancers template and conditions.
    3.1 Choose the best fit cv of the freelancer
    4. Send the offer plus the cv to the customer
    5. Repeat as long as matching rfps are available, may select another freelancer
    """
    page_title = get_title()
    st.header(page_title)
    stop_if_not_logged_in()
    log_info(__name__, "Visiting the side.")
    try:

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
        freelancers: List[Dict[str, Any]] = container.get_value(
            path_freelancers_root, []
        )
        current_process: Dict[str, Any] = container.get_value(
            path_current_process, {"freelancer-id": None, "rfp-id": None, "cv-id": None}
        )
        print(
            any(rfp.get("status") in ["new", "analyzed", "validated"] for rfp in rfps)
        )

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
                    if f.get("data", {}).get("id")
                    == current_process.get("freelancer-id")
                ),
                None,
            )
            if freelancer_entry is None:
                freelancer_entry = load_freelancer_data(
                    freelancer_entry=None,
                    freelancer_id=current_process.get("freelancer-id"),
                )
                freelancers.append(freelancer_entry)
            freelancer: Dict[str, Any] = freelancer_entry.get("data", None)
            cvs: List[Dict[str, Any]] = freelancer_entry.get("cvs", [])
            # log_debug(__name__, f"Fetched Freelancer:\n{freelancer}")
            freelancer_tech_skills = " ,".join(
                freelancer.get("capabilities", {}).get("tech-skills", [])
            )
            current_process["freelancer-tech-skills"] = freelancer_tech_skills
            st.write(f"{_T('Freelancer Tech-Skills')}:\n{freelancer_tech_skills}")
            freelancer_desired_rate = freelancer.get("desired_rate_min", 0.0)
            current_process["freelance-desired-rate"] = freelancer_desired_rate
            log_info(
                __name__, f"Freelancer #{current_process.get('freelancer-id')} is found"
            )
            st.success(f"{_T('Freelancer')} {freelancer.get('name')} {_T('is found')}")
            for new_rfp_entry in new_rfps:
                new_rfp = new_rfp_entry.get("data")
                log_info(__name__, f"Matching project {new_rfp.get('title')}")
                key_rfp = f"rfp#{new_rfp.get('id')}"
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
                st.write(
                    f"[{_T('Link to the Project')}]({new_rfp.get('original_link')})"
                )

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
                    key_rfp_offer = key_rfp + "_offer"
                    key_rfp_offer_freelancer = (
                        key_rfp_offer + f"_freelancer#{freelancer.get('id')}"
                    )
                    key_rfp_offer_cvs = key_rfp_offer_freelancer + f"_cvs"
                    path_offer_process = join_container_path(
                        path_current_process,
                        f"offer_process_freelancer-id#{freelancer.get('id')}_rfp-id#{new_rfp.get('id')}",
                    )
                    if freelancer_entry:
                        st.button(
                            _T("Reload Freelancer Data"),
                            on_click=load_freelancer_data,
                            args=(
                                freelancer_entry,
                                current_process.get("freelancer-id"),
                                lambda: (container.set_value(path_offer_process, None)),
                            ),
                        )
                    path_hourly_rate_remote = join_container_path(
                        path_offer_process, "hourly_rate_remote"
                    )
                    path_hourly_rate_onsite = join_container_path(
                        path_offer_process, "hourly_rate_onsite"
                    )
                    path_daily_flat_rate_onsite = join_container_path(
                        path_offer_process, "daily_flat_rate_onsite"
                    )
                    path_yearly_flat_rate_onsite = join_container_path(
                        path_offer_process, "yearly_flat_rate_onsite"
                    )
                    path_offer_template = join_container_path(
                        path_offer_process, "offer_template"
                    )
                    path_offer_content = join_container_path(
                        path_offer_process, "offer_content"
                    )
                    path_offer_language = join_container_path(
                        path_offer_process, "offer_language"
                    )
                    path_offer_currency = join_container_path(
                        path_offer_process, "offer_currency"
                    )
                    path_offer_selected_cv_id = join_container_path(
                        path_offer_process, "cv_id"
                    )
                    path_offer_selected_cv_pdf_path_name = join_container_path(
                        path_offer_process, "cv_pdf_path_name"
                    )
                    with st.container(key=key_rfp_offer_freelancer + "_container"):
                        freelancer_desired_rate_min = freelancer.get("desired_rate_min")
                        if not freelancer_desired_rate_min:
                            freelancer_desired_rate_min = 0.0
                        st.markdown(
                            f"***{_T('Making Offer for RFP')}: {new_rfp.get('title')}***"
                        )
                        adjusts_widget = st.container(
                            key=key_rfp_offer_freelancer + "_adjusts"
                        )
                        col1, col2 = adjusts_widget.columns([1, 2])
                        container.set_value(
                            path_hourly_rate_remote,
                            col1.number_input(
                                f"{_T('Hourly Rate remote in')} {_T('€')} {_T('plus VAT')}: ({_T('min')}) {freelancer_desired_rate_min:.2f}",
                                key=key_rfp_offer_freelancer + "_hourly_rate_remote",
                                value=container.get_value(
                                    path_hourly_rate_remote, freelancer_desired_rate_min
                                ),
                                format="%.2f",
                            ),
                        )
                        container.set_value(
                            path_hourly_rate_onsite,
                            col1.number_input(
                                f"{_T('Hourly Rate onsite in')} {_T('€')} {_T('plus VAT')}: ({_T('min')} + 20%) {(freelancer_desired_rate_min*1.2):.2f}",
                                key=key_rfp_offer_freelancer + "_hourly_rate_onsite",
                                value=container.get_value(
                                    path_hourly_rate_onsite,
                                    freelancer_desired_rate_min * 1.2,
                                ),
                                format="%.2f",
                            ),
                        )
                        container.set_value(
                            path_daily_flat_rate_onsite,
                            col1.number_input(
                                f"{_T('Daily flat rate onsite throughout Germany (all-in) in')} {_T('€')} {_T('plus VAT')}: ({_T('min')} * 8h + 500 {_T('€')}) {(freelancer_desired_rate_min*8+500.00):.2f}",
                                key=key_rfp_offer_freelancer
                                + "_daily_flat_rate_onsite",
                                value=container.get_value(
                                    path_daily_flat_rate_onsite,
                                    freelancer_desired_rate_min * 8 + 500.00,
                                ),
                                format="%.2f",
                            ),
                        )
                        container.set_value(
                            path_yearly_flat_rate_onsite,
                            col1.number_input(
                                f"{_T('Yearly flat rate onsite throughout Germany (all-in) in')} {_T('€')}: ({_T('min')} * 1680h {_T('€')}) {(freelancer_desired_rate_min*1680):.2f}",
                                key=key_rfp_offer_freelancer + "_yearly_rate_onsite",
                                value=container.get_value(
                                    path_yearly_flat_rate_onsite,
                                    freelancer_desired_rate_min * 1680,
                                ),
                                format="%.2f",
                            ),
                        )
                        container.set_value(
                            path_offer_language,
                            col1.select_slider(
                                f"{_T('Offer Lanuage')}: ({_T('default')} {freelancer.get('preferred_language', 'de_DE')}",
                                options=freelancer.get("languages", ["de_DE", "en_EN"]),
                                value=container.get_value(path_offer_language, "de_DE"),
                                key=key_rfp_offer_freelancer + "_offer_language",
                            ),
                        )
                        container.set_value(
                            path_offer_currency,
                            col1.select_slider(
                                f"{_T('Offer Currency')}: ({_T('default')} {freelancer.get('preferred_currency', 'EUR')}",
                                options=["EUR", "USD"],
                                value=container.get_value(path_offer_currency, "EUR"),
                                key=key_rfp_offer_freelancer + "_offer_currency",
                            ),
                        )
                        container.set_value(
                            path_offer_selected_cv_id,
                            col2.selectbox(
                                f"{_T('Select CV')}",
                                options=[cv.get("id") for cv in cvs],
                                index=next(
                                    (
                                        i
                                        for i in range(len(cvs))
                                        if cvs[i].get("id")
                                        == container.get_value(
                                            path_offer_selected_cv_id,
                                            cvs[0].get("id") if len(cvs) else None,
                                        )
                                    ),
                                    None,
                                ),
                                key=key_rfp_offer_freelancer + "_cv_id",
                            ),
                        )

                        @st.dialog(_T("View CV"), width="large")
                        def view_cv():
                            # get cv data and export it to pdf
                            selected_cv_id = container.get_value(
                                path_offer_selected_cv_id
                            )
                            path_name = export_selected_cv(
                                selected_cv_id=selected_cv_id,
                                cvs=cvs,
                            )
                            container.set_value(
                                path_offer_selected_cv_pdf_path_name, path_name
                            )
                            show_pdf(path_name)
                            if st.button(_T("OK")):
                                st.rerun()

                        col2.button(
                            label=_T("View Selected CV"),
                            on_click=view_cv,
                        )

                        container.set_value(
                            path_offer_template,
                            st.text_area(
                                _T("Freelancer's Offer Template"),
                                value=container.get_value(
                                    path_offer_template,
                                    freelancer.get("offer_template"),
                                ),
                                height=600,
                            ),
                        )
                        st.markdown("---")
                        st.html(
                            container.get_value(
                                path_offer_template, _T("No offer template")
                            )
                        )
                        st.markdown("---")

                        if st.button(_T("Apply")):
                            if not container.get_value(
                                path_offer_selected_cv_pdf_path_name
                            ):
                                container.set_value(
                                    path_offer_selected_cv_pdf_path_name,
                                    export_selected_cv(
                                        selected_cv_id=container.get_value(
                                            path_offer_selected_cv_id
                                        ),
                                        cvs=cvs,
                                    ),
                                )
                            container.set_value(
                                path_offer_content,
                                OfferGenerator().generate_html_offer(
                                    html_template=container.get_value(
                                        path_offer_template,
                                        freelancer.get("offer_template"),
                                    ),
                                    rfp=new_rfp,
                                    freelancer=freelancer,
                                    rates={
                                        "hourly_rate_remote": container.get_value(
                                            path_hourly_rate_remote,
                                            freelancer_desired_rate_min,
                                        ),
                                        "hourly_rate_onsite": container.get_value(
                                            path_hourly_rate_onsite,
                                            freelancer_desired_rate_min * 1.2,
                                        ),
                                        "daily_flat_rate_onsite": container.get_value(
                                            path_daily_flat_rate_onsite,
                                            freelancer_desired_rate_min * 8 + 500.00,
                                        ),
                                        "yearly_flat_rate_onsite": container.get_value(
                                            path_yearly_flat_rate_onsite,
                                            freelancer_desired_rate_min * 1680,
                                        ),
                                    },
                                    language=container.get_value(
                                        path_offer_language,
                                        freelancer.get("preferred_language"),
                                    ),
                                    currency=container.get_value(
                                        path_offer_currency,
                                        freelancer.get("preferred_currency"),
                                    ),
                                ),
                            )
                            st.markdown("---")
                            st.markdown(f"*** {_T('FINAL OFFER')} ***")
                            st.html(
                                container.get_value(path_offer_content, _T("NO OFFER"))
                            )
                            st.write(
                                f"{_T('Attachements')}: {container.get_value(path_offer_selected_cv_pdf_path_name)}"
                            )
                            st.markdown("---")

                            log_info(__name__, f"Offering '{path_offer_process}' ...")

                            st.button(
                                label=_T("SEND"),
                                key=path_offer_process,
                                on_click=send_offer_callback,
                                args=(
                                    new_rfp_entry,
                                    new_rfp,
                                    container.get_value(path_offer_content),
                                    [
                                        container.get_value(
                                            path_offer_selected_cv_pdf_path_name
                                        )
                                    ],
                                ),
                            )
    except Exception as e:
        log_error(__name__, f"ERROR: {e}")
        st.error(f"{_T('ERROR')}: {e}")


def export_selected_cv(selected_cv_id: int, cvs: List[Dict[str, Any]]):
    selected_cv = next(cv for cv in cvs if cv.get("id") == selected_cv_id)
    if not selected_cv:
        st.warning(_T("No CV available. Upload CV first!"))
    if st.button(_T("Continue")):
        st.rerun()
    return export_cv_to_pdf(
        selected_cv.get("name"),
        json.loads(selected_cv.get("cv_structured_data")),
    )


import base64
import streamlit as st


def show_pdf(file_path):
    log_info(__name__, f"Rendering {file_path} PDF ...")
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    # log_debug(__name__, f"base64:\n{base64_pdf}")
    pdf_display = f"""
    <iframe src="data:application/pdf;base64,{base64_pdf}" height="100%" width="100%" style="border: none;"></iframe>
    """
    st.components.v1.html(pdf_display, height=1000)
    log_info(__name__, f"Rendered {file_path} PDF.")


def load_freelancer_data(
    freelancer_entry: Optional[Dict[str, Any]],
    freelancer_id: int,
    callback: callable = None,
):
    log_info(__name__, f"Loading Freelancer #{freelancer_id} Data ...")
    if freelancer_entry is None:
        log_debug(__name__, "Is Freelancer Data First Time Loading ...")
        freelancer_entry = {}
    if not freelancer_id:
        raise ValueError(f"Missing or Invalid Freelancer Id: #{freelancer_id}")
    freelancer_entry["data"] = FreelancerFacade.get_first_by({"id": freelancer_id})
    freelancer_entry["cvs"] = CVFacade.get_all_by({"freelancer_id": freelancer_id})
    freelancer = freelancer_entry["data"]
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
            f"Unknwon Freelancer #{freelancer_id}. You may upload a CV first!",
        )
        st.error(
            f"{_T('Unknown Freelancer')} #{freelancer_id}. {_T('You may upload a CV first!')}"
        )
        st.stop()
    if callback:
        log_info(__name__, "Processing Callback ...")
        callback()
        log_info(__name__, "Processed Callback.")
    log_info(__name__, f"Loaded Freelancer #{freelancer_id} Data.")
    return freelancer_entry


def send_offer_callback(
    new_rfp_entry: Dict[str, Any],
    new_rfp: Dict[str, Any],
    final_content: str,
    attachments: List[str],
):
    log_info(__name__, f"Generated offer: \n{final_content}")

    if not new_rfp_entry:
        raise ValueError("Missing RFP Entry")
    if not new_rfp:
        raise ValueError("Misssing RFP")
    if not final_content:
        raise ValueError("Missing FINAL OFFER")
    recipient = new_rfp.get("contact_person_email")
    if not recipient:
        raise ValueError(_T("No Valid Recipient Email"))
    EmailUtils().send_email(
        recipient=recipient,
        subject=f"{_T('Offer for RFP')}: {new_rfp.get('title')}",
        body=final_content,
        is_html=True,
        attachments=attachments,
    )
    st.success(_T("Offer successfully sended!"))

    # Daten updaten:
    new_rfp["status"] = ProjectStatus.IN_PROGRESS
    new_rfp["offers"] = {
        "project_id": new_rfp.get("id"),
        "offer_number": datetime.date.today().isoformat(),
        "title": new_rfp.get("title"),
        "status": OfferStatus.SENT,
        "offer_contact_person": new_rfp.get("contact_person"),
        "offer_contact_person_email": new_rfp.get("contact_person_email"),
        "offer_text": final_content,
        "sent_date": datetime.datetime.now(),
    }
    ProjectFacade.update(new_rfp.get("id"), new_rfp)
    new_rfp_entry["offer_written"] = True
    new_rfp_entry["sent"] = datetime.datetime.now()
    new_rfp_entry["status"] = Status.SAVED
    # sleep(3)
