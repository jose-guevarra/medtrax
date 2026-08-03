import json
from datetime import datetime, timezone
from pathlib import Path

_TEST_SET_PATH = Path(__file__).resolve().parents[2] / "src" / "mtx_agent" / "eval" / "test_set.jsonl"


def _stem(name: str) -> str:
    return name.rsplit(".", 1)[0] if "." in name else name


def load_ground_truth() -> list[dict]:
    if not _TEST_SET_PATH.exists():
        return []
    rows = []
    with _TEST_SET_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def ground_truth_for_document(expected_document: str) -> list[dict]:
    target = _stem(expected_document)
    return [row for row in load_ground_truth() if _stem(row.get("expected_document", "")) == target]


def append_ground_truth(question: str, expected_document: str, answer: str = "", source: str = "manual") -> None:
    record = {
        "question": question,
        "expected_document": expected_document,
        "answer": answer,
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _TEST_SET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _TEST_SET_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
