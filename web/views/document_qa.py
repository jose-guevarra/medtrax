import uuid

import streamlit as st

from core.auth import get_user_id
from core.config import load_config
from core.document_qa import answer_document_question_stream
from core.eval_gen import generate_question_variants
from core.eval_retrieval import run_hit_rate
from core.eval_store import append_ground_truth, ground_truth_for_document, load_ground_truth
from core.s3_upload import build_embedding_key, list_user_documents, read_document_text

config = load_config()
st.title("Eval Builder")

user_id = get_user_id(config)
documents = list_user_documents(config, user_id)

if not documents:
    st.info("You haven't uploaded any documents yet.")
    st.stop()

names = [d["name"] for d in documents]
default = st.session_state.get("qa_selected_document")
default_index = names.index(default) if default in names else 0
selected_name = st.selectbox("Document", names, index=default_index)

expected_document = build_embedding_key(user_id, selected_name).rsplit("/", 1)[-1]
existing_rows = ground_truth_for_document(expected_document)
st.caption(f"{len(existing_rows)} ground-truth Q&A pair(s) saved for this document.")

if selected_name != st.session_state.get("qa_active_document"):
    st.session_state.qa_active_document = selected_name
    st.session_state.qa_history = []
    st.session_state.qa_generated = []

st.divider()
st.subheader("Ask & save ground truth")


def _render_save_button(message: dict, prompt_text: str | None) -> None:
    if st.button("Save as ground truth", key=f"save-{message['id']}"):
        append_ground_truth(prompt_text, expected_document, answer=message["content"], source="manual")
        st.toast("Saved.", icon="✅")


for i, msg in enumerate(st.session_state.qa_history):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            prior = st.session_state.qa_history[i - 1] if i > 0 else None
            prompt_text = prior["content"] if prior and prior["role"] == "user" else None
            _render_save_button(msg, prompt_text)

prompt = st.chat_input("Ask a question about this document…")
if prompt:
    st.session_state.qa_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        try:
            document_text = read_document_text(config, user_id, selected_name)
            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.qa_history[:-1]]
            for chunk in answer_document_question_stream(config, document_text, prompt, history):
                full_text += chunk
                placeholder.markdown(full_text + "▌")
            placeholder.markdown(full_text)
        except Exception as exc:
            full_text = f"Request failed: {exc}"
            placeholder.markdown(full_text)

        new_message = {"id": uuid.uuid4().hex, "role": "assistant", "content": full_text}
        st.session_state.qa_history.append(new_message)
        _render_save_button(new_message, prompt)

st.divider()
st.subheader("Generate question variants")

existing_questions = [row["question"] for row in existing_rows]
count = st.number_input("How many variants to generate", min_value=1, max_value=20, value=5, step=1)
if st.button("Generate variants"):
    try:
        document_text = read_document_text(config, user_id, selected_name)
        st.session_state.qa_generated = generate_question_variants(
            config, document_text, existing_questions, int(count)
        )
    except Exception as exc:
        st.error(f"Generation failed: {exc}")

if st.session_state.get("qa_generated"):
    st.write("Select which generated questions to save as ground truth:")
    selected_flags = {
        q: st.checkbox(q, value=True, key=f"gen-{i}") for i, q in enumerate(st.session_state.qa_generated)
    }
    if st.button("Save selected"):
        to_save = [q for q, checked in selected_flags.items() if checked]
        for q in to_save:
            append_ground_truth(q, expected_document, answer="", source="llm-generated")
        st.session_state.qa_generated = []
        st.toast(f"Saved {len(to_save)} question(s).", icon="✅")
        st.rerun()

st.divider()
st.subheader("Run hit-rate eval")

k = st.slider("Top-k", min_value=1, max_value=20, value=5)
all_docs = st.checkbox("Include ground truth from all documents", value=False)
if st.button("Run eval"):
    rows = load_ground_truth() if all_docs else ground_truth_for_document(expected_document)
    if not rows:
        st.warning("No ground-truth rows to evaluate.")
    else:
        with st.spinner("Running retrieval for each question…"):
            results, hit_rate = run_hit_rate(config, user_id, rows, k)
        st.metric("Hit rate", f"{hit_rate:.1%}", f"{sum(r['hit'] for r in results)}/{len(results)}")
        st.dataframe(
            [
                {
                    "Question": r["question"],
                    "Source": r["source"],
                    "Hit": "✅" if r["hit"] else "❌",
                    "Expected": r["expected_document"],
                    "Retrieved": ", ".join(r["retrieved"]) or "(none)",
                }
                for r in results
            ],
            hide_index=True,
            use_container_width=True,
        )
