"""
Root conftest — mock sentence_transformers before any module imports it so
the heavy model is never loaded during the test run.
"""
import sys
from unittest.mock import MagicMock

_mock_st = MagicMock()
sys.modules.setdefault('sentence_transformers', _mock_st)
