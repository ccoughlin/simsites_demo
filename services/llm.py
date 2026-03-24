"""
Provider-agnostic LLM chat module.

Targets any OpenAI-compatible chat completions API (OpenAI, Anthropic via
compatibility layer, Mistral, Ollama, etc.) by accepting the endpoint URL,
API key, and model name as parameters.

Configuration via environment variables (all optional):
  LLM_API_URL   — completions endpoint  (default: OpenAI)
  LLM_API_KEY   — Bearer token
  LLM_MODEL     — model identifier      (default: gpt-4o-mini)
"""

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults sourced from environment
# ---------------------------------------------------------------------------

DEFAULT_URL   = os.getenv("LLM_API_URL",  "https://api.openai.com/v1/chat/completions")
DEFAULT_KEY   = os.getenv("LLM_API_KEY",  "")
DEFAULT_MODEL = os.getenv("LLM_MODEL",    "gpt-4o-mini")

USER_ROLE   = "user"
SYSTEM_ROLE = "system"
AVAILABLE_ROLES = [USER_ROLE, SYSTEM_ROLE]


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

def user_message(content: str, **kwargs) -> dict:
    """Build a user-role chat message dict."""
    return _chat_message(USER_ROLE, content, **kwargs)


def system_message(content: str) -> dict:
    """Build a system-role chat message dict."""
    return _chat_message(SYSTEM_ROLE, content)


def _chat_message(role: str, content: str, **kwargs) -> dict:
    if role not in AVAILABLE_ROLES:
        raise ValueError(f"Role '{role}' not available, must be one of {AVAILABLE_ROLES}")
    msg: dict[str, Any] = {"role": role, "content": content}
    msg.update(kwargs)
    return msg


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

async def get_completions(
    messages: list[dict],
    *,
    api_key: str = DEFAULT_KEY,
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
) -> str | None:
    """
    Send *messages* to the chat completions endpoint and return the
    assistant's reply, or None if the request fails.

    Args:
        messages:  Conversation history built with user_message / system_message.
        api_key:   Bearer token for the provider.
        url:       Completions endpoint URL.
        model:     Model identifier string.
        timeout:   Request timeout in seconds.

    Returns:
        The assistant message content string, or None on error.
    """
    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {"model": model, "messages": messages}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error("LLM API returned %s: %s", response.status_code, response.text)
            return None

        data = json.loads(response.text)
        return data["choices"][0]["message"]["content"]

    except Exception as exc:
        logger.exception("get_completions failed: %s", exc)
        return None


async def get_embeddings(
    lines: list[str],
    *,
    api_key: str = DEFAULT_KEY,
    url: str = os.getenv("LLM_EMBEDDINGS_URL", "https://api.openai.com/v1/embeddings"),
    model: str = os.getenv("LLM_EMBEDDINGS_MODEL", "text-embedding-3-small"),
    chunk_size: int = 25,
    timeout: int = 30,
) -> list[list[float]]:
    """
    Generate embeddings for *lines* using the provider's embeddings endpoint.

    Sends requests in chunks of *chunk_size* to avoid hitting payload limits.

    Returns:
        A list of embedding vectors (one per input line), or an empty list on error.
    """
    headers = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    embeddings: list[list[float]] = []

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            for chunk in [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"model": model, "input": chunk},
                )
                if response.status_code != 200:
                    logger.error("Embeddings API returned %s", response.status_code)
                    continue
                data = json.loads(response.text)
                embeddings.extend(item["embedding"] for item in data["data"])

    except Exception as exc:
        logger.exception("get_embeddings failed: %s", exc)

    return embeddings
