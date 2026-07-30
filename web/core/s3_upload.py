import json

import boto3

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


def upload_document(config: Config, user_id: str, file_bytes: bytes, filename: str, content_type: str | None) -> str:
    validate_filename(filename)
    key = build_object_key(user_id, filename)
    s3 = _session(config).client("s3", region_name=config.aws_region)
    extra = {"ContentType": content_type} if content_type else {}
    s3.put_object(Bucket=config.s3_data_source_bucket, Key=key, Body=file_bytes, **extra)
    s3.put_object(
        Bucket=config.s3_data_source_bucket,
        Key=f"{key}.metadata.json",
        Body=json.dumps({"metadataAttributes": {"user_id": user_id}}).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def start_ingestion_job(config: Config) -> str:
    client = _session(config).client("bedrock-agent", region_name=config.aws_region)
    resp = client.start_ingestion_job(
        knowledgeBaseId=config.bedrock_knowledge_base_id,
        dataSourceId=config.bedrock_data_source_id,
    )
    return resp["ingestionJob"]["ingestionJobId"]
