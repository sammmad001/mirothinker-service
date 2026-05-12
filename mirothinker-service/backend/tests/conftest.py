"""MiroThinker - Test Configuration"""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_research_request():
    """Sample research request for testing."""
    return {
        "query": "What is Python programming language?",
        "max_turns": 5,
        "context_keep": 3,
        "model": "qwen-flash",
        "temperature": 0.5,
    }
