from f2clipboard.codex_task import _extract_pr_url


def test_extract_pr_url_success():
    html = '<html><a href="https://github.com/owner/repo/pull/123">PR</a></html>'
    assert _extract_pr_url(html) == "https://github.com/owner/repo/pull/123"


def test_extract_pr_url_missing():
    assert _extract_pr_url("<html></html>") is None
