"""MiroThinker - API Endpoint Tests"""

import pytest


class TestHealthEndpoint:
    """Test /api/health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check returns status."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "dashscope_configured" in data
        assert "search_available" in data
        assert "scrape_available" in data


class TestRootEndpoint:
    """Test / endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_frontend_or_message(self, client):
        """Test root endpoint returns either frontend or API message."""
        response = await client.get("/")
        assert response.status_code == 200
        # Either returns HTML or JSON message
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type or "application/json" in content_type


class TestResearchEndpoint:
    """Test /api/research endpoint."""

    @pytest.mark.asyncio
    async def test_create_research_task(self, client, sample_research_request):
        """Test creating a research task returns task_id."""
        response = await client.post("/api/research", json=sample_research_request)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["task_id"] is not None

    @pytest.mark.asyncio
    async def test_create_research_task_invalid_query(self, client):
        """Test creating task with empty query fails."""
        response = await client.post("/api/research", json={"query": ""})
        # FastAPI validation should reject empty query
        assert response.status_code in [422, 400]

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, client):
        """Test getting a non-existent task returns 404."""
        response = await client.get("/api/research/nonexistent-id")
        assert response.status_code == 404


class TestSystemStatus:
    """Test /api/status endpoint."""

    @pytest.mark.asyncio
    async def test_system_status(self, client):
        """Test system status returns service info."""
        response = await client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "concurrency" in data
        assert "tasks" in data
