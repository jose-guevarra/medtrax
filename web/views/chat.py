import streamlit as st

from core.agent_client import invoke_agent_stream, new_session_id
from core.auth import get_access_token
from core.config import load_config

config = load_config()
st.title("Ask about your health records")

st.session_state.setdefault("runtime_session_id", new_session_id())
st.session_state.setdefault("chat_history", [])

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask a question…")
if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    token = get_access_token(config)
    if not token:
        st.error("Session expired — please log in again.")
        st.stop()

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        try:
            history = st.session_state.chat_history[:-1]
            for event in invoke_agent_stream(
                config, token, prompt, history, st.session_state.runtime_session_id
            ):
                if event.get("type") == "text":
                    full_text += event["text"]
                    placeholder.markdown(full_text + "▌")
                elif event.get("type") == "error":
                    full_text += f"\n\n_Error: {event.get('text')}_"
                    break
            placeholder.markdown(full_text)
        except Exception as exc:
            full_text = f"Request failed: {exc}"
            placeholder.markdown(full_text)

    st.session_state.chat_history.append({"role": "assistant", "content": full_text})
