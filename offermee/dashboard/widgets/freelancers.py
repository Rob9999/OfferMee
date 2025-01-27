from typing import Any, Dict
import streamlit as st

from offermee.utils.international import _T


def edit_freelancers_hourly_rate(
    container_label: str, hourly_rate_data: Dict[str, Any] = None
):
    st.markdown(f"**{_T('Freelancers Hourly Rate')}**")
    desired_min_rate: float = 50.0
    desired_max_rate: float = 150.0
    with st.form("freelancers_hourly_rate"):

        if hourly_rate_data:
            desired_min_rate: float = hourly_rate_data.get(
                "desired_min_rate", desired_min_rate
            )
            desired_max_rate: float = hourly_rate_data.get(
                "desired_max_rate", desired_max_rate
            )
        # Gewünschter Stundensatz
        desired_rate = st.slider(
            f"{_T('Desired hourly rate')} ({_T('€')})",
            min_value=0.0,
            max_value=500.0,
            value=(desired_rate_min, desired_max_rate),
            step=10.0,
        )
        desired_rate_min, desired_rate_max = desired_rate
        st.write(
            f"{_T('Minimum hourly rate')}: {desired_rate_min} {_T('€')}, "
            f"{_T('Maximum hourly rate')}: {desired_rate_max} {_T('€')}"
        )
        if st.form_submit_button(_T("OK")):
            st.session_state[container_label] = {
                "desired_min_rate": desired_min_rate,
                "desired_max_rate": desired_max_rate,
            }
