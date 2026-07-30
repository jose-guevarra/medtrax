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

    header = st.columns([4, 2, 3, 2])
    header[0].markdown("**Name**")
    header[1].markdown("**Size**")
    header[2].markdown("**Uploaded**")

    for doc in documents:
        row = st.columns([4, 2, 3, 2])
        row[0].write(doc["name"])
        row[1].write(f"{doc['size_bytes'] / 1024:.1f} KB")
        row[2].write(doc["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S"))
        if row[3].button("Delete", key=f"delete-{doc['name']}"):
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
