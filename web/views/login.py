import streamlit as st

from core.auth import initiate_auth, respond_new_password
from core.config import load_config

config = load_config()
st.title("Medtrax Login")

challenge = st.session_state.get("challenge")

if challenge:
    st.info("First login: please set a new password.")
    with st.form("new_password_form"):
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Set password")
    if submitted:
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            try:
                tokens = respond_new_password(
                    config, challenge["username"], new_password, challenge["session"]
                )
                st.session_state.auth = {**tokens, "username": challenge["username"]}
                st.session_state.challenge = None
                st.rerun()
            except Exception as exc:
                st.error(f"Could not set new password: {exc}")
else:
    with st.form("login_form"):
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        try:
            result = initiate_auth(config, username, password)
            if result.get("challenge"):
                st.session_state.challenge = result
            else:
                st.session_state.auth = {**result["tokens"], "username": result["username"]}
            st.rerun()
        except Exception as exc:
            st.error(f"Login failed: {exc}")
