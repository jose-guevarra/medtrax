import streamlit as st

from core.auth import is_authenticated, logout
from core.config import load_config

st.set_page_config(page_title="Medtrax", page_icon="🩺", layout="wide")

config = load_config()

if not is_authenticated(config):
    pg = st.navigation([st.Page("views/login.py", title="Login", icon="🔑")])
else:
    pages = [
        st.Page("views/chat.py", title="Home", icon="💬", default=True),
        st.Page("views/upload.py", title="Upload Document", icon="📤"),
        st.Page("views/documents.py", title="My Documents", icon="🗂️"),
        st.Page("views/health_graph.py", title="Health Graph", icon="📈"),
        st.Page("views/document_qa.py", title="Eval Builder", icon="🧪"),
    ]
    pg = st.navigation(pages)
    with st.sidebar:
        st.caption(f"Logged in as **{st.session_state.auth['username']}**")
        if st.button("Log out"):
            logout()
            st.rerun()

        if config.debug:
            st.divider()
            st.caption("Debug")
            st.code(st.session_state.auth["user_id"])

pg.run()
