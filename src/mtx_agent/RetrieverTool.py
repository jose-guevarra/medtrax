import os
from typing import Annotated

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_core.documents import Document
from langgraph.prebuilt import InjectedState

load_dotenv()

bedrock_knowledge_base_id = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")


def extract_document_content(document: Document) -> Document:
    metadata = document.metadata
    if metadata.get("type").lower() == "text":
        return document
    elif metadata.get("type").lower() == "image":
        return Document(
            metadata=metadata,
            page_content=metadata.get("source_metadata", {}).get(
                "x-amz-bedrock-kb-description", ""
            ),
        )


def build_retriever(user_id: str | None) -> AmazonKnowledgeBasesRetriever:
    retrieval_config = {"vectorSearchConfiguration": {"numberOfResults": 5}}
    if user_id:
        retrieval_config["vectorSearchConfiguration"]["filter"] = {
            "equals": {"key": "user_id", "value": user_id}
        }

    return AmazonKnowledgeBasesRetriever(
        knowledge_base_id=bedrock_knowledge_base_id,
        retrieval_config=retrieval_config,
    )


def extract_source(document: Document) -> dict:
    metadata = document.metadata
    return {
        "s3_uri": metadata.get("location", {}).get("s3Location", {}).get("uri", ""),
        "score": metadata.get("score", 0),
        "document_type": metadata.get("source_metadata", {}).get("document_type", ""),
    }


@tool(response_format="content_and_artifact")
def knowledge_base_retriever(
    query: str, state: Annotated[dict, InjectedState]
) -> tuple[list[Document], list[dict]]:
    """Search and retrieve information from the user's medical records (medical reports and bills)."""

    retriever = build_retriever(state.get("user_id"))
    documents = retriever.invoke(query)

    content = [extract_document_content(document) for document in documents]
    sources = [extract_source(document) for document in documents]
    return content, sources


@tool
def sum_integers(a: int, b: int) -> int:
    """Add two integers together and return the sum."""
    return a + b
