"""Minimal LLM helpers used by f2clipboard."""

from __future__ import annotations

import httpx

from .config import Settings


async def _summarise_openai(text: str, api_key: str) -> str:
    """Summarise text using OpenAI's chat completions API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Summarise the following CI log."},
            {"role": "user", "content": text},
        ],
        "temperature": 0,
        "max_tokens": 200,
    }
    async with httpx.AsyncClient(base_url="https://api.openai.com/v1") as client:
        response = await client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def _anthropic_payload(text: str) -> dict[str, object]:
    return {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 200,
        "messages": [
            {"role": "user", "content": f"Summarise the following CI log:\n{text}"}
        ],
    }


async def _summarise_anthropic(text: str, api_key: str) -> str:
    """Summarise text using Anthropic's messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    async with httpx.AsyncClient(base_url="https://api.anthropic.com/v1") as client:
        response = await client.post(
            "/messages", json=_anthropic_payload(text), headers=headers
        )
        response.raise_for_status()
        data = response.json()
        # API returns list of content blocks; we expect first item is text
        return data["content"][0]["text"].strip()


async def summarise_log(text: str, settings: Settings) -> str:
    """Return an LLM-generated summary for the given log.

    If neither OpenAI nor Anthropic credentials are configured, a truncated
    snippet of the log is returned instead of calling a remote API.
    """
    try:
        if settings.openai_api_key:
            return await _summarise_openai(text, settings.openai_api_key)
        if settings.anthropic_api_key:
            return await _summarise_anthropic(text, settings.anthropic_api_key)
    except Exception:
        # Fall back to truncation on any API error
        pass
    return text[:100] + "\n…\n"
