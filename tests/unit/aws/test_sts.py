import pytest
from moto import mock_aws

from thingflash.aws import sts
from thingflash.aws.session import AWSUnavailableError, build_session


@mock_aws
def test_get_caller_identity_returns_identity(aws_credentials: None) -> None:
    session = build_session(region="us-east-1")
    identity = sts.get_caller_identity(session)
    assert identity.account
    assert identity.arn.startswith("arn:aws:")
    assert identity.user_id


def test_get_caller_identity_no_credentials_raises_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocore.exceptions import NoCredentialsError

    class _Client:
        def get_caller_identity(self) -> dict[str, str]:
            raise NoCredentialsError()

    monkeypatch.setattr(sts, "make_client", lambda service, **k: _Client())
    with pytest.raises(AWSUnavailableError):
        sts.get_caller_identity(session=None)  # type: ignore[arg-type]
