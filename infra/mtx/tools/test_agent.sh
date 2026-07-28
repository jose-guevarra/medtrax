#!/bin/bash


: '

'

ACCOUNT_ID=""
AGENTCORE_RUNTIME_ID="rtid-DKKDD"

TOKEN=""

SESSION_ID=""

PROMPT="In one sentence tell me about the method of the placebo effect experiment"


curl -X POST \
"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A${ACCOUNT_ID}%3Aruntime%2F${AGENTCORE_RUNTIME_ID}/invocations?qualifier=DEFAULT" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id: ${SESSION_ID}" \
  -d '{"prompt": ${PROMPT}, "conversation_history": []}'

