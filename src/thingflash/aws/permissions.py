from __future__ import annotations

IOT_ACTIONS = [
    "iot:CreateThing",
    "iot:CreateKeysAndCertificate",
    "iot:CreatePolicy",
    "iot:AttachPolicy",
    "iot:AttachThingPrincipal",
    "iot:DescribeEndpoint",
]

IAM_ROLE_ACTIONS = [
    "iam:CreateRole",
    "iam:GetRole",
    "iam:PassRole",
    "iam:AttachRolePolicy",
    "iam:PutRolePolicy",
]

STORAGE_ACTIONS = [
    "s3:CreateBucket",
    "s3:PutObject",
    "dynamodb:CreateTable",
]

CLOUDFORMATION_ACTIONS = [
    "cloudformation:CreateStack",
    "cloudformation:DescribeStacks",
]

ACTION_GROUPS: dict[str, list[str]] = {
    "iot": IOT_ACTIONS,
    "iam-roles": IAM_ROLE_ACTIONS,
    "storage": STORAGE_ACTIONS,
    "cloudformation": CLOUDFORMATION_ACTIONS,
}

REQUIRED_ACTIONS: list[str] = [
    action for actions in ACTION_GROUPS.values() for action in actions
]

DIAGNOSTICS_ACTIONS = ["iam:SimulatePrincipalPolicy"]
POLICY_NAME = "ThingFlashDeploy"
_SID_BY_GROUP: dict[str, str] = {
    "iot": "ThingFlashIoT",
    "iam-roles": "ThingFlashIamRoles",
    "storage": "ThingFlashStorage",
    "cloudformation": "ThingFlashCloudFormation",
}


def build_policy_document() -> dict[str, object]:
    """Return a least-privilege IAM policy document granting REQUIRED_ACTIONS.

    One ``Allow`` statement per capability group so denials map back to a
    recognisable Sid. ``Resource`` is ``*``: the actions here create the very
    resources ThingFlash manages, so their ARNs are not known ahead of time.

    A trailing ``ThingFlashDiagnostics`` statement grants
    ``iam:SimulatePrincipalPolicy`` so ``thingflash doctor`` can self-check the
    other actions against the very identity this policy is attached to.
    """
    statements: list[dict[str, object]] = [
        {
            "Sid": _SID_BY_GROUP[group],
            "Effect": "Allow",
            "Action": list(actions),
            "Resource": "*",
        }
        for group, actions in ACTION_GROUPS.items()
    ]
    statements.append(
        {
            "Sid": "ThingFlashDiagnostics",
            "Effect": "Allow",
            "Action": list(DIAGNOSTICS_ACTIONS),
            "Resource": "*",
        }
    )
    return {"Version": "2012-10-17", "Statement": statements}
