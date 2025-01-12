import datetime
import streamlit as st
from offermee.config import Config
from offermee.dashboard.web_dashboard import log_error, log_info, stop_if_not_logged_in
from offermee.database.db_connection import connect_to_db, get_freelancer_by_name
from offermee.database.db_utils import load_projects_from_db
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.edited_project_model import EditedProjectModel
from offermee.database.models.enums.offer_status import OfferStatus
from offermee.database.models.freelancer_model import FreelancerModel
from offermee.database.models.enums.project_status import ProjectStatus
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.matcher.price_matcher import PriceMatcher
from offermee.offers.generator import OfferGenerator
from offermee.offers.email_utils import EmailUtils


def render():
    st.header("Projektmatcher & Angebotserstellung")
    stop_if_not_logged_in()
    log_info(__name__, "Visiting the side.")

    # evaluate candidate
    config = Config.get_instance()
    cv_candidate = st.text_input(
        label="Candidate", value=config.get_name_from_local_settings()
    )
    session = connect_to_db()
    freelancer: FreelancerModel = get_freelancer_by_name(cv_candidate, session=session)
    if freelancer is None:
        log_error(
            __name__, f"Unknwon freelancer {cv_candidate}. Cv must be loaded first!"
        )
        st.error(f"Unbekannter Freelancer {cv_candidate}, bitte zuerst CV hochladen!")
        session.close()
        st.stop()

    freelancer_tech_skills = freelancer.tech_skills.lower().split(",")
    freelancer_desired_rate = freelancer.desired_rate_min
    st.session_state["freelancer"] = freelancer
    session.close()
    log_info(__name__, f"Freelancer {cv_candidate} is found")
    st.success(f"Freelancer {cv_candidate} ist gefunden")

    # evaluate projects
    projects: list[BaseProjectModel] = load_projects_from_db(ProjectStatus.NEW)
    projects_count = len(projects)
    st.success(f"Aktuell {projects_count} neue Projekte gespeichert")
    if projects_count <= 0:
        log_info(__name__, "No new projects in db. User must go to scrap some first.")
        st.warning(
            f"Keine neuen Projekte gespeichert, auf geht´s zum Projekte Scrapen!"
        )

    for project in projects:
        log_info(__name__, f"Matching project {project.title}")
        match_score, skill_details = SkillMatcher.match_skills(
            project, freelancer_tech_skills
        )
        if project.hourly_rate:
            if freelancer_desired_rate:
                price_score = PriceMatcher.match_price(project, freelancer_desired_rate)
            else:
                # freelancer would accept any rate
                price_score = 1
        else:
            price_score = 0
        total_score = (match_score * 0.7) + (price_score * 0.3)  # Gewichtung anpassen

        st.subheader(project.title)
        st.write(f"**Beschreibung:** {project.description}")
        st.write(f"**Match Score:** {total_score:.2f}%")
        st.write(f"[Link zum Projekt]({project.original_link})")

        with st.expander("Details"):
            st.write("**Must-Have Skills:**")
            for skill, details in skill_details.items():
                if (
                    details["matched"]
                    and project.must_haves
                    and skill in project.must_haves.lower()
                ):
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write("**Nice-To-Have Skills:**")
            for skill, details in skill_details.items():
                if (
                    details["matched"]
                    and project.nice_to_haves
                    and skill in project.nice_to_haves.lower()
                ):
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write(f"**Preis-Matching-Score:** {price_score:.2f}%")

        if st.button(f"Angebot für {project.title} erstellen"):
            if st.session_state and st.session_state.get("freelancer"):
                freelancer = st.session_state["freelancer"]
            else:
                log_error(__name__, "No freelancer loaded.")
                st.error("Kein Freelancer geladen. Zuerst den CV hochladen!")
                session.close()
                st.stop()

            hourly_rate_remote = st.number_input(
                f"Stundensatz remote in € zzgl. MwSt. (min: {freelancer.desired_rate_min})",
                min_value=freelancer.desired_rate_min,
                format="%.2f",
            )
            hourly_rate_onsite = st.number_input(
                f"Stundensatz onsite in € zzgl. MwSt. (min: {freelancer.desired_rate_min})",
                min_value=freelancer.desired_rate_min,
                format="%.2f",
            )
            daily_rate_onsite_pauschal = st.number_input(
                f"Tagespauschale onsite deutschlandweit (all-in) in € zzgl. MwSt. (min: {freelancer.desired_rate_min*8+500.00})",
                value=freelancer.desired_rate_min * 8 + 500.00,
                min_value=freelancer.desired_rate_min * 8 + 500,
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
            log_info(__name__, f"Generated offer: \n{offer_content}")
            EmailUtils().send_email(
                project.contact_person,
                f"Angebot für {project.title}",
                offer_content,
                True,
            )

            st.success("Angebot erfolgreich gesendet!")

            # Aktualisieren des Projektstatus
            project.status = ProjectStatus.IN_PROGRESS.value

            # Neues EditedProjectModel anlegen oder vorhandenes updaten:
            edited_offer = EditedProjectModel(
                id=project.id,
                offer_written=True,
                offer=offer_content,
                offer_status=OfferStatus.SENT,
                sent_date=datetime.datetime.now(),  # <- hier setzen wir das Versanddatum
            )
            session.merge(edited_offer)
            session.commit()
            session.close()
