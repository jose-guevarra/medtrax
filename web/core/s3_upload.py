import json

import boto3
from botocore.exceptions import ClientError

from core.config import Config

_MAX_FILENAME_BYTES = 255


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def validate_filename(filename: str) -> None:
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty.")
    if "/" in filename or "\\" in filename:
        raise ValueError("Filename cannot contain '/' or '\\'.")
    if filename in (".", ".."):
        raise ValueError("Filename cannot be '.' or '..'.")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in filename):
        raise ValueError("Filename cannot contain control characters.")
    if len(filename.encode("utf-8")) > _MAX_FILENAME_BYTES:
        raise ValueError(f"Filename is too long (max {_MAX_FILENAME_BYTES} bytes).")


def build_object_key(user_id: str, filename: str) -> str:
    return f"uploads/{user_id}/{filename}"


def document_exists(config: Config, user_id: str, filename: str) -> bool:
    s3 = _session(config).client("s3", region_name=config.aws_region)
    try:
        s3.head_object(Bucket=config.s3_data_source_bucket, Key=build_object_key(user_id, filename))
        return True
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
            return False
        raise


def upload_document(config: Config, user_id: str, file_bytes: bytes, filename: str, content_type: str | None) -> str:
    validate_filename(filename)
    if document_exists(config, user_id, filename):
        raise ValueError(f"A document named '{filename}' already exists. Delete it first or rename the file before uploading.")
    key = build_object_key(user_id, filename)
    s3 = _session(config).client("s3", region_name=config.aws_region)
    extra = {"ContentType": content_type} if content_type else {}
    s3.put_object(Bucket=config.s3_data_source_bucket, Key=key, Body=file_bytes, **extra)
    return key


def build_embedding_key(user_id: str, filename: str) -> str:
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    return f"embeddings/{user_id}/{stem}.md"


def read_document_text(config: Config, user_id: str, filename: str) -> str:
    s3 = _session(config).client("s3", region_name=config.aws_region)
    obj = s3.get_object(Bucket=config.s3_data_source_bucket, Key=build_embedding_key(user_id, filename))
    return obj["Body"].read().decode("utf-8")


_MAX_METADATA_VALUE_LENGTH = 500


def _sanitize_metadata_value(value) -> str:
    text = "" if value is None else str(value)
    return text[:_MAX_METADATA_VALUE_LENGTH]


def upload_embedding_markdown(config: Config, user_id: str, filename: str, extracted: dict) -> str:
    key = build_embedding_key(user_id, filename)
    s3 = _session(config).client("s3", region_name=config.aws_region)
    metadata_fields = {}
    for k, v in extracted.items():
        if k == "full_text":
            continue
        sanitized = _sanitize_metadata_value(v)
        if sanitized:  # omit empty values entirely - Bedrock KB rejects "" as an invalid metadata value
            metadata_fields[k] = sanitized
    s3.put_object(
        Bucket=config.s3_data_source_bucket,
        Key=key,
        Body=extracted["full_text"].encode("utf-8"),
        ContentType="text/markdown",
    )
    s3.put_object(
        Bucket=config.s3_data_source_bucket,
        Key=f"{key}.metadata.json",
        Body=json.dumps({"metadataAttributes": {"user_id": user_id, **metadata_fields}}).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def _read_metadata_sidecar(s3, bucket: str, embedding_key: str) -> dict:
    try:
        obj = s3.get_object(Bucket=bucket, Key=f"{embedding_key}.metadata.json")
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
            return {}
        raise
    return json.loads(obj["Body"].read()).get("metadataAttributes", {})


def delete_document(config: Config, user_id: str, filename: str) -> None:
    s3 = _session(config).client("s3", region_name=config.aws_region)
    original_key = build_object_key(user_id, filename)
    embedding_key = build_embedding_key(user_id, filename)
    keys = [
        original_key,
        f"{original_key}.metadata.json",  # legacy sidecar, from before extraction was split into embeddings/
        embedding_key,
        f"{embedding_key}.metadata.json",
    ]
    resp = s3.delete_objects(
        Bucket=config.s3_data_source_bucket,
        Delete={"Objects": [{"Key": key} for key in keys]},
    )
    errors = resp.get("Errors", [])
    if errors:
        details = "; ".join(f"{e['Key']}: {e['Code']} - {e['Message']}" for e in errors)
        raise RuntimeError(f"Failed to delete some objects: {details}")


def list_user_documents(config: Config, user_id: str) -> list[dict]:
    s3 = _session(config).client("s3", region_name=config.aws_region)
    prefix = f"uploads/{user_id}/"
    paginator = s3.get_paginator("list_objects_v2")
    documents = []
    for page in paginator.paginate(Bucket=config.s3_data_source_bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".metadata.json"):
                continue
            name = key[len(prefix) :]
            sidecar = _read_metadata_sidecar(
                s3, config.s3_data_source_bucket, build_embedding_key(user_id, name)
            )
            documents.append(
                {
                    "name": name,
                    "size_bytes": obj["Size"],
                    "uploaded_at": obj["LastModified"],
                    "document_type": sidecar.get("document_type", ""),
                    "provider_name": sidecar.get("provider_name", ""),
                    "provider_type": sidecar.get("provider_type", ""),
                    "payer": sidecar.get("payer", ""),
                    "amount_paid": sidecar.get("amount_paid", ""),
                    "visit_date": sidecar.get("visit_date") or sidecar.get("document_date", ""),
                }
            )
    documents.sort(key=lambda d: d["uploaded_at"], reverse=True)
    return documents


def start_ingestion_job(config: Config) -> str:
    client = _session(config).client("bedrock-agent", region_name=config.aws_region)
    resp = client.start_ingestion_job(
        knowledgeBaseId=config.bedrock_knowledge_base_id,
        dataSourceId=config.bedrock_data_source_id,
    )
    return resp["ingestionJob"]["ingestionJobId"]
