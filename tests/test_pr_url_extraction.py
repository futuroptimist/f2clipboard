import pytest

from f2clipboard.codex_task import _extract_pr_url


@pytest.mark.parametrize(
    "html",
    [
        '<a href="https://github.com/owner/repo/pull/123">View PR</a>',
        "<a href='https://github.com/owner/repo/pull/123'>View PR</a>",
        '<a href="https://github.com/owner/repo/pull/123?utm_source=codex">PR</a>',
        "<a href='https://github.com/owner/repo/pull/123#discussion'>PR</a>",
        '<a href="https://github.com/owner/repo/pull/123/">PR</a>',
    ],
)
def test_extract_pr_url_success(html: str) -> None:
    assert _extract_pr_url(html) == "https://github.com/owner/repo/pull/123"


def test_extract_pr_url_missing() -> None:
    assert _extract_pr_url("<html></html>") is None
