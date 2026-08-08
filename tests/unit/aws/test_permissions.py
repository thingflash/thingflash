from thingflash.aws import permissions


def test_policy_document_covers_all_required_actions() -> None:
    document = permissions.build_policy_document()
    assert document["Version"] == "2012-10-17"
    granted = {
        action
        for statement in document["Statement"]
        for action in statement["Action"]
    }
    assert granted == set(permissions.REQUIRED_ACTIONS) | set(permissions.DIAGNOSTICS_ACTIONS)


def test_policy_document_grants_simulate_for_self_check() -> None:
    document = permissions.build_policy_document()
    granted = {a for s in document["Statement"] for a in s["Action"]}
    assert "iam:SimulatePrincipalPolicy" in granted
    assert "iam:SimulatePrincipalPolicy" not in permissions.REQUIRED_ACTIONS


def test_policy_document_has_one_statement_per_group_plus_diagnostics() -> None:
    document = permissions.build_policy_document()
    statements = document["Statement"]
    assert len(statements) == len(permissions.ACTION_GROUPS) + 1
    for statement in statements:
        assert statement["Effect"] == "Allow"
        assert statement["Resource"] == "*"
        assert statement["Sid"]
