"""Minimal LLM helpers used by f2clipboard."""

from __future__ import annotations

import httpx

from .config import Settings


async def _summarise_openai(text: str, api_key: str, model: str) -> str:
    """Summarise text using OpenAI's chat completions API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
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


def _anthropic_payload(text: str, model: str) -> dict[str, object]:
    return {
        "model": model,
        "max_tokens": 200,
        "messages": [
            {"role": "user", "content": f"Summarise the following CI log:\n{text}"}
        ],
    }


async def _summarise_anthropic(text: str, api_key: str, model: str) -> str:
    """Summarise text using Anthropic's messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    async with httpx.AsyncClient(base_url="https://api.anthropic.com/v1") as client:
        response = await client.post(
            "/messages", json=_anthropic_payload(text, model), headers=headers
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
            return await _summarise_openai(
                text, settings.openai_api_key, settings.openai_model
            )
        if settings.anthropic_api_key:
            return await _summarise_anthropic(
                text, settings.anthropic_api_key, settings.anthropic_model
            )
    except Exception:
        # Fall back to truncation on any API error
        pass
    return text[:100] + "\n…\n"


async def _openai_conflict_patch(diff: str, api_key: str, model: str) -> str:
    """Request a merge-conflict patch suggestion from OpenAI."""

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You resolve git merge conflicts by producing unified diffs that "
                    "apply cleanly with `git apply`."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Resolve the following merge conflicts. "
                    "Return only the unified diff patch without explanation.\n\n"
                    f"{diff}"
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 1200,
    }
    async with httpx.AsyncClient(base_url="https://api.openai.com/v1") as client:
        response = await client.post("/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


async def _anthropic_conflict_patch(diff: str, api_key: str, model: str) -> str:
    """Request a merge-conflict patch suggestion from Anthropic."""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": model,
        "max_tokens": 1200,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Resolve the following git merge conflicts by returning a unified diff "
                    "patch suitable for `git apply`. Provide only the diff.\n\n"
                    f"{diff}"
                ),
            }
        ],
    }
    async with httpx.AsyncClient(base_url="https://api.anthropic.com/v1") as client:
        response = await client.post("/messages", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Anthropic responses contain blocks; expect first item is text
        return data["content"][0]["text"].strip()


async def generate_conflict_patch(diff: str, settings: Settings) -> str | None:
    """Generate a patch suggestion for merge conflicts using configured LLMs."""

    if not diff.strip():
        return None

    try:
        if settings.openai_api_key:
            return await _openai_conflict_patch(
                diff, settings.openai_api_key, settings.openai_model
            )
        if settings.anthropic_api_key:
            return await _anthropic_conflict_patch(
                diff, settings.anthropic_api_key, settings.anthropic_model
            )
    except Exception:
        return None
    return None
