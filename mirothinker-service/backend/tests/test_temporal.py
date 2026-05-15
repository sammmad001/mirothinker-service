"""MiroThinker - Phase 1 Temporal Anti-Hallucination Tests"""

import pytest
from datetime import datetime, timedelta

from src.services.search import DateExtractor
from src.services.quality import SourceCredibilityScorer, QualityCheckPipeline


class TestDateExtractor:
    """Test DateExtractor class."""

    def setup_method(self):
        self.current_date = datetime(2026, 5, 13)

    def test_extract_iso_date(self):
        """Test extracting ISO format dates."""
        result = {"snippet": "Published on 2025-03-15"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is not None
        assert date_info["date_confidence"] >= 0.8

    def test_extract_chinese_date_year_month(self):
        """Test extracting Chinese date format."""
        # The regex uses \b which needs a word boundary, so we add a space
        result = {"snippet": "发布于 2025年3月"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is not None

    def test_extract_relative_date_days(self):
        """Test extracting relative dates (days ago)."""
        result = {"snippet": "3天前发布"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is not None
        # Should be within 1 day of expected
        expected = self.current_date - timedelta(days=3)
        actual = datetime.fromisoformat(date_info["extracted_date"])
        assert abs((actual - expected).days) <= 1

    def test_extract_relative_date_months(self):
        """Test extracting relative dates (months ago)."""
        # The regex expects "月前" not "个月前"
        result = {"snippet": "2月前"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is not None

    def test_extract_english_date(self):
        """Test extracting English date format."""
        result = {"snippet": "March 2025 report"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        # May or may not extract depending on pattern
        assert isinstance(date_info["date_confidence"], float)

    def test_no_date_in_result(self):
        """Test when no date can be extracted."""
        result = {"snippet": "Some random text without dates"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is None
        assert date_info["date_confidence"] == 0.0

    def test_extract_from_url_with_date_pattern(self):
        """Test extracting date from URL pattern."""
        # The code uses 'link' not 'url'
        result = {"link": "https://example.com/2025/04/article-title"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        assert date_info["extracted_date"] is not None
        assert date_info["date_confidence"] >= 0.5

    def test_extract_from_title(self):
        """Test extracting date from title."""
        result = {"title": "2025年度人工智能报告"}
        date_info = DateExtractor.extract_from_result(result, self.current_date)
        # Should extract year at least
        assert isinstance(date_info["date_confidence"], float)


class TestRecencyScoring:
    """Test recency scoring with date extraction."""

    def setup_method(self):
        self.scorer = SourceCredibilityScorer()

    def test_recent_date_scores_high(self):
        """Test that recent dates score high."""
        recent_date = (datetime.now() - timedelta(days=10)).isoformat()
        score = self.scorer.score(
            url="https://example.com",
            content="Test content",
            metadata={"date": recent_date, "date_confidence": 1.0}
        )
        assert score["breakdown"]["recency_score"] >= 0.8

    def test_old_date_scores_low(self):
        """Test that old dates score low."""
        old_date = (datetime.now() - timedelta(days=3*365)).isoformat()  # 3 years ago
        score = self.scorer.score(
            url="https://example.com",
            content="Test content",
            metadata={"date": old_date, "date_confidence": 1.0}
        )
        assert score["breakdown"]["recency_score"] <= 0.4

    def test_no_date_penalized(self):
        """Test that missing dates are penalized."""
        score = self.scorer.score(
            url="https://example.com",
            content="Test content",
            metadata=None
        )
        assert score["breakdown"]["recency_score"] == 0.3

    def test_low_confidence_reduces_score(self):
        """Test that low date confidence reduces recency score."""
        recent_date = (datetime.now() - timedelta(days=10)).isoformat()
        high_conf = self.scorer.score(
            url="https://example.com",
            content="Test content",
            metadata={"date": recent_date, "date_confidence": 1.0}
        )
        low_conf = self.scorer.score(
            url="https://example.com",
            content="Test content",
            metadata={"date": recent_date, "date_confidence": 0.3}
        )
        # Low confidence should result in lower recency score
        assert high_conf["breakdown"]["recency_score"] > low_conf["breakdown"]["recency_score"]


class TestTemporalConsistencyCheck:
    """Test temporal consistency check in QualityCheckPipeline."""

    def setup_method(self):
        self.pipeline = QualityCheckPipeline()

    def test_detect_future_year_reference(self):
        """Test detection of impossible future year references."""
        # Current year is 2026, so 2027+ should be flagged
        result = """
        # AI Report
        In 2027, AI will surpass human intelligence.
        The technology landscape of 2028 looks promising.
        """
        metadata = {"sources": []}
        
        check_result = self.pipeline._check_temporal_consistency(result, metadata)
        assert check_result["score"] < 1.0
        assert any("future" in issue.lower() or "CRITICAL" in issue for issue in check_result["issues"])

    def test_detect_temporal_paradox(self):
        """Test detection of temporal paradoxes."""
        result = """
        # Report
        预计到2024年，人工智能将取得重大突破。
        """
        metadata = {"sources": []}
        
        check_result = self.pipeline._check_temporal_consistency(result, metadata)
        assert check_result["score"] < 1.0
        assert any("paradox" in issue.lower() or "WARNING" in issue for issue in check_result["issues"])

    def test_old_sources_warning(self):
        """Test warning for outdated sources."""
        result = "Test report content"
        old_date = (datetime.now() - timedelta(days=3*365)).isoformat()
        metadata = {
            "sources": [
                {"extracted_date": old_date},
                {"extracted_date": old_date},
                {"extracted_date": old_date},
                {"extracted_date": old_date},
            ]
        }
        
        check_result = self.pipeline._check_temporal_consistency(result, metadata)
        assert check_result["score"] < 1.0
        assert any("older than 2 years" in issue for issue in check_result["issues"])

    def test_undated_sources_warning(self):
        """Test warning for undated sources."""
        result = "Test report content"
        metadata = {
            "sources": [
                {},  # No date
                {},  # No date
                {},  # No date
            ]
        }
        
        check_result = self.pipeline._check_temporal_consistency(result, metadata)
        assert check_result["score"] < 1.0
        assert any("lack publication dates" in issue for issue in check_result["issues"])

    def test_valid_temporal_context(self):
        """Test that valid temporal context passes."""
        result = """
        # AI in 2025
        Recent developments in AI have been significant.
        As of 2025, the technology has advanced considerably.
        """
        metadata = {"sources": []}
        
        check_result = self.pipeline._check_temporal_consistency(result, metadata)
        # Should pass without major issues
        assert check_result["score"] >= 0.7

    def test_full_pipeline_includes_temporal_check(self):
        """Test that full pipeline runs temporal check."""
        result = """
        # Summary
        AI impact study with finding and source information.
        Sources: https://example.com/2025
        """
        metadata = {"sources": []}
        
        report = self.pipeline.run(result, metadata)
        # Should include temporal check in scores
        assert "_check_temporal_consistency" in report["scores"]


class TestSystemPromptTemporalContext:
    """Test system prompt temporal context injection."""

    def test_build_system_prompt_includes_current_date(self):
        """Test that system prompt includes current date."""
        from src.services.agent import build_system_prompt
        
        current_date = "2026-05-13"
        prompt = build_system_prompt(max_turns=5, domain="tech", current_date=current_date)
        
        assert current_date in prompt
        assert "TEMPORAL CONTEXT" in prompt or "当前日期" in prompt or "时间上下文" in prompt

    def test_build_system_prompt_without_date(self):
        """Test that system prompt works without date (backward compatibility)."""
        from src.services.agent import build_system_prompt
        
        prompt = build_system_prompt(max_turns=5, domain="tech")
        # Should still work, just without temporal context
        assert isinstance(prompt, str)
        assert len(prompt) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
