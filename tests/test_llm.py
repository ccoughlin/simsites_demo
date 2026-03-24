"""Unit tests for services/llm.py."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from services.llm import (
    get_completions,
    get_embeddings,
    system_message,
    user_message,
    SYSTEM_ROLE,
    USER_ROLE,
)


# ---------------------------------------------------------------------------
# Message helpers
# ---------------------------------------------------------------------------

def test_user_message():
    msg = user_message("hello")
    assert msg == {"role": USER_ROLE, "content": "hello"}


def test_system_message():
    msg = system_message("you are an assistant")
    assert msg == {"role": SYSTEM_ROLE, "content": "you are an assistant"}


def test_user_message_extra_kwargs():
    msg = user_message("hi", name="Alice")
    assert msg["name"] == "Alice"


def test_invalid_role_raises():
    from services.llm import _chat_message
    with pytest.raises(ValueError, match="not available"):
        _chat_message("unknown", "content")


# ---------------------------------------------------------------------------
# get_completions
# ---------------------------------------------------------------------------

def _mock_response(status: int, body: dict) -> MagicMock:
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status
    mock.text = json.dumps(body)
    return mock


_COMPLETIONS_BODY = {
    "choices": [{"message": {"content": "Here are your SEO tips."}}]
}


@pytest.mark.asyncio
async def test_get_completions_returns_content():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(200, _COMPLETIONS_BODY))

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_completions(
            [user_message("give me SEO tips")],
            api_key="test-key",
        )

    assert result == "Here are your SEO tips."


@pytest.mark.asyncio
async def test_get_completions_non_200_returns_none():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(401, {"error": "Unauthorized"}))

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_completions([user_message("hi")], api_key="bad-key")

    assert result is None


@pytest.mark.asyncio
async def test_get_completions_exception_returns_none():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_completions([user_message("hi")], api_key="key")

    assert result is None


# ---------------------------------------------------------------------------
# get_embeddings
# ---------------------------------------------------------------------------

def _embeddings_body(vectors: list[list[float]]) -> dict:
    return {"data": [{"embedding": v} for v in vectors]}


@pytest.mark.asyncio
async def test_get_embeddings_returns_vectors():
    vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(200, _embeddings_body(vectors)))

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_embeddings(["text one", "text two"], api_key="key")

    assert result == vectors


@pytest.mark.asyncio
async def test_get_embeddings_non_200_returns_empty():
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=_mock_response(500, {}))

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_embeddings(["text"], api_key="key")

    assert result == []


@pytest.mark.asyncio
async def test_get_embeddings_chunking():
    """Verify that more than chunk_size inputs trigger multiple API calls."""
    vectors = [[float(i)] for i in range(6)]
    responses = [
        _mock_response(200, _embeddings_body(vectors[:3])),
        _mock_response(200, _embeddings_body(vectors[3:])),
    ]
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=responses)

    with patch("services.llm.httpx.AsyncClient", return_value=mock_client):
        result = await get_embeddings(
            ["a", "b", "c", "d", "e", "f"],
            api_key="key",
            chunk_size=3,
        )

    assert result == vectors
    assert mock_client.post.call_count == 2
