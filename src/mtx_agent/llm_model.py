from langchain_aws import ChatBedrockConverse


def bedrock_llm_model(temperature: float = 0.5, top_p: float | None = None):
    return ChatBedrockConverse(
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        temperature=temperature,
        top_p=top_p,
    )
