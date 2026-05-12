"""
置信度机制测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from backend.src.understanding import (
    get_content_analyzer,
    get_confidence_evaluator,
    get_review_manager,
)


class TestConfidenceSystem:
    """置信度系统测试"""

    @pytest.fixture
    def analyzer(self):
        """获取内容分析器"""
        return get_content_analyzer()

    @pytest.fixture
    def evaluator(self):
        """获取置信度评估器"""
        return get_confidence_evaluator()

    @pytest.fixture
    def review_mgr(self):
        """获取审核管理器"""
        return get_review_manager()

    @pytest.mark.asyncio
    async def test_high_confidence_content(self, analyzer, evaluator):
        """测试高置信度内容 - 结构清晰"""
        content = "今天学习了 Python 异步编程，主要包括 asyncio、await、async def 等概念。学会了使用 aiohttp 进行异步 HTTP 请求。"

        result = await analyzer.analyze(content)
        confidence_score = evaluator.calculate_confidence(content, result)
        level = evaluator.classify_confidence(confidence_score)

        assert confidence_score >= 85, f"高置信度内容应 >= 85，实际: {confidence_score}"
        assert level.value == "high"

    @pytest.mark.asyncio
    async def test_medium_confidence_content(self, analyzer, evaluator):
        """测试中置信度内容"""
        content = "需要买些东西"

        result = await analyzer.analyze(content)
        confidence_score = evaluator.calculate_confidence(content, result)
        level = evaluator.classify_confidence(confidence_score)

        assert 60 <= confidence_score < 85, f"中置信度内容应在 60-85 之间，实际: {confidence_score}"

    @pytest.mark.asyncio
    async def test_low_confidence_content(self, analyzer, evaluator):
        """测试低置信度内容 - 内容模糊"""
        content = "好的"

        result = await analyzer.analyze(content)
        confidence_score = evaluator.calculate_confidence(content, result)
        level = evaluator.classify_confidence(confidence_score)

        assert confidence_score < 60, f"低置信度内容应 < 60，实际: {confidence_score}"
        assert level.value == "low"

    def test_confidence_classification(self, evaluator):
        """测试置信度分类"""
        assert evaluator.classify_confidence(90).value == "high"
        assert evaluator.classify_confidence(75).value == "medium"
        assert evaluator.classify_confidence(40).value == "low"

    @pytest.mark.asyncio
    async def test_review_manager_stats(self, review_mgr):
        """测试审核统计"""
        stats = await review_mgr.get_review_stats()
        assert isinstance(stats, dict)

    def test_evaluator_stats(self, evaluator):
        """测试评估器统计"""
        conf_stats = evaluator.get_stats()
        assert isinstance(conf_stats, dict)
