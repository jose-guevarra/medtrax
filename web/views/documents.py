import streamlit as st
from botocore.exceptions import ClientError

from core.auth import get_user_id
from core.config import load_config
from core.s3_upload import delete_document, list_user_documents, start_ingestion_job

config = load_config()
st.title("My Documents")

user_id = get_user_id(config)
documents = list_user_documents(config, user_id)

if not documents:
    st.info("You haven't uploaded any documents yet.")
else:
    sort_option = st.selectbox(
        "Sort by",
        ["Newest first", "Oldest first", "Name (A-Z)", "Name (Z-A)"],
    )
    sort_key, reverse = {
        "Newest first": (lambda d: d["uploaded_at"], True),
        "Oldest first": (lambda d: d["uploaded_at"], False),
        "Name (A-Z)": (lambda d: d["name"].lower(), False),
        "Name (Z-A)": (lambda d: d["name"].lower(), True),
    }[sort_option]
    documents.sort(key=sort_key, reverse=reverse)

    COL_WIDTHS = [3, 2, 3, 2, 3, 2, 1, 1]

    def _text(value: str) -> str:
        return value if value else "—"

    def _provider(doc: dict) -> str:
        name, kind = doc["provider_name"], doc["provider_type"]
        if name and kind:
            return f"{name} ({kind})"
        return _text(name or kind)

    header = st.columns(COL_WIDTHS)
    header[0].markdown("**Name**")
    header[1].markdown("**Type**")
    header[2].markdown("**Provider**")
    header[3].markdown("**Visit Date**")
    header[4].markdown("**Amount Paid**")
    header[5].markdown("**Uploaded**")

    for doc in documents:
        row = st.columns(COL_WIDTHS)
        row[0].write(doc["name"])
        row[1].write(_text(doc["document_type"]))
        row[2].write(_provider(doc))
        row[3].write(_text(doc["visit_date"]))
        row[4].write(_text(doc["amount_paid"]))
        row[5].write(doc["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S"))
        if row[6].button("", icon=":material/quiz:", key=f"eval-{doc['name']}", help="Ask about this document"):
            st.session_state.qa_selected_document = doc["name"]
            st.switch_page("views/document_qa.py")
        if row[7].button("", icon=":material/delete:", key=f"delete-{doc['name']}", help="Delete"):
            st.session_state.pending_delete = doc["name"]

    pending = st.session_state.get("pending_delete")
    if pending:
        st.warning(f"Delete **{pending}**? This also removes it from search results.")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Confirm delete", type="primary"):
            with st.spinner("Deleting…"):
                try:
                    delete_document(config, user_id, pending)
                except Exception as exc:
                    st.error(f"Delete failed: {exc}")
                    st.stop()
                try:
                    start_ingestion_job(config)
                except ClientError as exc:
                    if exc.response.get("Error", {}).get("Code") != "ConflictException":
                        st.error(f"Deleted, but failed to start ingestion sync: {exc}")
            st.session_state.pending_delete = None
            st.success(f"Deleted {pending}.")
            st.rerun()
        if cancel_col.button("Cancel"):
            st.session_state.pending_delete = None
            st.rerun()
