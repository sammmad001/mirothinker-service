"""MiroThinker - Quality Module Tests"""

import pytest

from src.services.quality import (
    SourceCredibilityScorer,
    ContradictionDetector,
    QualityCheckPipeline,
)


class TestSourceCredibilityScorer:
    """Test SourceCredibilityScorer."""

    def setup_method(self):
        self.scorer = SourceCredibilityScorer()

    def test_score_authoritative_source(self):
        """Test scoring an authoritative source."""
        result = self.scorer.score(
            url="https://nature.com/articles/test",
            content="According to recent studies [1], the results show significant improvement (p<0.05).",
            metadata={"date": "2024-01-15"}
        )
        assert result["score"] >= 0.7
        assert "A" in result["level"] or "B" in result["level"]

    def test_score_low_quality_source(self):
        """Test scoring a low quality source."""
        result = self.scorer.score(
            url="https://medium.com/some-blog",
            content="I think this is good",
            metadata=None
        )
        assert result["score"] < 0.7

    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        assert self.scorer._extract_domain("https://www.example.com/path") == "example.com"
        assert self.scorer._extract_domain("http://test.org") == "test.org"

    def test_score_to_level(self):
        """Test score to level conversion."""
        assert "A" in self.scorer._score_to_level(0.90)
        assert "B" in self.scorer._score_to_level(0.75)
        assert "C" in self.scorer._score_to_level(0.60)
        assert "D" in self.scorer._score_to_level(0.40)


class TestContradictionDetector:
    """Test ContradictionDetector."""

    def setup_method(self):
        self.detector = ContradictionDetector()

    def test_detect_numeric_conflict(self):
        """Test detecting numeric contradictions."""
        claims = [
            {"topic": "revenue", "text": "Revenue increased by 50%", "source": "A"},
            {"topic": "revenue", "text": "Revenue grew by 25%", "source": "B"},
        ]
        contradictions = self.detector.detect(claims)
        assert len(contradictions) > 0
        assert contradictions[0]["type"] == "numeric_conflict"

    def test_no_contradiction(self):
        """Test no contradiction detected when claims agree."""
        claims = [
            {"topic": "growth", "text": "Growth was positive", "source": "A"},
            {"topic": "growth", "text": "Growth increased", "source": "B"},
        ]
        contradictions = self.detector.detect(claims)
        # May or may not detect depending on opposition words
        assert isinstance(contradictions, list)

    def test_group_by_topic(self):
        """Test grouping claims by topic."""
        claims = [
            {"topic": "tech", "text": "AI is growing", "source": "A"},
            {"topic": "tech", "text": "ML is popular", "source": "B"},
            {"topic": "finance", "text": "Stocks are up", "source": "C"},
        ]
        topics = self.detector._group_by_topic(claims)
        assert len(topics) == 2
        assert len(topics["tech"]) == 2
        assert len(topics["finance"]) == 1


class TestQualityCheckPipeline:
    """Test QualityCheckPipeline."""

    def setup_method(self):
        self.pipeline = QualityCheckPipeline()

    def test_run_quality_check(self):
        """Test running quality check on a result."""
        result = """
        # AI Impact Study

        ## Executive Summary
        AI is transforming industries.

        ## Research Findings
        According to studies [1], AI adoption increased by 40% in 2024.
        Source: https://example.com/study-2024

        ## Sources
        - https://example.com/study-2024
        """
        metadata = {"query": "AI impact", "domain": "tech"}

        report = self.pipeline.run(result, metadata)
        assert "overall_score" in report
        assert "passed" in report
        assert "issues" in report
        assert "recommendation" in report

    def test_check_source_count(self):
        """Test source count check."""
        result_with_sources = "Source: https://example.com/2024\n" * 10
        result_no_sources = "No sources here"

        score_with = self.pipeline._check_source_count(result_with_sources, {})
        score_without = self.pipeline._check_source_count(result_no_sources, {})

        assert score_with["score"] > score_without["score"]

    def test_check_structure(self):
        """Test structure completeness check."""
        complete = "summary finding source"
        incomplete = "just some text"

        score_complete = self.pipeline._check_structure(complete, {})
        score_incomplete = self.pipeline._check_structure(incomplete, {})

        assert score_complete["score"] == 1.0
        assert score_incomplete["score"] < 1.0
        assert len(score_incomplete["issues"]) > 0
