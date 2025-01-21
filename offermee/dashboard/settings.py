import streamlit as st
import os
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import stop_if_not_logged_in


def settings_render():
    st.title("Einstellungen")
    stop_if_not_logged_in()

    config = Config.get_instance()

    # 1) Settings aktuell halten
    config.reload_settings()

    # 2) Aktuelle Werte lesen (gesamtes Dictionary aus der verschlüsselten .settings)
    current_data = config.get_local_settings_to_dict()

    # --- AI PROVIDERS ---

    # Lade das Dictionary mit allen AI-Providern (falls nicht vorhanden, Defaults setzen)
    ai_families = current_data.get(
        "ai_families",
        {
            "OpenAI": {"api_key": "", "model": "gpt-4"},
            "GenAI": {"api_key": "", "model": "gemini-1.5-flash"},
        },
    )

    # Aktueller aktiver Provider
    ai_selected_family = current_data.get("ai_selected_family", "OpenAI")

    st.subheader("KI-Einstellungen")

    # Nutzer wählt hier den aktiven Provider
    ai_selected_family = st.selectbox(
        "Welcher AI Provider ist aktuell aktiv?",
        ["OpenAI", "GenAI"],
        index=["OpenAI", "GenAI"].index(ai_selected_family),
        # Vorsicht, IndexError vermeiden:
        # ggf. try/except oder eine ordentliche fallback-Logik
    )

    # --- Einstellungen für OpenAI ---
    st.markdown("### OpenAI Settings")
    openai_api_key = st.text_input(
        "OpenAI API-Key",
        value=ai_families["OpenAI"].get("api_key", ""),
        type="password",
    )
    openai_model = st.text_input(
        "OpenAI Modell", value=ai_families["OpenAI"].get("model", "gpt-4")
    )

    # --- Einstellungen für GenAI ---
    st.markdown("### GenAI Settings")
    genai_api_key = st.text_input(
        "GenAI API-Key", value=ai_families["GenAI"].get("api_key", ""), type="password"
    )
    genai_model = st.text_input(
        "GenAI Modell", value=ai_families["GenAI"].get("model", "gemini-1.5-flash")
    )

    # Änderungen direkt ins Dictionary übernehmen:
    ai_families["OpenAI"]["api_key"] = openai_api_key
    ai_families["OpenAI"]["model"] = openai_model
    ai_families["GenAI"]["api_key"] = genai_api_key
    ai_families["GenAI"]["model"] = genai_model

    # --- E-Mail-Einstellungen ---
    st.subheader("E-Mail-Einstellungen")
    email_address = st.text_input(
        "E-Mail-Adresse", value=current_data.get("email_address", "")
    )
    email_password = st.text_input(
        "E-Mail-Passwort", value=current_data.get("email_password", ""), type="password"
    )
    smtp_server = st.text_input(
        "SMTP-Server", value=current_data.get("smtp_server", "smtp.gmail.com")
    )
    smtp_port = st.number_input(
        "SMTP-Port", value=int(current_data.get("smtp_port", 465))
    )

    # --- Personendaten (Wer?) ---
    st.subheader("Personendaten (Wer?)")
    first_name = st.text_input("Vorname(n)", value=current_data.get("first_name", ""))
    last_name = st.text_input("Nachname", value=current_data.get("last_name", ""))
    birth_date = st.text_input("Geburtsdatum", value=current_data.get("birth_date", ""))
    birth_place = st.text_input("Geburtsort", value=current_data.get("birth_place", ""))

    # --- Adresse (Wo?) ---
    st.subheader("Adresse (Wo?)")
    street = st.text_input("Straße", value=current_data.get("street", ""))
    zip_code = st.text_input("PLZ", value=current_data.get("zip_code", ""))
    city = st.text_input("Stadt", value=current_data.get("city", ""))
    country = st.text_input("Land", value=current_data.get("country", ""))

    # --- Account ---
    st.subheader("Account")
    account_name = st.text_input(
        "Account-Name", value=current_data.get("account_name", "")
    )
    account_password = st.text_input(
        "Account-Passwort",
        value=current_data.get("account_password", ""),
        type="password",
    )

    # --- Sprache / Währung ---
    st.subheader("Sprache / Währung")
    language = st.selectbox(
        "Sprache",
        ["de", "en", "fr", "es"],
        index=0 if current_data.get("language", "de") == "de" else 1,
    )
    currency = st.text_input("Währung", value=current_data.get("currency", "EUR"))

    # --- Speichern ---
    if st.button("Speichern"):
        # Alle Felder in new_settings sammeln
        new_settings = {
            "ai_selected_family": ai_selected_family,  # aktiver Provider
            "ai_families": ai_families,  # alle Provider-Daten
            "email_address": email_address,
            "email_password": email_password,
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
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

        # In local_settings speichern (wird verschlüsselt)
        config.save_local_settings(new_settings)

        st.success("Einstellungen erfolgreich gespeichert und verschlüsselt.")
