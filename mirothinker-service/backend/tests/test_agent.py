"""MiroThinker - Agent Service Tests"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.agent import (
    AgentState,
    ResearchAgent,
    build_system_prompt,
    detect_domain,
    classify_query,
)


class TestAgentState:
    """Test AgentState class."""

    def test_init_creates_system_message(self):
        """Test that AgentState initializes with system prompt."""
        state = AgentState(
            system_prompt="Test system prompt",
            model="qwen-plus",
            temperature=0.7
        )
        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "system"
        assert state.messages[0]["content"] == "Test system prompt"
        assert state.model == "qwen-plus"
        assert state.temperature == 0.7
        assert state.turn_count == 0

    def test_add_message_appends_correctly(self):
        """Test adding messages to state."""
        state = AgentState("prompt", "qwen-plus", 0.7)
        state.add_message("user", "Hello")
        assert len(state.messages) == 2
        assert state.messages[1]["role"] == "user"
        assert state.messages[1]["content"] == "Hello"

    def test_add_message_tool_creates_summary(self):
        """Test that tool messages create summaries."""
        state = AgentState("prompt", "qwen-plus", 0.7)
        long_content = "A" * 200
        state.add_message("tool", long_content)
        assert len(state.tool_summaries) == 1
        assert len(state.tool_summaries[0]) <= 100

    def test_get_context_window_keeps_system_prompt(self):
        """Test context window always includes system prompt."""
        state = AgentState("system", "qwen-plus", 0.7)
        state.add_message("user", "query")
        state.add_message("assistant", "response")

        context = state.get_context_window(context_keep=5)
        assert context[0]["role"] == "system"


class TestBuildSystemPrompt:
    """Test build_system_prompt function."""

    def test_basic_prompt_contains_tools(self):
        """Test that basic prompt includes tool definitions."""
        prompt = build_system_prompt(max_turns=10, domain="general")
        assert "google_search" in prompt
        assert "scrape_webpage" in prompt
        assert "FINAL ANSWER:" in prompt
        assert "Max 10 turns" in prompt

    def test_tech_domain_extra(self):
        """Test tech domain includes specific instructions."""
        prompt = build_system_prompt(max_turns=10, domain="tech")
        assert "code examples" in prompt.lower()

    def test_finance_domain_extra(self):
        """Test finance domain includes specific instructions."""
        prompt = build_system_prompt(max_turns=10, domain="finance")
        assert "data with dates" in prompt.lower()

    def test_health_domain_extra(self):
        """Test health domain includes peer-reviewed requirement."""
        prompt = build_system_prompt(max_turns=10, domain="health")
        assert "peer-reviewed" in prompt.lower()


class TestDetectDomain:
    """Test detect_domain function."""

    def test_detect_tech(self):
        """Test tech domain detection."""
        assert detect_domain("AI machine learning algorithm") == "tech"
        assert detect_domain("Python programming software") == "tech"
        assert detect_domain("人工智能技术") == "tech"

    def test_detect_finance(self):
        """Test finance domain detection."""
        assert detect_domain("stock market investment") == "finance"
        assert detect_domain("股票投资金融") == "finance"

    def test_detect_health(self):
        """Test health domain detection."""
        assert detect_domain("medical treatment disease") == "health"
        assert detect_domain("医疗健康疾病") == "health"

    def test_default_general(self):
        """Test that unknown queries default to general."""
        assert detect_domain("What is the weather today?") == "general"


class TestClassifyQuery:
    """Test classify_query function."""

    @pytest.mark.asyncio
    async def test_simple_factual_is_tier1(self):
        """Test simple factual queries classified as TIER_1."""
        # This test requires actual API call, so we mock it
        with patch('src.services.agent.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "TIER_1"}}]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await classify_query("What is 2+2?")
            assert result == "TIER_1"

    @pytest.mark.asyncio
    async def test_returns_tier2_on_error(self):
        """Test that API errors default to TIER_2."""
        with patch('src.services.agent.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API error")

            result = await classify_query("Some query")
            assert result == "TIER_2"


class TestResearchAgent:
    """Test ResearchAgent class."""

    def test_init_with_quality_enhancement(self):
        """Test agent initializes with quality modules."""
        agent = ResearchAgent(enable_quality_enhancement=True)
        assert agent.enable_quality is True
        assert agent.channel_search is not None
        assert agent.credibility_scorer is not None

    def test_init_without_quality_enhancement(self):
        """Test agent without quality modules."""
        agent = ResearchAgent(enable_quality_enhancement=False)
        assert agent.enable_quality is False
        assert agent.channel_search is None

    @pytest.mark.asyncio
    async def test_call_llm_returns_dict(self):
        """Test that call_llm returns a dict with content."""
        agent = ResearchAgent(enable_quality_enhancement=False)

        with patch('src.services.agent.httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response", "role": "assistant"}}]
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            result = await agent.call_llm(
                messages=[{"role": "user", "content": "test"}],
                model="qwen-flash",
                temperature=0.1,
            )

            assert isinstance(result, dict)
            assert result["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_call_llm_validates_response(self):
        """Test that call_llm validates response structure."""
        agent = ResearchAgent(enable_quality_enhancement=False)

        with patch('src.services.agent.httpx.AsyncClient') as mock_client:
            # Invalid response - missing choices
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalid": "response"}
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await agent.call_llm(
                    messages=[{"role": "user", "content": "test"}],
                    model="qwen-flash",
                    temperature=0.1,
                )

            assert "invalid response" in str(exc_info.value).lower()
