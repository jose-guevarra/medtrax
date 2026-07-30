import boto3

from core.config import Config

_MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
_TOOL_NAME = "medical_document_extraction"


def _session(config: Config) -> boto3.Session:
    return boto3.Session(profile_name=config.aws_profile) if config.aws_profile else boto3.Session()


def build_extraction_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "amount_paid": {"type": "string", "maxLength": 20},
            "payer": {"type": "string", "maxLength": 100},
            "provider_name": {"type": "string", "maxLength": 150},
            "provider_type": {"type": "string", "maxLength": 100},
            "document_type": {"type": "string", "maxLength": 100},
            "provider_office_name": {"type": "string", "maxLength": 150},
            "provider_office_address": {"type": "string", "maxLength": 300},
            "document_date": {"type": "string", "maxLength": 20},
            "visit_date": {"type": "string", "maxLength": 20},
            "full_text": {"type": "string"},
        },
        "required": [
            "amount_paid",
            "payer",
            "provider_name",
            "provider_type",
            "document_type",
            "provider_office_name",
            "provider_office_address",
            "document_date",
            "visit_date",
            "full_text",
        ],
    }


def extraction_system_message() -> str:
    return (
        "You are an expert at reading medical reports and billing documents. "
        "Extract the amount paid, payer, provider, provider type, document type, provider office name, office address, "
        "document date, and visit date when visible. If something is not visible, return an empty string. "
        "Also extract all visible text from the document. "
    )


def extract_document_fields(config: Config, file_bytes: bytes, filename: str) -> dict:
    client = _session(config).client("bedrock-runtime", region_name=config.aws_region)
    response = client.converse(
        modelId=_MODEL_ID,
        system=[{"text": extraction_system_message()}],
        messages=[
            {
                "role": "user",
                "content": [
                    {"document": {"format": "pdf", "name": "uploaded_document", "source": {"bytes": file_bytes}}},
                    {"text": f"Extract the requested fields from the attached document ({filename})."},
                ],
            }
        ],
        toolConfig={
            "tools": [
                {
                    "toolSpec": {
                        "name": _TOOL_NAME,
                        "description": "Structured extraction of key fields from a medical report or billing document.",
                        "inputSchema": {"json": build_extraction_schema()},
                    }
                }
            ],
            "toolChoice": {"tool": {"name": _TOOL_NAME}},
        },
    )
    for block in response["output"]["message"]["content"]:
        if "toolUse" in block:
            return block["toolUse"]["input"]
    raise RuntimeError("Model did not return structured extraction output.")
