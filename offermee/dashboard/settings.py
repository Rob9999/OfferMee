import streamlit as st
from offermee.config import Config
from offermee.dashboard.helpers.international import _T
from offermee.dashboard.helpers.web_dashboard import (
    log_debug,
    log_info,
    stop_if_not_logged_in,
)


def settings_render():
    st.title(_T("Settings"))
    stop_if_not_logged_in()

    config = Config.get_instance()

    # 1) Keep settings up to date
    config.reload_settings()

    # 2) Read current values (entire dictionary from the encrypted .settings)
    current_data = config.get_local_settings_to_dict()

    # --- AI PROVIDERS ---

    # Load the dictionary with all AI providers (set defaults if not available)
    ai_families = current_data.get(
        "ai_families",
        {
            "OpenAI": {"api_key": "", "model": "gpt-4"},
            "GenAI": {"api_key": "", "model": "gemini-1.5-flash"},
        },
    )

    # Currently active provider
    ai_selected_family = current_data.get("ai_selected_family", "OpenAI")

    st.subheader(_T("AI Settings"))

    # User selects the active provider here
    ai_selected_family = st.selectbox(
        _T("Which AI provider is currently active?"),
        ["OpenAI", "GenAI"],
        index=["OpenAI", "GenAI"].index(ai_selected_family),
        # Be careful to avoid IndexError:
        # possibly try/except or a proper fallback logic
    )

    # --- Settings for OpenAI ---
    st.markdown(f"### {_T('OpenAI Settings')}")
    openai_api_key = st.text_input(
        _T("OpenAI API Key"),
        value=ai_families["OpenAI"].get("api_key", ""),
        type="password",
    )
    openai_model = st.text_input(
        _T("OpenAI Model"), value=ai_families["OpenAI"].get("model", "gpt-4")
    )

    # --- Settings for GenAI ---
    st.markdown(f"### {_T('GenAI Settings')}")
    genai_api_key = st.text_input(
        _T("GenAI API Key"),
        value=ai_families["GenAI"].get("api_key", ""),
        type="password",
    )
    genai_model = st.text_input(
        _T("GenAI Model"), value=ai_families["GenAI"].get("model", "gemini-1.5-flash")
    )

    # Apply changes directly to the dictionary:
    ai_families["OpenAI"]["api_key"] = openai_api_key
    ai_families["OpenAI"]["model"] = openai_model
    ai_families["GenAI"]["api_key"] = genai_api_key
    ai_families["GenAI"]["model"] = genai_model

    # --- Email Settings ---
    st.subheader(_T("Email Settings"))
    email_address = st.text_input(
        _T("Email Address"),
        value=current_data.get("email_address", ""),
        placeholder="",
    )
    email_password = st.text_input(
        _T("Email Password"),
        value=current_data.get("email_password", ""),
        placeholder="",
        type="password",
    )
    smtp_server = st.text_input(
        _T("SMTP Server"),
        value=current_data.get("smtp_server", ""),
        placeholder="smtp.gmail.com",
    )
    smtp_port = st.number_input(
        _T("SMTP Port"), value=int(current_data.get("smtp_port", 465))
    )
    receiver_email = st.text_input(
        _T("Receiver Email Address"),
        value=current_data.get("receiver_email", ""),
        placeholder="",
    )
    receiver_password = st.text_input(
        _T("Receiver Email Password"),
        value=current_data.get("receiver_password", ""),
        placeholder="",
        type="password",
    )
    receiver_server = st.text_input(
        _T("Receiver Email Server"),
        value=current_data.get("receiver_server", ""),
        placeholder="smtp.gmail.com",
    )
    receiver_port = st.number_input(
        _T("Receiver Email Port"), value=int(current_data.get("receiver_port", 993))
    )

    # --- RFP Settings ---
    rfp_mailbox = st.text_input(
        _T("RFP Mailbox"),
        value=current_data.get("rfp_mailbox", ""),
        placeholder="RFPs",
    )
    rfp_email_subject_filter = st.text_input(
        _T("RFP Email Subject Filter"),
        value=current_data.get("rfp_email_subject_filter", ""),
        placeholder="RFP",
    )
    rfp_email_sender_filter = st.text_input(
        _T("RFP Email Sender Filter"),
        value=current_data.get("rfp_email_sender_filter", ""),
        placeholder="partner@example.com",
    )

    # --- Personal Data (Who?) ---
    st.subheader(_T("Personal Data (Who?)"))
    first_name = st.text_input(
        _T("First Name(s)"), value=current_data.get("first_name", "")
    )
    last_name = st.text_input(_T("Last Name"), value=current_data.get("last_name", ""))
    birth_date = st.text_input(
        _T("Birth Date"), value=current_data.get("birth_date", "")
    )
    birth_place = st.text_input(
        _T("Birth Place"), value=current_data.get("birth_place", "")
    )

    # --- Address (Where?) ---
    st.subheader(_T("Address (Where?)"))
    street = st.text_input(_T("Street"), value=current_data.get("street", ""))
    zip_code = st.text_input(_T("ZIP Code"), value=current_data.get("zip_code", ""))
    city = st.text_input(_T("City"), value=current_data.get("city", ""))
    country = st.text_input(_T("Country"), value=current_data.get("country", ""))

    # --- Account ---
    st.subheader(_T("Account"))
    account_name = st.text_input(
        _T("Account Name"), value=current_data.get("account_name", "")
    )
    account_password = st.text_input(
        _T("Account Password"),
        value=current_data.get("account_password", ""),
        type="password",
    )

    # --- Language / Currency ---
    st.subheader(_T("Language / Currency"))
    language = st.selectbox(
        _T("Language"),
        ["de", "en", "fr", "es"],
        index=0 if current_data.get("language", "de") == "de" else 1,
    )
    currency = st.text_input(_T("Currency"), value=current_data.get("currency", "EUR"))

    # --- Save ---
    if st.button(_T("Save")):
        # Collect all fields in new_settings
        new_settings = {
            "ai_selected_family": ai_selected_family,  # active provider
            "ai_families": ai_families,  # all provider data
            "email_address": email_address,
            "email_password": email_password,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "receiver_email": receiver_email,
            "receiver_password": receiver_password,
            "receiver_server": receiver_server,
            "receiver_port": receiver_port,
            "rfp_mailbox": rfp_mailbox,
            "rfp_email_subject_filter": rfp_email_subject_filter,
            "rfp_email_sender_filter": rfp_email_sender_filter,
            "first_name": first_name,
            "last_name": last_name,
            "birth_date": birth_date,
            "birth_place": birth_place,
            "street": street,
            "zip_code": zip_code,
            "city": city,
            "country": country,
            "account_name": account_name,
            "account_password": account_password,
            "language": language,
            "currency": currency,
        }

        # Save to local_settings (will be encrypted)
        config.save_local_settings(new_settings)
        log_debug(
            __name__, f"Settings successfully saved and encrypted:\n {new_settings}"
        )

        st.success(_T("Settings successfully saved and encrypted."))
