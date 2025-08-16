import asyncio

from f2clipboard.config import Settings
from f2clipboard.llm import summarise_log


def test_openai_model_override(monkeypatch):
    called: dict[str, str] = {}

    async def fake_summarise_openai(text: str, api_key: str, model: str) -> str:
        called["model"] = model
        return "summary"

    monkeypatch.setattr("f2clipboard.llm._summarise_openai", fake_summarise_openai)
    settings = Settings(OPENAI_API_KEY="key", OPENAI_MODEL="gpt-4o-mini")
    result = asyncio.run(summarise_log("log text", settings))
    assert result == "summary"
    assert called["model"] == "gpt-4o-mini"
