import aws_cdk as core
import aws_cdk.assertions as assertions

from medtrax.kb_stack import MedTraxKbStack
from medtrax.medtrax_stack import MedtraxStack


# example tests. To run these tests, uncomment this file along with the example
# resource in medtrax/medtrax_stack.py
#def test_sqs_queue_created():
#    app = core.App()
#    stack = MedtraxStack(app, "medtrax")
#    template = assertions.Template.from_stack(stack)


def test_bedrock_knowledge_base_stack_synthesizes():
    app = core.App()
    stack = MedTraxKbStack(
        app,
        "medtrax-kb",
        log_level="INFO",
        aws_env={"account": "123456789012", "region": "us-east-1"},
        env={"account": "123456789012", "region": "us-east-1"},
    )
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::Bedrock::KnowledgeBase", 1)
    template.has_resource_properties(
        "AWS::Bedrock::KnowledgeBase",
        {
            "Name": "multimodal-rag-s3vector-kb",
            "KnowledgeBaseConfiguration": {
                "Type": "VECTOR",
                "VectorKnowledgeBaseConfiguration": {
                    "EmbeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
                },
            },
            "StorageConfiguration": {
                "Type": "S3_VECTORS",
            },
        },
    )
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                    }
                ]
            }
        },
    )
    template.has_resource_properties(
        "AWS::IAM::Policy",
        {
            "PolicyDocument": assertions.Match.object_like(
                {
                    "Statement": assertions.Match.array_with([
                        assertions.Match.object_like(
                            {
                                "Action": assertions.Match.array_with([
                                    "s3vectors:WriteVectors",
                                    "s3vectors:ReadVectors",
                                    "s3vectors:GetVectors",
                                    "s3vectors:QueryVectors",
                                    "s3vectors:GetVectorIndex",
                                    "s3vectors:ListVectorIndexes",
                                ]),
                                "Effect": "Allow",
                            }
                        )
                    ])
                }
            )
        },
    )

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
