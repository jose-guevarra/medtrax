import uuid

import streamlit as st

from core.agent_client import invoke_agent_stream
from core.auth import get_access_token, get_user_id
from core.config import load_config
from core.feedback import RATING_LABELS, record_feedback

config = load_config()
st.title("Ask about your health records")

user_id = get_user_id(config)
st.session_state.setdefault("runtime_session_id", user_id)
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("feedback_error", None)
st.session_state.setdefault("feedback_toast", None)

if st.session_state.feedback_error:
    st.error(st.session_state.feedback_error)
    st.session_state.feedback_error = None

if st.session_state.feedback_toast:
    st.toast(st.session_state.feedback_toast, icon="✅")
    st.session_state.feedback_toast = None


def _on_feedback_change(message: dict, prompt_text: str | None, key: str) -> None:
    value = st.session_state[key]
    message["feedback"] = value
    if value is None:  # user cleared their rating; nothing to log
        return
    try:
        record_feedback(
            config,
            user_id=user_id,
            session_id=st.session_state.runtime_session_id,
            message_id=message["id"],
            rating=RATING_LABELS[value],
            response_text=message["content"],
            prompt_text=prompt_text,
        )
        st.session_state.feedback_toast = "Thanks for your feedback!"
    except Exception as exc:
        st.session_state.feedback_error = f"Couldn't save feedback: {exc}"


def _render_assistant_feedback(message: dict, prompt_text: str | None) -> None:
    key = f"feedback_{message['id']}"
    st.feedback(
        "thumbs",
        key=key,
        default=message.get("feedback"),
        on_change=_on_feedback_change,
        args=(message, prompt_text, key),
    )


for i, msg in enumerate(st.session_state.chat_history):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            prior = st.session_state.chat_history[i - 1] if i > 0 else None
            prompt_text = prior["content"] if prior and prior["role"] == "user" else None
            _render_assistant_feedback(msg, prompt_text)

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
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.chat_history[:-1]
            ]
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

        new_message = {
            "id": uuid.uuid4().hex,
            "role": "assistant",
            "content": full_text,
            "feedback": None,
        }
        st.session_state.chat_history.append(new_message)
        _render_assistant_feedback(new_message, prompt)
