# Medtrax Web

Streamlit frontend for the Medtrax AgentCore RAG app. Logs into Cognito, uses
the access token to call the AgentCore runtime, and uploads documents to the
Bedrock Knowledge Base's S3 data source.

## Run locally

```bash
cp .env.example .env   # fill in real values, see infra/mtx/ terraform outputs
aws sso login --profile <your-profile>   # if using AWS_PROFILE for S3/Bedrock calls
uv sync
uv run streamlit run app.py
```
