import streamlit as st
from botocore.exceptions import ClientError

from core.auth import get_user_id
from core.config import load_config
from core.extraction import extract_document_fields
from core.s3_upload import start_ingestion_job, upload_document, upload_embedding_markdown

config = load_config()
st.title("Upload a document")

file = st.file_uploader("Choose a PDF", type=["pdf"])
if file and st.button("Upload and sync"):
    user_id = get_user_id(config)

    with st.spinner("Uploading original to S3…"):
        try:
            key = upload_document(config, user_id, file.getvalue(), file.name, file.type)
            st.success(f"Uploaded original: s3://{config.s3_data_source_bucket}/{key}")
        except Exception as exc:
            st.error(f"Upload failed: {exc}")
            st.stop()

    with st.spinner("Extracting document information…"):
        try:
            extracted = extract_document_fields(config, file.getvalue(), file.name)
            embedding_key = upload_embedding_markdown(config, user_id, file.name, extracted)
            st.success(f"Prepared for search: s3://{config.s3_data_source_bucket}/{embedding_key}")
        except Exception as exc:
            st.error(f"Document processing failed: {exc}")
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
