import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

from core.config import Config


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def _table(config: Config):
    return _session(config).resource("dynamodb", region_name=config.aws_region).Table(config.retrieval_table_name)


def _to_dynamo_number(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo_number(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo_number(v) for v in value]
    return value


def record_retrieval(
    config: Config,
    *,
    user_id: str | None,
    session_id: str | None,
    message_id: str,
    question: str,
    sources: list[dict],
) -> None:
    record = {
        "retrieval_id": uuid.uuid4().hex,
        "message_id": message_id,
        "session_id": session_id,
        "user_id": user_id,
        "question": question,
        "sources": _to_dynamo_number(sources),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _table(config).put_item(Item=record)
