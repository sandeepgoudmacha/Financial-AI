"""
Valura AI — Test Fixtures.

Shared fixtures for all test modules.
All tests run WITHOUT API keys.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env():
    """Ensure no real API keys are used in tests."""
    with patch.dict(os.environ, {
        "GROQ_API_KEY": "test-key-not-real",
        "GROQ_MODEL": "llama-3.3-70b-versatile",
        "GROQ_FAST_MODEL": "llama-3.1-8b-instant",
    }):
        yield


@pytest.fixture
def mock_llm_service():
    """Mock LLM service that returns canned responses."""
    service = AsyncMock()
    service.generate = AsyncMock(return_value="Mock LLM response content")
    service.generate_structured = AsyncMock()
    service.stream = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def tmp_db(tmp_path):
    """Temporary database path for testing."""
    return str(tmp_path / "test_valura.db")
