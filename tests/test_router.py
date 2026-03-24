"""
Integration tests for routers/seo.py.

Uses FastAPI's TestClient with seo_analyzer.analyze mocked out so
there is no real network activity.
"""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from models.seo import AnalyzeResponse, SEOHint

client = TestClient(app)

_SAMPLE_RESPONSE = AnalyzeResponse(
    url="https://example.com",
    search_query="running shoes",
    score=80,
    hints=[
        SEOHint(
            category="title",
            severity="warning",
            message="The page title is a little long",
            recommendation="Try to shorten the title.",
        )
    ],
    page_image=None,
    semantic_similarity=0.72,
)


@pytest.fixture(autouse=True)
def mock_analyze():
    with patch("routers.seo.analyze", new=AsyncMock(return_value=_SAMPLE_RESPONSE)):
        yield


def test_analyze_returns_200():
    res = client.post("/api/seo/analyze", json={
        "url": "https://example.com",
        "search_query": "running shoes",
    })
    assert res.status_code == 200


def test_analyze_response_shape():
    res = client.post("/api/seo/analyze", json={
        "url": "https://example.com",
        "search_query": "running shoes",
    })
    data = res.json()
    assert data["score"] == 80
    assert data["semantic_similarity"] == pytest.approx(0.72)
    assert len(data["hints"]) == 1
    assert data["hints"][0]["severity"] == "warning"


def test_analyze_invalid_url_returns_422():
    res = client.post("/api/seo/analyze", json={
        "url": "not-a-url",
        "search_query": "running shoes",
    })
    assert res.status_code == 422


def test_analyze_missing_query_returns_422():
    res = client.post("/api/seo/analyze", json={"url": "https://example.com"})
    assert res.status_code == 422


def test_analyze_upstream_error_returns_502():
    with patch("routers.seo.analyze", new=AsyncMock(side_effect=Exception("timeout"))):
        res = client.post("/api/seo/analyze", json={
            "url": "https://example.com",
            "search_query": "running shoes",
        })
    assert res.status_code == 502
