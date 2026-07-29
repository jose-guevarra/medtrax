import json
import time
import urllib.parse
import uuid
from typing import Iterator

import requests

from core.config import Config


def build_invoke_url(runtime_arn: str, region: str) -> str:
    encoded_arn = urllib.parse.quote(runtime_arn, safe="")
    return f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"


def new_session_id() -> str:
    return f"medtrax-web-{uuid.uuid4().hex}-{int(time.time())}"


def invoke_agent_stream(
    config: Config,
    access_token: str,
    prompt: str,
    conversation_history: list[dict],
    runtime_session_id: str,
) -> Iterator[dict]:
    """Generator yielding parsed SSE event dicts: {"type": "text"|"error", "text": str, ...}."""
    url = build_invoke_url(config.agentcore_runtime_arn, config.aws_region)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": runtime_session_id,
    }
    body = {"prompt": prompt, "conversation_history": conversation_history}
    with requests.post(url, headers=headers, json=body, stream=True, timeout=(10, 180)) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            payload = line[len("data:"):].strip()
            if payload:
                yield json.loads(payload)
