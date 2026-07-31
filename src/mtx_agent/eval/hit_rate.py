"""Offline hit_rate evaluator.

Measures the fraction of test questions where the expected source document
appears among the top-k retrieved documents (document-level match, since
documents are ingested as one markdown blob each with no page boundaries).

Before running, replace the placeholder rows in test_set.jsonl with real
questions and real filenames from documents you've actually uploaded (as
shown on the Documents page) - ground truth can't be guessed, it has to
reflect what's actually in your knowledge base.

Usage:
    python hit_rate.py --user-id <cognito-sub> [--test-set test_set.jsonl] [--k 5]
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from RetrieverTool import build_retriever, extract_source  # noqa: E402


def _stem(name: str) -> str:
    return name.rsplit(".", 1)[0] if "." in name else name


def _filename(s3_uri: str) -> str:
    return s3_uri.rsplit("/", 1)[-1] if s3_uri else ""


def evaluate(test_set_path: Path, user_id: str, k: int) -> float:
    retriever = build_retriever(user_id)
    hits = 0
    total = 0

    with test_set_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            question = row["question"]
            expected = row["expected_document"]

            documents = retriever.invoke(question)[:k]
            retrieved_names = [_filename(extract_source(doc)["s3_uri"]) for doc in documents]
            hit = any(_stem(expected) == _stem(name) for name in retrieved_names if name)

            total += 1
            hits += int(hit)
            status = "HIT " if hit else "MISS"
            print(f"[{status}] {question!r} -> expected {expected!r}, retrieved {retrieved_names}")

    hit_rate = hits / total if total else 0.0
    print(f"\nhit_rate = {hits}/{total} = {hit_rate:.2%}")
    return hit_rate


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute document-level hit_rate for the RAG retriever.")
    parser.add_argument("--user-id", required=True, help="Cognito user id (sub) whose documents to search")
    parser.add_argument(
        "--test-set",
        default=str(Path(__file__).parent / "test_set.jsonl"),
        help="Path to a JSONL file of {question, expected_document} rows",
    )
    parser.add_argument("--k", type=int, default=5, help="Top-k retrieved results to check")
    args = parser.parse_args()

    evaluate(Path(args.test_set), args.user_id, args.k)


if __name__ == "__main__":
    main()
