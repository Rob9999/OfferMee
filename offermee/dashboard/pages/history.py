import streamlit as st
from offermee.database.db_connection import connect_to_db
from offermee.database.models.edited_project_model import EditedProjectModel
from offermee.database.models.enums.offer_status import OfferStatus
from datetime import datetime


def render():
    st.header("Offer History")

    session = connect_to_db()

    try:
        offers = (
            session.query(EditedProjectModel)
            .filter(EditedProjectModel.offer_status != OfferStatus.DRAFT)
            .all()
        )

        if offers:
            for offer in offers:
                st.subheader(offer.title)
                st.write(f"**Status:** {offer.offer_status.value}")
                st.write(f"**Offer Content:** {offer.offer}")
                st.write(f"**Comment:** {offer.comment or '-'}")

                # Display new fields
                st.write(f"**First Sent:** {offer.sent_date or '-'}")
                st.write(f"**Follow-Ups Sent:** {offer.followup_count}")
                st.write(f"**Last Follow-Up:** {offer.last_followup_date or '-'}")
                st.write(f"**Offer Opened:** {'Yes' if offer.opened else 'No'}")
                if offer.opened_date:
                    st.write(f"**Opened On:** {offer.opened_date}")

                st.markdown("---")
        else:
            st.info("No offers found.")
    except Exception as e:
        st.error(f"Error retrieving offers: {e}")
    finally:
        session.close()
