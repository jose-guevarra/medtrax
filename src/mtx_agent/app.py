import base64
import json

from bedrock_agentcore import BedrockAgentCoreApp
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from RetrieverAgent import RetrieverAgent

app = BedrockAgentCoreApp()
agent = RetrieverAgent(app.logger).get_agent_graph()

load_dotenv()

app.logger.setLevel("INFO")


def __build_messages(conversation_history, user_input):
    messages = []
    for conversation in conversation_history:
        if conversation.get("role") == "user":
            messages.append(HumanMessage(content=conversation.get("content", "")))
        elif conversation.get("role") == "assistant":
            messages.append(AIMessage(content=conversation.get("content", "")))

    messages.append(HumanMessage(content=user_input))
    return messages


def __process_stream_chunk(message_chunk):
    if not message_chunk.content:
        return

    text = message_chunk.content[0].get("text")
    if not text:
        return

    yield {"type": "text", "text": text}


def __decode_jwt_claims(token: str) -> dict:
    payload = token.split(".")[1]
    padded = payload + "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def __extract_user_id(context) -> str | None:
    # Unverified decode is safe here: AgentCore's custom_jwt_authorizer already
    # validates this bearer token's signature before this entrypoint runs.
    headers = (context.request_headers or {}) if context else {}
    auth_header = headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        app.logger.warning("No Authorization header present; user_id will be unset")
        return None
    try:
        return __decode_jwt_claims(token).get("sub")
    except Exception:
        app.logger.warning("Failed to decode bearer token claims")
        return None


@app.entrypoint
def invoke_agent(payload, context):
    app.logger.info("Starting agent.")
    app.logger.info(payload)

    user_input = payload.get("prompt", "")
    conversation_history = payload.get("conversation_history", [])
    user_id = __extract_user_id(context)

    if not user_input:
        yield {
            "type": "error",
            "text": "No user input provided",
            "error_details": "No user input provided",
        }
        return

    try:
        messages = __build_messages(conversation_history, user_input)
        initial_state = {
            "messages": messages,
            "generated_agent_queries": [],
            "user_id": user_id,
        }
    except Exception as exc:
        app.logger.error("Error creating initial state for agent graph")
        yield {
            "type": "error",
            "text": "Something went wrong while creating initial state for agent graph.",
            "error_details": str(exc),
        }
        return

    try:
        for chunk, metadata in agent.stream(
            initial_state,
            stream_mode="messages",
        ):
            if metadata.get("langgraph_node") == "generate_answer":
                yield from __process_stream_chunk(chunk)
    except Exception as exc:
        app.logger.error("Streaming agent response failed")
        yield {
            "type": "error",
            "text": "Something went wrong while streaming the response.",
            "error_details": str(exc),
        }
        return


if __name__ == "__main__":
    app.run()
