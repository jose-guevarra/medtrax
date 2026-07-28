output "ecr_repository_name" {
  value = aws_ecr_repository.agentcore_runtime_agent_code_ecr_repository.name
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.userpool_client.id
}

output "agentcore_runtime_id" {
  value = aws_bedrockagentcore_agent_runtime.agentcore_runtime.agent_runtime_id
}