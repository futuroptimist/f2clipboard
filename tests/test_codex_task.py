import gzip

from f2clipboard.codex_task import _decode_log, _extract_pr_url, _parse_pr_url


def test_extract_pr_url_success():
    html = '<html><a href="https://github.com/owner/repo/pull/123">PR</a></html>'
    assert _extract_pr_url(html) == "https://github.com/owner/repo/pull/123"


def test_extract_pr_url_missing():
    assert _extract_pr_url("<html></html>") is None


def test_parse_pr_url():
    assert _parse_pr_url("https://github.com/owner/repo/pull/42") == (
        "owner",
        "repo",
        42,
    )


def test_decode_log_handles_gzip():
    data = gzip.compress(b"hello")
    assert _decode_log(data) == "hello"


def test_decode_log_plain():
    assert _decode_log(b"plain") == "plain"
