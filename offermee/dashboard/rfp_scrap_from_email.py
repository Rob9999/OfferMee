# offermee/dashboard/pages/manual_input.py

import datetime
import json
import traceback
from typing import Any, Dict, List
import streamlit as st
from jsonschema import ValidationError

# Deine Projektspezifischen Importe
from offermee.config import Config
from offermee.dashboard.helpers.web_dashboard import (
    get_app_container,
    join_container_path,
    log_debug,
    stop_if_not_logged_in,
    log_info,
    log_error,
)
from offermee.AI.project_processor import ProjectProcessor
from offermee.database.facades.main_facades import ProjectFacade
from offermee.schemas.json.schema_loader import get_schema, validate_json
from offermee.schemas.json.schema_keys import SchemaKey
from offermee.database.transformers.project_model_transformer import json_to_db
from offermee.dashboard.widgets.to_sreamlit import (
    create_streamlit_edit_form_from_json_schema,
)
from offermee.dashboard.helpers.international import _T
from offermee.scraper.rfp_email_scraper import (
    connect_to_email,
    fetch_emails,
    parse_email,
)
from offermee.utils.container import Container
from offermee.enums.process_status import Status


def rfp_scrap_from_email_render():
    """
    # scrap email account for new RFPs (email of the last 48 hours)

    # Idee für die Implementierung:
    # 1. Verwende die Python-Bibliothek imaplib, um auf das E-Mail-Konto zuzugreifen.
    # 2. Verwende die Python-Bibliothek email, um die E-Mails zu parsen.
    # 3. Filtere die E-Mails nach dem Betreff oder dem Absender.
    # 3.1 Prüfe durch die ProjectFacade.get_first_by-Methode, ob das Projekt bereits in der Datenbank existiert. -->original_link, contact_person, contact_email
    # 3.2 Nehme nur die E-Mails, die noch nicht in der Datenbank existieren.
    # 4. Extrahiere den Text aus den E-Mails und gebe diese dem ProjektProcessor zu AI Analyse
    # 4.1 Speicher alle Daten zur verifizierenden Abarbeitung durch den Anwender in dem rfp-Dictionary
    # 4.2 View the extracted data of each rfp in the user interface to let the user verify + save to db or discard each rfp --> Raw Text, Analyze with AI, Validate Data, Save to DB


    Returns:
        _type_: _description_
    """

    st.header("Scrap Requests For Proposal (RFPs) from Email Account")
    stop_if_not_logged_in()

    page_root = __name__
    container: Container = get_app_container()
    config = Config.get_instance().get_config_data()
    email_user = config.receiver_email
    email_pass = config.receiver_password
    server = config.receiver_server
    port = config.receiver_port
    mailbox = config.rfp_mailbox
    subject_filter = config.rfp_email_subject_filter
    sender_filter = config.rfp_email_sender_filter
    operator = config.current_user

    # --- Initialize
    path_rfps_root = container.make_paths(
        join_container_path(page_root, "rfps"),
        typ=list,
        exists_ok=True,
        force_typ=True,
    )

    rfps: List[Dict[str, Any]] = container.get_value(path_rfps_root, [])
    print(any(rfp.get("status") in ["new", "analyzed", "validated"] for rfp in rfps))

    # Check if there is a need to scrap new RFPs from the email account
    if (
        any(
            rfp.get("status") in [Status.NEW, Status.ANALYZED, Status.VALIDATED]
            for rfp in rfps
        )
        == False
    ):
        log_info(__name__, "Offers to scrap rfps ...")
        st.markdown(
            f"### {_T('Scrap new RFPs from email account:')} {email_user}@{server}"
        )
        since_days = st.number_input(
            _T("Since when to check for new RFPs from email account?"),
            1,
            7,
            2,  # (seit den letzten 48 Stunden)
        )
        if st.button(_T("Scrap new RFPs from email account")):
            log_info(__name__, "Wants more rfp scraping ...")
            # Verbinde mit dem E-Mail-Server
            mail = connect_to_email(
                server,
                port,
                email_user,
                email_pass,
                mailbox if mailbox.strip() else "INBOX",
            )
            if not mail:
                st.error(
                    f"{_T('Could not connect to email server')} '{server}' {_T('with user')} '{email_user}'. {_T('Please check your credentials in Settings Page and try again.')}"
                )
                return

            # Definiere das Datum
            since_date = (
                datetime.datetime.now() - datetime.timedelta(days=since_days)
            ).strftime("%d-%b-%Y")

            # Hole relevante E-Mails
            emails = fetch_emails(mail, since_date, subject_filter, sender_filter)

            count = 0
            for email in emails:
                parsed_email = parse_email(email)
                raw_text = json.dumps(parsed_email)
                # rfp = { "raw_text": "...", "schema": { ... }, "data": { ... }, "control": { ... }, "status": Status.NEW }
                # check if email is already in the list
                if any(r.get("raw_text") == raw_text for r in rfps):
                    continue

                count += 1
                rfp_index = len(rfps)
                # add new rfp
                rfp_index = len(rfps)
                rfp = {
                    "raw_text": raw_text,
                    "schema": get_schema(SchemaKey.PROJECT),
                    "data": {},
                    "control": {"wantstore": False},
                    "status": Status.NEW,
                }
                rfps.append(rfp)
                log_info(__name__, f"Added new RFP to list.")
                # log_debug(__name__, f"Added new RFP to list:\n{rfp}")

            log_info(
                __name__,
                f"Scraped '{len(emails)}' emails from '{email_user}@{server}', '{count}' which are new ones.",
            )
            st.rerun()

    # Check if there are any RFPS to process that are not saved or discarded
    else:
        # get the first rfp that is not saved or discarded
        rfp_index = next(
            (
                i
                for i, r in enumerate(rfps)
                if r.get("status") in [Status.NEW, Status.ANALYZED, Status.VALIDATED]
            ),
            None,
        )
        rfp: Dict[str, Any] = rfps[rfp_index]

        path_rfp_data = path_rfps_root + f"[{rfp_index}].data"
        path_rfp_schema = path_rfps_root + f"[{rfp_index}].schema"
        path_rfp_control = path_rfps_root + f"[{rfp_index}].control"

        def invalidate_analysis(rfp: Dict[str, Any]):
            """When raw text changes, drop the old AI result + validation status."""
            rfp["status"] = Status.NEW
            rfp["data"] = {}
            rfp["control"]["wantstore"] = False

        def invalidate_validation(rfp: Dict[str, Any]):
            """When user modifies form fields, reset the validation flag."""
            rfp["status"] = Status.ANALYZED
            rfp["control"]["wantstore"] = False

        # log_info(
        #    __name__,
        #    f"Selected RFP#{rfp_index} to process:\n{rfp.get('raw_text') if rfp else {'Nix'}}",
        # )
        # --- Step 1: Big raw text input
        raw_text_dict = json.loads(rfp.get("raw_text", "{}"))
        with st.container(
            key=f"email_{raw_text_dict['subject']}_{raw_text_dict['date']}"
        ):
            st.write(f"### {_T('Email Subject')}: {raw_text_dict['subject']}")
            st.write(f"#### {_T('From')}: {raw_text_dict['from']}")
            st.html(raw_text_dict["body"])
            if st.checkbox(_T("Discard Email / RFP !")):
                st.warning(_T("RFP will be discarded."))
                if st.button(_T("Press again to confirm discarding.")):
                    rfp["status"] = Status.DISCARDED
                    st.rerun()
            st.write("---")

        # If user modifies raw text => AI analysis invalid
        # if new_raw_text != rfp["raw_text"]:
        #    rfp["raw_text"] = new_raw_text
        #    invalidate_analysis(rfp)

        # --- Step 2: "Analyze with AI" button
        if rfp["status"] == Status.NEW:
            if st.button(_T("Analyze Raw Input (AI)")):
                try:
                    log_info(__name__, f"Analyzing project with AI ...")
                    processor = ProjectProcessor()
                    result = processor.analyze_project(rfp["raw_text"])
                    if not result or "project" not in result:
                        st.error(
                            "AI analysis did not return a valid 'project' structure."
                        )
                    else:
                        rfp["data"] = {"project": result["project"]}
                        rfp["status"] = Status.ANALYZED
                except Exception as e:
                    log_error(__name__, f"Error during AI analysis: {e}")
                    st.error(f"Error during AI analysis: {e}")

        if rfp["status"] == Status.ANALYZED:
            st.success("AI analysis complete. Please review the fields below.")

        # --- Step 3: Validation form
        if rfp["status"] in [Status.ANALYZED, Status.VALIDATED]:

            create_streamlit_edit_form_from_json_schema(
                container=container,
                container_data_path=path_rfp_data,
                container_schema_path=path_rfp_schema,
                container_control_path=path_rfp_control,
                label=_T("Project Validate Extracted Data"),
            )
            wants_to_store = container.get_value(
                path_rfps_root + f"[{rfp_index}].control.wantstore", False
            )
            # If user wants to store (data accepted or modified) => we must (re-)validate
            if not wants_to_store:
                invalidate_validation(rfp)

            # --- Step 4: Validate Data
            if wants_to_store and rfp["status"] != Status.VALIDATED:
                if st.button("Validate Data"):
                    try:
                        validate_json(rfp["data"], rfp["schema"])
                        rfp["status"] = Status.VALIDATED
                        st.success(
                            "Data is valid according to the schema. You can now save."
                        )
                    except ValidationError as ve:
                        rfp["status"] = Status.ANALYZED
                        st.error(f"Validation Error: {ve.message}")
                    except Exception as e:
                        rfp["status"] = Status.ANALYZED
                        st.error(f"Unexpected error during validation: {e}")

            # --- Step 5: Save to DB (only if valid)
            if rfp["status"] == Status.VALIDATED:
                if st.button("Save to DB"):
                    try:
                        final_data = rfp["data"]
                        original_link = final_data["project"].get("original-link")
                        if original_link:
                            existing = ProjectFacade.get_first_by(
                                {"original_link": original_link}
                            )
                            if existing:
                                st.warning(
                                    "A project with that 'original-link' already exists."
                                )
                                return
                        # create and save
                        new_project = json_to_db(final_data).to_dict()
                        ProjectFacade.create(new_project, operator)
                        rfps[rfp_index]["status"] = Status.SAVED
                        st.success(f"Project '{new_project.get('title')}' saved to DB.")
                    except Exception as e:
                        log_error(__name__, f"Error saving to DB: {e}")
                        st.error(f"Error while saving: {e}")
                        traceback.print_exception(type(e), e, e.__traceback__)
