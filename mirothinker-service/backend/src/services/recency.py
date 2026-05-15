"""
MiroThinker - Recency Scoring
Zero-cost solution for time-aware recency scoring.
Extends the existing date extraction logic in quality.py.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


class RecencyScorer:
    """
    Time-aware recency scoring with configurable time windows.

    Scoring rules:
    - Within 90 days: 1.0 (Excellent)
    - Within 1 year: 0.7 (Good)
    - Within 3 years: 0.4 (Fair)
    - Over 3 years: 0.2 (Poor)

    For partial dates, confidence factor adjusts the effective score.
    """

    # Time windows in days
    WINDOW_90_DAYS = 90
    WINDOW_1_YEAR = 365
    WINDOW_3_YEARS = 365 * 3

    # Base scores
    SCORE_EXCELLENT = 1.0
    SCORE_GOOD = 0.7
    SCORE_FAIR = 0.4
    SCORE_POOR = 0.2
    SCORE_UNKNOWN = 0.3

    def __init__(self):
        """Initialize with default scoring thresholds."""
        pass

    def score(self, date: Optional[str] = None, date_confidence: float = 1.0) -> dict:
        """
        Calculate recency score for a given date.

        Args:
            date: ISO format date string (e.g., "2024-01-15")
            date_confidence: Confidence of date accuracy (0.0-1.0)

        Returns:
            dict with score, level, days_old, confidence_factor, description
        """
        if not date:
            return {
                "score": self.SCORE_UNKNOWN,
                "level": "Unknown",
                "days_old": None,
                "confidence_factor": 0.0,
                "description": "No date available"
            }

        try:
            parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            days_old = (datetime.now() - parsed_date.replace(tzinfo=None)).days

            # Calculate base score based on age
            if days_old <= self.WINDOW_90_DAYS:
                base_score = self.SCORE_EXCELLENT
                level = "Excellent"
            elif days_old <= self.WINDOW_1_YEAR:
                base_score = self.SCORE_GOOD
                level = "Good"
            elif days_old <= self.WINDOW_3_YEARS:
                base_score = self.SCORE_FAIR
                level = "Fair"
            else:
                base_score = self.SCORE_POOR
                level = "Poor"

            # Adjust by confidence factor (0.7 to 1.0)
            # If confidence is 0.5 (year-only), reduce score by 30%
            confidence_factor = 0.7 + (date_confidence * 0.3)
            effective_score = base_score * confidence_factor

            return {
                "score": round(effective_score, 3),
                "level": level,
                "days_old": days_old,
                "confidence_factor": round(confidence_factor, 2),
                "description": self._get_description(level, days_old)
            }

        except (ValueError, TypeError):
            return {
                "score": self.SCORE_UNKNOWN,
                "level": "Invalid",
                "days_old": None,
                "confidence_factor": 0.0,
                "description": f"Invalid date format: {date}"
            }

    def score_search_result(self, result: dict) -> dict:
        """
        Score a search result's recency based on metadata.

        Args:
            result: Search result dict with optional 'date' and 'date_confidence'

        Returns:
            Recency score dict
        """
        date = result.get("date") or result.get("extracted_date")
        confidence = result.get("date_confidence", 1.0)

        score_result = self.score(date, confidence)

        # Add data currency warning if needed
        warning = None
        if score_result["days_old"] and score_result["days_old"] > self.WINDOW_2_YEARS:
            warning = f"数据截至 {self.format_date_relative(result.get('date'))}"

        return {
            **score_result,
            "warning": warning,
            "currency_label": self.get_currency_label(score_result["days_old"])
        }

    def get_currency_label(self, days_old: Optional[int]) -> str:
        """
        Get human-readable currency label.

        Args:
            days_old: Number of days since publication

        Returns:
            Currency label string
        """
        if days_old is None:
            return "📅 日期未知"

        if days_old <= self.WINDOW_90_DAYS:
            return "🟢 最新"
        elif days_old <= self.WINDOW_1_YEAR:
            return "🟡 近期"
        elif days_old <= self.WINDOW_3_YEARS:
            return "🟠 较早"
        else:
            return "🔴 过时"

    def format_date_relative(self, date_str: Optional[str]) -> str:
        """
        Format date as relative string (e.g., "3个月前").

        Args:
            date_str: ISO format date string

        Returns:
            Relative date string
        """
        if not date_str:
            return "未知时间"

        try:
            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            parsed = parsed.replace(tzinfo=None)
            days_old = (datetime.now() - parsed).days

            if days_old == 0:
                return "今天"
            elif days_old == 1:
                return "昨天"
            elif days_old < 30:
                return f"{days_old}天前"
            elif days_old < 365:
                months = days_old // 30
                return f"{months}个月前"
            else:
                years = days_old // 365
                return f"{years}年前"

        except (ValueError, TypeError):
            return date_str if date_str else "未知"

    def _get_description(self, level: str, days_old: int) -> str:
        """Get description for score level."""
        descriptions = {
            "Excellent": f"数据新鲜 ({days_old}天前)",
            "Good": f"数据较新 ({days_old}天前)",
            "Fair": f"数据较旧 ({days_old}天前)",
            "Poor": f"数据可能过时 ({days_old}天前)",
            "Unknown": "缺少日期信息",
            "Invalid": "日期格式无效"
        }
        return descriptions.get(level, "")

    @staticmethod
    def extract_date_from_text(text: str) -> Tuple[Optional[str], float]:
        """
        Extract date from text content with confidence.

        Args:
            text: Text containing potential date

        Returns:
            Tuple of (extracted_date, confidence)
            confidence: 1.0 = full date, 0.5 = year only, 0.3 = uncertain
        """
        # Try ISO format first
        iso_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(iso_pattern, text)
        if match:
            return match.group(1), 1.0

        # Try year-month
        ym_pattern = r'(\d{4}-\d{2})'
        match = re.search(ym_pattern, text)
        if match:
            return match.group(1), 0.7

        # Try year only
        year_pattern = r'\b(20[12]\d)\b'
        match = re.search(year_pattern, text)
        if match:
            return match.group(1), 0.5

        return None, 0.3


class DataCurrencyFormatter:
    """
    Format data currency warnings for research outputs.
    """

    @staticmethod
    def format_currency_notice(sources: list[dict], recency_scorer: RecencyScorer = None) -> str:
        """
        Generate a data currency notice for research results.

        Args:
            sources: List of sources with dates
            recency_scorer: Optional RecencyScorer instance

        Returns:
            Markdown formatted currency notice
        """
        if not recency_scorer:
            recency_scorer = RecencyScorer()

        if not sources:
            return "⚠️ 数据来源日期未知，请注意核实时效性"

        # Score all sources
        scores = []
        oldest_date = None
        oldest_days = 0

        for source in sources:
            date = source.get("date") or source.get("extracted_date")
            if date:
                result = recency_scorer.score(date)
                scores.append(result)

                if result["days_old"] and (oldest_date is None or result["days_old"] > oldest_days):
                    oldest_date = date
                    oldest_days = result["days_old"]

        # Generate notice
        avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0

        if avg_score >= 0.8:
            freshness = "🟢 数据新鲜"
        elif avg_score >= 0.5:
            freshness = "🟡 数据较新"
        else:
            freshness = "🔴 数据较旧"

        notice = f"**数据时效性**: {freshness}\n\n"

        if oldest_date:
            notice += f"- 最早来源: {recency_scorer.format_date_relative(oldest_date)}\n"
            notice += f"- 数据截至: {oldest_date}\n"

        if avg_score < 0.5:
            notice += "\n⚠️ **建议**: 部分数据可能已过时，请交叉验证\n"

        return notice


# Example usage
if __name__ == "__main__":
    scorer = RecencyScorer()

    test_dates = [
        "2026-05-01",   # Recent
        "2026-01-01",   # ~4 months ago
        "2025-06-01",   # ~1 year ago
        "2024-01-01",   # ~2 years ago
        "2022-01-01",   # ~4 years ago
        None,           # No date
    ]

    print("=== Recency Scoring Tests ===\n")

    for date in test_dates:
        result = scorer.score(date, date_confidence=1.0)
        label = scorer.get_currency_label(result["days_old"])
        print(f"Date: {date or 'None'}")
        print(f"  Score: {result['score']} ({result['level']})")
        print(f"  Label: {label}")
        print(f"  Description: {result['description']}")
        print()

    # Test currency formatter
    print("\n=== Currency Formatter ===\n")
    sources = [
        {"date": "2026-04-15", "url": "https://example1.com"},
        {"date": "2025-08-20", "url": "https://example2.com"},
        {"date": "2024-03-10", "url": "https://example3.com"},
    ]
    notice = DataCurrencyFormatter.format_currency_notice(sources)
    print(notice)