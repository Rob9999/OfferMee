import datetime
import streamlit as st
from offermee.database.db_connection import connect_to_db
from offermee.database.models.base_project_model import BaseProjectModel
from offermee.database.models.edited_project_model import EditedProjectModel
from offermee.database.models.enums.offer_status import OfferStatus
from offermee.database.models.freelancer_model import FreelancerModel
from offermee.database.models.enums.project_status import ProjectStatus
from offermee.matcher.skill_matcher import SkillMatcher
from offermee.matcher.price_matcher import PriceMatcher
from offermee.offers.generator import OfferGenerator
from offermee.offers.email_utils import EmailUtils


def get_freelancer_skills():
    """
    Holt die Fähigkeiten des Freelancers aus der Datenbank.
    """
    session = connect_to_db()
    freelancer = session.query(FreelancerModel).first()
    session.close()
    return (
        freelancer.skills.lower().split(", ")
        if freelancer and freelancer.skills
        else []
    )


def get_freelancer_desired_rate():
    """
    Holt den gewünschten Stundensatz des Freelancers aus der Datenbank.
    """
    session = connect_to_db()
    freelancer = session.query(FreelancerModel).first()
    session.close()
    return freelancer.desired_rate if freelancer else 0.0


def render():
    st.header("Projektübersicht")

    session = connect_to_db()
    projects = (
        session.query(BaseProjectModel)
        .filter(BaseProjectModel.status == ProjectStatus.NEW.value)
        .all()
    )

    freelancer_skills = get_freelancer_skills()
    freelancer_desired_rate = get_freelancer_desired_rate()

    for project in projects:
        match_score, skill_details = SkillMatcher.match_skills(
            project, freelancer_skills
        )
        price_score = PriceMatcher.match_price(project, freelancer_desired_rate)
        total_score = (match_score * 0.7) + (price_score * 0.3)  # Gewichtung anpassen

        st.subheader(project.title)
        st.write(f"**Beschreibung:** {project.description}")
        st.write(f"**Match Score:** {total_score:.2f}%")
        st.write(f"[Link zum Projekt]({project.original_link})")

        with st.expander("Details"):
            st.write("**Must-Have Skills:**")
            for skill, details in skill_details.items():
                if details["matched"] and skill in project.must_haves.lower():
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write("**Nice-To-Have Skills:**")
            for skill, details in skill_details.items():
                if details["matched"] and skill in project.nice_to_haves.lower():
                    st.write(f"- {skill} (Score: {details['score']})")
            st.write(f"**Preis-Matching-Score:** {price_score:.2f}%")

        if st.button(f"Angebot für {project.title} erstellen"):
            freelancer = session.query(FreelancerModel).first()
            if not freelancer:
                st.error(
                    "Freelancer-Profil nicht gefunden. Bitte hinterlegen Sie Ihren CV."
                )
                continue

            offer_content = OfferGenerator.generate_offer(project, freelancer)
            EmailUtils().send_email(
                project.contact_person, f"Angebot für {project.title}", offer_content
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
