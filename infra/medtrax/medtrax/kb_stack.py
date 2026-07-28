from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
    aws_bedrock as bedrock,
    aws_s3vectors as s3vectors
)
from constructs import Construct

class MedTraxKbStack(Stack):
    """Bedrock Knowledge Base """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        self.log_level = kwargs.pop('log_level')
        self.aws_env = kwargs.pop('aws_env')

        super().__init__(scope, construct_id, **kwargs)


        # -------------------------------------------------------------
        # 1. S3 BUCKETS: General Purpose vs. Vector Buckets
        # -------------------------------------------------------------
        
        # Raw Files Input - General Purpose S3 Bucket
        data_source_bucket = s3.Bucket(
            self, "RagDataSourceBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True
        )

        # Destination for extracted multimodal pieces - General Purpose S3 Bucket
        multimodal_storage_bucket = s3.Bucket(
            self, "RagMultimodalStorageBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True
        )

        # S3 Vector Buckets are purpose-built for high-dimensional vectors
        s3_vector_bucket = s3vectors.CfnVectorBucket(
            self, "RagS3VectorBucket",
            vector_bucket_name=f"rag-multimodal-vector-store-{self.account}"
        )

        # S3 Vector Buckets require an internal index configuration
        # Amazon Nova Multimodal Embeddings utilizes 3072 dimensions
        s3_vector_index = s3vectors.CfnIndex(
            self, "RagS3VectorIndex",
            vector_bucket_name=s3_vector_bucket.vector_bucket_name,
            index_name="multimodal-nova-index",
            data_type="float32",
            dimension=1024,                # Default dimension for Amazon Nova Multimodal Embeddings
            distance_metric="cosine"       # Optimal for multimodal search structures
        )
        s3_vector_index.add_dependency(s3_vector_bucket)

        # -------------------------------------------------------------
        # 2. IAM SERVICE ROLE & POLICY ACCESS
        # -------------------------------------------------------------
        kb_role = iam.Role(
            self, "BedrockKbServiceRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Service role for Bedrock Multimodal S3 Vectors Knowledge Base"
        )

        # Grant access to Nova Embeddings Model
        kb_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-image-v1"
            ]
        ))

        # Standard S3 permissions for inputs and outputs
        data_source_bucket.grant_read(kb_role)
        multimodal_storage_bucket.grant_read_write(kb_role)

        # S3 Vector bucket requires specific native 's3vectors:' API policies
        kb_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3vectors:WriteVectors",
                "s3vectors:ReadVectors",
                "s3vectors:GetVectors",
                "s3vectors:QueryVectors",
                "s3vectors:GetVectorIndex",
                "s3vectors:ListVectorIndexes"
            ],
            resources=[
                f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{s3_vector_bucket.vector_bucket_name}",
                f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{s3_vector_bucket.vector_bucket_name}/index/*"
            ]
        ))

        # -------------------------------------------------------------
        # 3. BEDROCK KNOWLEDGE BASE CONFIGURATION (Using S3_VECTORS)
        # -------------------------------------------------------------
        knowledge_base = bedrock.CfnKnowledgeBase(
            self, "MultimodalKnowledgeBase",
            name="multimodal-rag-s3vector-kb",
            role_arn=kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                )
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="S3_VECTORS",
                s3_vectors_configuration=bedrock.CfnKnowledgeBase.S3VectorsConfigurationProperty(
                    index_arn=s3_vector_index.attr_index_arn
                )
            )
        )
        knowledge_base.node.add_dependency(kb_role)

        # -------------------------------------------------------------
        # 4. DATA SOURCE CONFIGURATION WITH MULTIMODAL SETTINGS
        # -------------------------------------------------------------
        bedrock.CfnDataSource(
            self, "MultimodalS3DataSource",
            knowledge_base_id=knowledge_base.ref,
            name="s3-multimodal-docs-source",
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=data_source_bucket.bucket_arn,
                )
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                parsing_configuration=bedrock.CfnDataSource.ParsingConfigurationProperty(
                    parsing_strategy="BEDROCK_DATA_AUTOMATION",
                    bedrock_data_automation_configuration=bedrock.CfnDataSource.BedrockDataAutomationConfigurationProperty(
                        parsing_modality="MULTIMODAL"
                    )
                )
            )
        )
        