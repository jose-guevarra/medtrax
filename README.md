# MedTrax - Personal Health Records app





## Table of Contents






## Problem Description

Medical receipts, bills, EOBs, and records pile up across different
providers, pharmacies, and visits, in paper and digital form. When you need
to answer a simple question later — how much did I spend on doctor visits
this year, what did that specialist say about my last checkup, do I have a
copy of that lab result — you're stuck digging through drawers, inboxes, and
photo rolls with no easy way to search or add it all up.

## Solution

Upload your medical receipts and documents in one place, and the app
organizes them automatically so you can browse and sort your spending by
provider, date, or amount at a glance. Ask it questions in plain English —
like "how much did I spend at Dr. Smith's office last year" or "what did my
last blood test show" — and get answers pulled directly from your own
documents, so you always know exactly where the information came from.

## Technology Stack

- **Python 3.14**, managed with `uv`
- **Frontend**: Streamlit (multi-page: login, chat, upload, documents)
- **Agent**: LangGraph + LangChain, running on Amazon Bedrock AgentCore Runtime, packaged as a Docker container in ECR
- **LLM**: Amazon Bedrock (Claude Haiku 4.5)
- **RAG**: Bedrock Knowledge Base with S3 Vectors + Titan embeddings v2
- **Auth**: Amazon Cognito (JWT)
- **Storage**: S3 (documents), DynamoDB (feedback + retrieval logs)
- **Infra**: Terraform
- **Observability**: OpenTelemetry

## Architecture

The web app is a multi-page Streamlit UI: log in via Cognito, upload health
records, browse them in a sortable table (type, provider, visit date, amount
paid — pulled out during ingestion), and chat with an assistant that answers
questions grounded in your own documents.

A chat request goes to the Bedrock AgentCore Runtime, a containerized
LangGraph agent that decides whether to retrieve from the Bedrock Knowledge
Base, then streams the answer back token by token along with the source
documents it used. Every answer gets a thumbs up/down, and both the sources
and the feedback are logged to DynamoDB — that log is the eval loop: a
hit_rate script replays a set of known question → expected-document pairs
against the retriever and reports how often the right document lands in the
top-k results, so retrieval quality can be checked after changes.

Uploaded documents land in S3, which feeds the Knowledge Base's ingestion
pipeline (chunking + embedding into an S3 Vectors index); deleting a document
removes it and kicks off a re-sync. Both the web app and the agent runtime
validate the same Cognito JWT, so retrieval, chat, and document access all
stay scoped to the user who made the request.


## Project Structure


# Demo


- User pages

- Metrics?


- Screen Capture

- 






## Results






## Future Improvements





## Installation

NOTE: 
Best way to deploy and run application is in VS Code DevContainers.
In VS Code, install the DevContainers extension.   





### Requirements

- Docker
- Python 3.14
- Run from Linux (or VSCode Devcontainers)
- Terraform
- AWS Account
- AWS Cli





Download repo and run bootstrap script that installs
Python deps and Terraform.


```
git clone https://github.com/jose-guevarra/medtrax.git
cd metrax

git checkout -b main <commit-sha> @TODO

```

```
sh bootstrap
```



## Deploy Instructions

### Step 1

Set your AWS_PROFILE and AWS_REGION=us-east-1


Run Terraform to deploy infrastructure

```
cd infra/mtx
terraform init
terraform plan
terraform apply
```

NOTE: This will fail due to no ECR image!

### Step 2 - Build initial Docker image

NOTE: Most DevContainer installations are not build to do container-in-container
Docker installation.  This means you will have to build the Docker image
on your host machine(machine running VSCode).  You should set you AWS credentials
on the host computer and run the `sh upload-agent-to-ecr.sh` command on the host manchine.

Build and upload initial ECR image.

```
cd infra/mtx/tools
sh upload-agent-to-ecr.sh
```

You should see a new Docker image in ECR in your AWS Account.


### Step 3 - ReDploy

Now that the image is in ECR, AWS Bedrock AgentCore can use it as the Runtime for the Agent.  So 
deploy using Terraform again.

```
terraform apply
```

When successfuly, take note of Output values of deployed resource.


# Web app

```
cd web
uv run streamlit run app.py
```




## Acknowledgements

