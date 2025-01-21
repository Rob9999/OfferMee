import datetime
from typing import Any, Dict, List
import streamlit as st
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import (
    log_error,
    log_info,
    stop_if_not_logged_in,
)
from offermee.database.facades.main_facades import FreelancerFacade, ProjectFacade
from offermee.database.models.main_models import ProjectStatus
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.matcher.price_matcher import PriceMatcher
from offermee.offers.generator import OfferGenerator
from offermee.offers.email_utils import EmailUtils


def matches_render():
    page_title = "Projektmatcher & Angebotserstellung"
    st.header(page_title)
    stop_if_not_logged_in()
    log_info(__name__, "Visiting the side.")

    # evaluate candidate
    config = Config.get_instance()
    cv_candidate = st.text_input(
        label="Candidate", value=config.get_name_from_local_settings()
    )

    freelancer: Dict[str, Any] = FreelancerFacade.get_first_by({"name": cv_candidate})
    if freelancer is None:
        log_error(
            __name__, f"Unknwon freelancer {cv_candidate}. Cv must be loaded first!"
        )
        st.error(f"Unbekannter Freelancer {cv_candidate}, bitte zuerst CV hochladen!")
        st.stop()

    freelancer_tech_skills = freelancer.get(
        "capabilities", {}
    )  # .get("tech_skills", [])
    st.write(f"freelancer_tech_skills:\n{freelancer_tech_skills}")
    freelancer_desired_rate = freelancer.get("desired_rate_min")
    st.session_state["freelancer"] = freelancer
    log_info(__name__, f"Freelancer {cv_candidate} is found")
    st.success(f"Freelancer {cv_candidate} ist gefunden")

    # evaluate projects
    projects: List[Dict[str, Any]] = ProjectFacade.get_all_by(
        {"status": ProjectStatus.NEW}
    )
    projects_count = len(projects)
    st.success(f"Aktuell {projects_count} neue Projekte gespeichert")
    if projects_count <= 0:
        log_info(__name__, "No new projects in db. User must go to scrap some first.")
        st.warning(
            f"Keine neuen Projekte gespeichert, auf geht´s zum Projekte Scrapen!"
        )

    for project in projects:
        log_info(__name__, f"Matching project {project.get('title')}")
        match_score, skill_details = SkillMatcher.match_skills(
            project, freelancer_tech_skills
        )
        if project.get("hourly_rate"):
            if freelancer_desired_rate:
                price_score = PriceMatcher.match_price(project, freelancer_desired_rate)
            else:
                # freelancer would accept any rate
                price_score = 1
        else:
            price_score = 0
        total_score = (match_score * 0.7) + (price_score * 0.3)  # Gewichtung anpassen

        st.subheader(project.get("title"))
        st.write(f"**Beschreibung:** {project.get('description')}")
        st.write(f"**Match Score:** {total_score:.2f}%")
        st.write(f"[Link zum Projekt]({project.get('original_link')})")

        with st.expander("Details"):
            st.write("**Must-Have Skills:**")
            for skill, details in skill_details.items():
                if (
                    details["matched"]
                    and project.get("must_haves")
                    and skill in project.get("must_haves").lower()
                ):
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write("**Nice-To-Have Skills:**")
            for skill, details in skill_details.items():
                if (
                    details["matched"]
                    and project.get("nice_to_haves")
                    and skill in project.get("nice_to_haves").lower()
                ):
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write(f"**Preis-Matching-Score:** {price_score:.2f}%")

        if st.button(f"Angebot für {project.get('title')} erstellen"):
            if st.session_state and st.session_state.get("freelancer"):
                freelancer = st.session_state["freelancer"]
            else:
                log_error(__name__, "No freelancer loaded.")
                st.error("Kein Freelancer geladen. Zuerst den CV hochladen!")
                st.stop()

            freelancer_desired_rate_min = freelancer.get("desired_rate_min")
            hourly_rate_remote = st.number_input(
                f"Stundensatz remote in € zzgl. MwSt. (min: {freelancer_desired_rate_min})",
                min_value=freelancer_desired_rate_min,
                format="%.2f",
            )
            hourly_rate_onsite = st.number_input(
                f"Stundensatz onsite in € zzgl. MwSt. (min: {freelancer_desired_rate_min})",
                min_value=freelancer_desired_rate_min,
                format="%.2f",
            )
            daily_rate_onsite_pauschal = st.number_input(
                f"Tagespauschale onsite deutschlandweit (all-in) in € zzgl. MwSt. (min: {freelancer_desired_rate_min*8+500.00})",
                value=freelancer_desired_rate_min * 8 + 500.00,
                min_value=freelancer_desired_rate_min * 8 + 500,
                format="%.2f",
            )
            offer_content = OfferGenerator().generate_offer(
                project,
                freelancer,
                {
                    "hourly_rate_remote": hourly_rate_remote,
                    "hourly_rate_onsite": hourly_rate_onsite,
                    "daily_rate_onsite_pauschal": daily_rate_onsite_pauschal,
                },
            )
            # log_info(__name__, f"Generated offer: \n{offer_content}")
            EmailUtils().send_email(
                project.get("contact_person"),
                f"Angebot für {project.get('title')}",
                offer_content,
                True,
            )
            st.success("Angebot erfolgreich gesendet!")

            # updaten data set:
            project["status"] = ProjectStatus.IN_PROGRESS
            project["offer_written"] = True
            project["offer"] = offer_content
            project["sent"] = datetime.datetime.now()
            ProjectFacade.update(project.get("id"), project)
            st.rerun(page_title)
