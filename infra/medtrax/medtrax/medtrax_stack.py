import os
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    # Duration,
    RemovalPolicy,
    Stack,
    aws_bedrockagentcore as agentcore,
    aws_s3 as s3,
    # aws_sqs as sqs,
)
from aws_cdk import aws_bedrock as bedrock

from constructs import Construct


SRC_PATH = Path(__file__).resolve().parent.parent / "dist"


class MedtraxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "MedtraxQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
        
        # S3 bucket containing the agent core
        code_bucket = s3.Bucket(self, "AgentCode",
            bucket_name="mtx-agentcode-bucket",
            removal_policy=RemovalPolicy.DESTROY
        )

        """
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_s3(s3.Location(
            bucket_name=code_bucket.bucket_name,
            object_key="deployment_package.zip"
        ), agentcore.AgentCoreRuntime.PYTHON_3_14, ["opentelemetry-instrument", "agent.py"])
        #"""

        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_code_asset(
            path=str(SRC_PATH),
            runtime=agentcore.AgentCoreRuntime.PYTHON_3_14,
            #entrypoint=["opentelemetry-instrument", "agent.py"]
            entrypoint=["agent.py"]
        )

        # Configure Lifecycle with Idle Timeout
        lifecycle_config = agentcore.LifecycleConfiguration(
            idle_runtime_session_timeout=cdk.Duration.minutes(5),  # <-- Set idle timeout here
            max_lifetime=cdk.Duration.hours(1)                      # Optional: Max instance life
        )


        runtime_instance = agentcore.Runtime(self, "MedTraxAgentRuntime",
            runtime_name="MedTraxAgent",
            description="MedTrax Agent Runtime",
            agent_runtime_artifact=agent_runtime_artifact,
            lifecycle_configuration=lifecycle_config
        )

        # Define the model (using CDK Bedrock Alpha construct)
        model = bedrock.FoundationModel.from_foundation_model_id(
            self, "NovaMicro1.0",
            #bedrock.FoundationModelIdentifier.ANTHROPIC_CLAUDE_3_5_SONNET_20241022_V2_0
            bedrock.FoundationModelIdentifier.AMAZON_NOVA_MICRO_V1_0
        )


        # Grant the runtime permission to invoke this specific model
        runtime_instance.grant(
            ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            [model.model_arn]
        )




