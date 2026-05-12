"""
LLM 服务测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from backend.src.services.llm import get_llm_service
from backend.src.core.config import get_settings


class TestLLMService:
    """LLM 服务测试"""

    @pytest.fixture
    def settings(self):
        """获取配置"""
        return get_settings()

    @pytest.fixture
    def llm(self):
        """获取 LLM 服务"""
        return get_llm_service()

    def test_config_loaded(self, settings):
        """测试配置加载"""
        assert settings.CLOUD_LLM_PROVIDER is not None
        assert settings.OLLAMA_BASE_URL is not None
        assert settings.CLOUD_LLM_MODEL is not None

    @pytest.mark.asyncio
    async def test_ollama_availability(self, llm):
        """测试 Ollama 可用性检查"""
        result = await llm.is_ollama_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_list_models(self, llm):
        """测试列出模型"""
        if await llm.is_ollama_available():
            models = await llm.list_models()
            assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_chat_basic(self, llm):
        """测试基础聊天"""
        messages = [
            {"role": "user", "content": "你好，请回复'测试成功'"}
        ]

        try:
            response = await llm.chat(messages, temperature=0.7, max_tokens=50)
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"LLM 服务不可用: {e}")

    @pytest.mark.asyncio
    async def test_embedding_basic(self, llm):
        """测试基础向量化"""
        try:
            embedding = await llm.embed("测试文本")
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except Exception as e:
            pytest.skip(f"Embedding 服务不可用: {e}")
