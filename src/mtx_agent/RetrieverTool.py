import os

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_core.documents import Document

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


@tool
def knowledge_base_retriever(query: str) -> str:
    """Search and retrieve information from the knowledge base."""

    retriever = AmazonKnowledgeBasesRetriever(
        knowledge_base_id=bedrock_knowledge_base_id,
        retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 5}},
    )
    documents = retriever.invoke(query)

    return [extract_document_content(document) for document in documents]
