import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.config import Config


def _log_path(config: Config) -> Path:
    path = Path(config.retrieval_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


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
        "sources": sources,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _log_path(config).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
