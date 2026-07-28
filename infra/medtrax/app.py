#!/usr/bin/env python3
import os

import aws_cdk as cdk

from medtrax.medtrax_stack import MedtraxStack
from medtrax.kb_stack import MedTraxKbStack


domain_app_name = 'mtx'

environment = os.getenv('ENVIRONMENT_TAG')
log_level = os.getenv('LOG_LEVEL', 'INFO')
postfix = ''

tags = {
    "Product": 'mtx',
    "Environment": environment,
}

region_map = {
    'as1': 'ap-southeast-1',
    'as2': 'ap-south-1',
    'eu1': 'eu-west-1',
    'eu2': 'eu-central-1',
    'na1': 'us-east-1',
    'na2': 'us-west-2',
    'sa1': 'sa-east-1',
}

if 'prod' == environment:
    regions = ['na1']
elif 'dev' == environment:
    regions = ['na1']
elif 'sandbox' == environment:
    regions = ['na1']
    postfix = '-sandbox'
else:
    regions = []


os.environ['POSTFIX'] = postfix
primary_region = 'na1'


# Stacks to deploy to primary region only
aws_account = os.getenv('CDK_DEFAULT_ACCOUNT')
aws_env={'account': aws_account, 'region': region_map[primary_region]}

app = cdk.App()

# Set tags on all resources.
for key, value in tags.items():
    if value is not None:
        cdk.Tags.of(app).add(key, value)

kb_stack = MedTraxKbStack(
            app,
            "MtxKbStack",
            log_level=log_level,
            aws_env=aws_env 
            )


mtx_stack = MedtraxStack(app, "MedtraxStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )


app.synth()
