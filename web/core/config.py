import os
from dataclasses import dataclass

import streamlit as st
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    aws_region: str
    aws_profile: str | None
    cognito_user_pool_id: str
    cognito_client_id: str
    agentcore_runtime_arn: str
    s3_data_source_bucket: str
    bedrock_knowledge_base_id: str
    bedrock_data_source_id: str
    feedback_table_name: str
    retrieval_table_name: str
    debug: bool


@st.cache_resource
def load_config() -> Config:
    load_dotenv()

    def require(key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise RuntimeError(f"Missing required env var: {key} (check web/.env)")
        return value

    return Config(
        aws_region=os.environ.get("AWS_REGION", "us-east-1"),
        aws_profile=os.environ.get("AWS_PROFILE") or None,
        cognito_user_pool_id=require("COGNITO_USER_POOL_ID"),
        cognito_client_id=require("COGNITO_CLIENT_ID"),
        agentcore_runtime_arn=require("AGENTCORE_RUNTIME_ARN"),
        s3_data_source_bucket=require("S3_DATA_SOURCE_BUCKET"),
        bedrock_knowledge_base_id=require("BEDROCK_KNOWLEDGE_BASE_ID"),
        bedrock_data_source_id=require("BEDROCK_DATA_SOURCE_ID"),
        feedback_table_name=require("FEEDBACK_TABLE_NAME"),
        retrieval_table_name=require("RETRIEVAL_TABLE_NAME"),
        debug=os.environ.get("DEBUG", "").strip().lower() in ("true", "1"),
    )
