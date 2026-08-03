import boto3

from core.config import Config


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def _stem(name: str) -> str:
    return name.rsplit(".", 1)[0] if "." in name else name


def _filename(s3_uri: str) -> str:
    return s3_uri.rsplit("/", 1)[-1] if s3_uri else ""


def retrieve_documents(config: Config, user_id: str, question: str, k: int = 5) -> list[dict]:
    client = _session(config).client("bedrock-agent-runtime", region_name=config.aws_region)
    resp = client.retrieve(
        knowledgeBaseId=config.bedrock_knowledge_base_id,
        retrievalQuery={"text": question},
        retrievalConfiguration={
            "vectorSearchConfiguration": {
                "numberOfResults": k,
                "filter": {"equals": {"key": "user_id", "value": user_id}},
            }
        },
    )
    return resp.get("retrievalResults", [])


def run_hit_rate(config: Config, user_id: str, rows: list[dict], k: int = 5) -> tuple[list[dict], float]:
    results = []
    hits = 0
    for row in rows:
        question = row["question"]
        expected = row["expected_document"]
        retrieved = retrieve_documents(config, user_id, question, k)
        retrieved_names = [_filename(r.get("location", {}).get("s3Location", {}).get("uri", "")) for r in retrieved]
        hit = any(_stem(expected) == _stem(name) for name in retrieved_names if name)
        hits += int(hit)
        results.append(
            {
                "question": question,
                "expected_document": expected,
                "source": row.get("source", ""),
                "retrieved": retrieved_names,
                "hit": hit,
            }
        )
    hit_rate = hits / len(rows) if rows else 0.0
    return results, hit_rate
