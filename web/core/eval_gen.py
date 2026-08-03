import boto3

from core.config import Config

_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
_TOOL_NAME = "generate_question_variants"


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def generate_question_variants(
    config: Config, document_text: str, existing_questions: list[str], count: int = 5
) -> list[str]:
    client = _session(config).client("bedrock-runtime", region_name=config.aws_region)
    existing_block = "\n".join(f"- {q}" for q in existing_questions) or "(none yet)"
    prompt = (
        f"Document:\n{document_text}\n\n"
        f"Existing questions already asked about this document:\n{existing_block}\n\n"
        f"Generate {count} new questions a user might ask about this document. Each must be "
        "meaningfully different in wording and phrasing from the existing questions and from "
        "each other, but must still be answerable from the document above."
    )
    response = client.converse(
        modelId=_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        toolConfig={
            "tools": [
                {
                    "toolSpec": {
                        "name": _TOOL_NAME,
                        "description": "Return a list of newly generated question variants.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "questions": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "minItems": count,
                                        "maxItems": count,
                                    }
                                },
                                "required": ["questions"],
                            }
                        },
                    }
                }
            ],
            "toolChoice": {"tool": {"name": _TOOL_NAME}},
        },
    )
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return block["toolUse"]["input"]["questions"]
    raise RuntimeError("Model did not return generated questions.")
