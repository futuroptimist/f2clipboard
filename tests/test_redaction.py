from f2clipboard.redaction import redact_secrets


def test_redact_github_token():
    token = "ghp_1234567890abcdef1234567890abcdef1234"
    text = f"token={token}"
    assert redact_secrets(text) == "token=[REDACTED]"


def test_redact_aws_access_key():
    key = "AKIA1234567890ABCDEF"
    text = f"key {key}"
    assert redact_secrets(text) == "key [REDACTED]"
