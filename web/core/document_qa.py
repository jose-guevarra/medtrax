import boto3

from core.config import Config

_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def _system_message(document_text: str) -> str:
    return (
        "You are a helpful assistant answering questions about a single medical "
        "document. Answer only using the document text below. If the answer isn't "
        "in the document, say so clearly rather than guessing.\n\n---\n" + document_text
    )


def answer_document_question_stream(config: Config, document_text: str, question: str, conversation_history: list[dict]):
    """conversation_history: list of {"role": "user"|"assistant", "content": str}. Yields text chunks."""
    client = _session(config).client("bedrock-runtime", region_name=config.aws_region)
    messages = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in conversation_history] + [
        {"role": "user", "content": [{"text": question}]}
    ]
    response = client.converse_stream(
        modelId=_MODEL_ID,
        system=[{"text": _system_message(document_text)}],
        messages=messages,
    )
    for event in response["stream"]:
        delta = event.get("contentBlockDelta", {}).get("delta", {})
        if "text" in delta:
            yield delta["text"]
