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
from tavily import TavilyClient

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults sourced from environment
# ---------------------------------------------------------------------------

DEFAULT_URL   = os.getenv("LLM_API_URL",  "https://api.openai.com/v1/chat/completions")
DEFAULT_KEY   = os.getenv("LLM_API_KEY",  "")
DEFAULT_MODEL = os.getenv("LLM_MODEL",    "gpt-4o-mini")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

USER_ROLE   = "user"
SYSTEM_ROLE = "system"
AVAILABLE_ROLES = [USER_ROLE, SYSTEM_ROLE]


RECOMMENDATION_PROMPT = '''
You are an expert Search Engine Optimization (SEO) Consultant. You are helping a client optimize their site contents to improve their search engine ranking for a specific search. 

Your client's web site is {url}.

Here is the web search that your client seeks your help with.

Search: {search}

You performed this search and came up with the following top results:

{search_results}

Your task is to provide 3-5 concise insights for your client: what are these sites doing that makes them score so well for this search?  Please keep your answer brief and to the point, your client is looking for takeaways they can immediately use to improve their own rank.  

Remember! You are the SEO Consultant, presenting your results to your client.  When referring to the client, use "you," "your," "your site," and *not* phrases such as "your client" or "your client's site."

'''


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
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
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



async def search(query: str) -> list[dict]:
    """
    Search for *query* via Tavily and return a list of result dicts, each with
    keys: url, title, content, score.  Returns an empty list on error.
    """
    import asyncio
    try:
        tavily_client = TavilyClient(api_key=TAVILY_KEY)
        response = await asyncio.to_thread(
            tavily_client.search, query, search_depth="fast"
        )
        return [
            {
                "url":     r.get("url", ""),
                "title":   r.get("title", ""),
                "content": r.get("content", ""),
                "score":   r.get("score"),
            }
            for r in response.get("results", [])
        ]
    except Exception as err:
        logger.error("Couldn't complete search request: %s", err)
        return []
    

async def explain_relevance(query: str, url: str, search_results: list[dict]) -> str:
    return await get_completions(
        messages=[
            system_message(RECOMMENDATION_PROMPT.format(url=url, search=query, search_results=str(search_results))),
            user_message("How do these sites perform so well for this search?")
        ]
    )
