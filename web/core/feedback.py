import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from core.config import Config

# st.feedback("thumbs") returns 0 (thumbs down) or 1 (thumbs up); map to storage labels.
RATING_LABELS = {0: "down", 1: "up"}
_VALID_RATINGS = set(RATING_LABELS.values())


def _log_path(config: Config) -> Path:
    path = Path(config.feedback_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def record_feedback(
    config: Config,
    *,
    user_id: str | None,
    session_id: str | None,
    message_id: str,
    rating: str,
    response_text: str,
    prompt_text: str | None,
) -> None:
    if rating not in _VALID_RATINGS:
        raise ValueError(f"Invalid rating: {rating!r} (expected one of {sorted(_VALID_RATINGS)})")
    record = {
        "feedback_id": uuid.uuid4().hex,
        "message_id": message_id,
        "session_id": session_id,
        "user_id": user_id,
        "rating": rating,
        "prompt_text": prompt_text,
        "response_text": response_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _log_path(config).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
