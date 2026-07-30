import streamlit as st
from botocore.exceptions import ClientError

from core.auth import get_user_id
from core.config import load_config
from core.s3_upload import start_ingestion_job, upload_document

config = load_config()
st.title("Upload a document")

file = st.file_uploader("Choose a PDF", type=["pdf"])
if file and st.button("Upload and sync"):
    with st.spinner("Uploading to S3…"):
        try:
            user_id = get_user_id(config)
            key = upload_document(config, user_id, file.getvalue(), file.name, file.type)
            st.success(f"Uploaded: s3://{config.s3_data_source_bucket}/{key}")
        except Exception as exc:
            st.error(f"Upload failed: {exc}")
            st.stop()
    with st.spinner("Starting knowledge base ingestion sync…"):
        try:
            job_id = start_ingestion_job(config)
            st.success(f"Ingestion job started: {job_id}")
            st.info(
                "Ingestion runs in the background; ask about the document in Home "
                "once it finishes (usually a few minutes)."
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConflictException":
                st.warning(
                    "An ingestion job is already in progress. Your file was uploaded "
                    "and will be picked up by that run or the next sync."
                )
            else:
                st.error(f"Failed to start ingestion job: {exc}")
