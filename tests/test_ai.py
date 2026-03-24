"""
Unit tests for services/ai.py.

The sentence-transformers model is mocked in conftest.py so the real
weights are never loaded.
"""
from unittest.mock import MagicMock, patch
import pytest

import services.ai as ai_module


def _make_mock_model(raw_similarity: float) -> MagicMock:
    mock_model = MagicMock()
    mock_embeddings = [MagicMock(), MagicMock()]
    mock_model.encode.return_value = mock_embeddings

    with patch.object(ai_module, '_model', mock_model):
        # Also patch util.cos_sim to return the desired value
        pass

    return mock_model


def _run_similarity(raw: float, text: str = "page text", query: str = "query") -> float:
    mock_model = MagicMock()
    mock_embeddings = [MagicMock(), MagicMock()]
    mock_model.encode.return_value = mock_embeddings

    mock_util = MagicMock()
    mock_util.cos_sim.return_value = raw

    with patch.object(ai_module, '_model', mock_model), \
         patch.object(ai_module, 'util', mock_util):
        return ai_module.compute_similarity(text, query)


def test_compute_similarity_returns_float():
    result = _run_similarity(0.75)
    assert isinstance(result, float)

def test_compute_similarity_midrange():
    assert _run_similarity(0.75) == pytest.approx(0.75)

def test_compute_similarity_clamps_above_one():
    assert _run_similarity(1.5) == pytest.approx(1.0)

def test_compute_similarity_clamps_negative():
    assert _run_similarity(-0.3) == pytest.approx(0.0)

def test_compute_similarity_exactly_zero():
    assert _run_similarity(0.0) == pytest.approx(0.0)

def test_compute_similarity_exactly_one():
    assert _run_similarity(1.0) == pytest.approx(1.0)
