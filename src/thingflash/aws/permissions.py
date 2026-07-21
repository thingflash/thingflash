from __future__ import annotations

# IoT Core: things, certificates, and policies.
IOT_ACTIONS = [
    "iot:CreateThing",
    "iot:CreateKeysAndCertificate",
    "iot:CreatePolicy",
    "iot:AttachPolicy",
    "iot:AttachThingPrincipal",
    "iot:DescribeEndpoint",
]

# IAM: the roles ThingFlash creates and passes to AWS services.
IAM_ROLE_ACTIONS = [
    "iam:CreateRole",
    "iam:GetRole",
    "iam:PassRole",
    "iam:AttachRolePolicy",
    "iam:PutRolePolicy",
]

# Storage: telemetry sinks.
STORAGE_ACTIONS = [
    "s3:CreateBucket",
    "s3:PutObject",
    "dynamodb:CreateTable",
]

# Orchestration: CloudFormation stacks used to manage the resources.
CLOUDFORMATION_ACTIONS = [
    "cloudformation:CreateStack",
    "cloudformation:DescribeStacks",
]

# Grouped view (useful for reporting denials by capability).
ACTION_GROUPS: dict[str, list[str]] = {
    "iot": IOT_ACTIONS,
    "iam-roles": IAM_ROLE_ACTIONS,
    "storage": STORAGE_ACTIONS,
    "cloudformation": CLOUDFORMATION_ACTIONS,
}

# Flat list of every action to simulate.
REQUIRED_ACTIONS: list[str] = [
    action for actions in ACTION_GROUPS.values() for action in actions
]
