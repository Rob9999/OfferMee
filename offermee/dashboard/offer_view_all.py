import streamlit as st
from offermee.dashboard.helpers.web_dashboard import stop_if_not_logged_in

from offermee.database.facades.main_facades import OfferFacade

# from offermee.database.models.main_models import OfferStatus


def offer_view_all_render():
    st.header("Offer History")
    stop_if_not_logged_in()

    try:
        offers = OfferFacade.get_all()

        if offers:
            for offer in offers:
                st.subheader(offer.get("offer_number"))
                st.write(f"**Status:** {offer.get('status')}")
                st.write(f"**Offer Content:** {offer.get('offer_text')}")
                st.write(f"**Comment:** {offer.get('comment', '-')}")

                # Display new fields
                st.write(f"**First Sent:** {offer.get('sent_date', '-')}")
                st.write(f"**Follow-Ups Sent:** {offer.get('follow_up_count')}")
                st.write(f"**Last Follow-Up:** {offer.get('last_follow_up_date', '-')}")
                st.write(f"**Offer Opened:** {'Yes' if offer.get('opened') else 'No'}")
                if offer.get("opened_date"):
                    st.write(f"**Opened On:** {offer.get('opened_date')}")

                st.markdown("---")
        else:
            st.info("No offers found.")
    except Exception as e:
        st.error(f"Error retrieving offers: {e}")
