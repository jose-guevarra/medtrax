import time

import boto3

from core.config import Config


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def build_object_key(filename: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"uploads/{ts}-{filename.replace('/', '_')}"


def upload_document(config: Config, file_bytes: bytes, filename: str, content_type: str | None) -> str:
    key = build_object_key(filename)
    s3 = _session(config).client("s3", region_name=config.aws_region)
    extra = {"ContentType": content_type} if content_type else {}
    s3.put_object(Bucket=config.s3_data_source_bucket, Key=key, Body=file_bytes, **extra)
    return key


def start_ingestion_job(config: Config) -> str:
    client = _session(config).client("bedrock-agent", region_name=config.aws_region)
    resp = client.start_ingestion_job(
        knowledgeBaseId=config.bedrock_knowledge_base_id,
        dataSourceId=config.bedrock_data_source_id,
    )
    return resp["ingestionJob"]["ingestionJobId"]
