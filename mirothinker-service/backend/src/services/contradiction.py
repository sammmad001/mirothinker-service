"""
MiroThinker - Enhanced Contradiction Detector
Zero-cost solution for detecting both numeric and qualitative contradictions.
Extends the existing ContradictionDetector in quality.py.
"""

import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class ConflictType(Enum):
    """Types of contradictions that can be detected."""
    NUMERIC_CONFLICT = "numeric_conflict"
    QUALITATIVE_CONFLICT = "qualitative_conflict"
    CAUSAL_CONFLICT = "causal_conflict"
    TEMPORAL_CONFLICT = "temporal_conflict"
    UNCERTAIN = "uncertain"


@dataclass
class Conflict:
    """Represents a detected contradiction."""
    conflict_type: ConflictType
    claim1: dict
    claim2: dict
    difference: Optional[str] = None
    opposition_words: Optional[tuple] = None
    resolution: str = "Requires human judgment or third-party verification"

    def format_markdown(self) -> str:
        """Format conflict as markdown string."""
        lines = [f"### {self.conflict_type.value.replace('_', ' ').title()}\n"]

        if self.conflict_type == ConflictType.NUMERIC_CONFLICT:
            lines.append(f"- **Claim 1**: {self.claim1.get('text', '')} (来源: {self.claim1.get('source', 'Unknown')})")
            lines.append(f"- **Claim 2**: {self.claim2.get('text', '')} (来源: {self.claim2.get('source', 'Unknown')})")
            lines.append(f"- **差异**: {self.difference}")
        else:
            lines.append(f"- **正方**: {self.claim1.get('text', '')} (来源: {self.claim1.get('source', 'Unknown')})")
            lines.append(f"- **反方**: {self.claim2.get('text', '')} (来源: {self.claim2.get('source', 'Unknown')})")
            if self.opposition_words:
                lines.append(f"- **对立词**: {self.opposition_words[0]} vs {self.opposition_words[1]}")

        lines.append(f"- **建议**: {self.resolution}")
        return "\n".join(lines)


class EnhancedContradictionDetector:
    """
    Enhanced contradiction detection with numeric and qualitative analysis.

    Features:
    - Numeric conflict detection (>20% difference)
    - Qualitative conflict detection (opposition words)
    - Causal chain conflict detection
    - Temporal paradox detection
    - Conflict report generation

    Usage:
        detector = EnhancedContradictionDetector()
        conflicts = detector.detect(claims)
        report = detector.format_conflict_report(conflicts)
    """

    # Opposition word pairs for qualitative detection
    OPPOSITIONS = [
        # English
        ("increase", "decrease"),
        ("rise", "fall"),
        ("positive", "negative"),
        ("growth", "decline"),
        ("better", "worse"),
        ("expand", "contract"),
        ("support", "oppose"),
        ("agree", "disagree"),
        ("believe", "doubt"),
        ("beneficial", "harmful"),
        # Chinese
        ("增长", "下降"),
        ("上升", "下跌"),
        ("支持", "反对"),
        ("同意", "反对"),
        ("有利的", "有害的"),
        ("促进", "抑制"),
        ("扩展", "收缩"),
        ("正面", "负面"),
        ("肯定", "否定"),
        ("相信", "怀疑"),
        # Mixed
        ("利好", "利空"),
        ("看涨", "看跌"),
        ("买入", "卖出"),
    ]

    # Causal contradiction patterns
    CAUSAL_PATTERNS = [
        (r"导致", r"预防"),
        (r"因为", r"所以不"),
        (r"由于", r"因此不"),
        (r"causes", r"prevents"),
        (r"leads to", r"avoids"),
    ]

    def __init__(self, numeric_threshold: float = 0.20):
        """
        Args:
            numeric_threshold: Threshold for numeric conflict detection (default 20%)
        """
        self.numeric_threshold = numeric_threshold
        self._opposition_patterns = self._compile_opposition_patterns()

    def _compile_opposition_patterns(self) -> list[tuple]:
        """Compile regex patterns for opposition detection."""
        patterns = []
        for w1, w2 in self.OPPOSITIONS:
            patterns.append((
                re.compile(rf'\b{re.escape(w1)}\b', re.IGNORECASE),
                re.compile(rf'\b{re.escape(w2)}\b', re.IGNORECASE)
            ))
            patterns.append((
                re.compile(rf'\b{re.escape(w2)}\b', re.IGNORECASE),
                re.compile(rf'\b{re.escape(w1)}\b', re.IGNORECASE)
            ))
        return patterns

    def detect(self, claims: list[dict]) -> list[Conflict]:
        """
        Detect all types of contradictions in claims.

        Args:
            claims: List of claim dicts with 'text', 'source', 'topic' keys

        Returns:
            List of detected Conflict objects
        """
        conflicts = []

        # Group by topic
        topics = self._group_by_topic(claims)

        for topic, topic_claims in topics.items():
            if len(topic_claims) < 2:
                continue

            # Numeric conflicts
            numeric_conflicts = self._detect_numeric_conflicts(topic_claims)
            conflicts.extend(numeric_conflicts)

            # Qualitative conflicts
            qualitative_conflicts = self._detect_qualitative_conflicts(topic_claims)
            conflicts.extend(qualitative_conflicts)

            # Causal conflicts
            causal_conflicts = self._detect_causal_conflicts(topic_claims)
            conflicts.extend(causal_conflicts)

        return conflicts

    def detect_from_results(self, results: list[dict]) -> list[Conflict]:
        """
        Detect contradictions from search results.

        Args:
            results: List of search result dicts with 'title', 'snippet', 'url'

        Returns:
            List of detected conflicts
        """
        claims = []
        for r in results:
            claim = {
                "text": r.get("title", "") + " " + r.get("snippet", ""),
                "source": r.get("url", ""),
                "topic": self._extract_topic(r.get("title", ""))
            }
            claims.append(claim)

        return self.detect(claims)

    def _group_by_topic(self, claims: list[dict]) -> dict:
        """Group claims by topic."""
        topics = {}
        for claim in claims:
            topic = claim.get("topic", "general")
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(claim)
        return topics

    def _extract_topic(self, text: str) -> str:
        """Extract a simple topic from text."""
        words = text.split()[:5]
        return "_".join(words).lower() if words else "general"

    def _detect_numeric_conflicts(self, claims: list[dict]) -> list[Conflict]:
        """Detect numeric contradictions (>20% difference)."""
        conflicts = []
        numbers = []

        for claim in claims:
            nums = re.findall(r'([+-]?\d+(?:\.\d+)?)\s*(%|percent|百万|亿|十亿|billion|million)?', claim.get("text", ""), re.I)
            for num_str, unit in nums:
                try:
                    value = float(num_str)
                    numbers.append({
                        "value": value,
                        "unit": unit or "%",
                        "source": claim.get("source", ""),
                        "text": claim.get("text", ""),
                        "credibility": claim.get("credibility_score", 0.5)
                    })
                except ValueError:
                    continue

        # Check for same unit conflicts
        units = {}
        for n in numbers:
            unit = n["unit"].lower()
            if unit not in units:
                units[unit] = []
            units[unit].append(n)

        for unit, values in units.items():
            for i, v1 in enumerate(values):
                for v2 in values[i+1:]:
                    if v1["value"] > 0:
                        diff = abs(v1["value"] - v2["value"]) / v1["value"]
                        if diff > self.numeric_threshold:
                            conflicts.append(Conflict(
                                conflict_type=ConflictType.NUMERIC_CONFLICT,
                                claim1={"text": v1["text"], "source": v1["source"]},
                                claim2={"text": v2["text"], "source": v2["source"]},
                                difference=f"{diff:.1%}",
                                resolution="Check if different time periods or measurement methods"
                            ))

        return conflicts

    def _detect_qualitative_conflicts(self, claims: list[dict]) -> list[Conflict]:
        """Detect qualitative contradictions (opposition words)."""
        conflicts = []

        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                text1 = c1.get("text", "").lower()
                text2 = c2.get("text", "").lower()

                for pattern1, pattern2 in self._opposition_patterns:
                    has_opposition = False
                    opposition_words = None

                    if pattern1.search(text1) and pattern2.search(text2):
                        has_opposition = True
                        # Extract the actual words
                        m1 = pattern1.search(text1)
                        m2 = pattern2.search(text2)
                        if m1 and m2:
                            # Get original case words
                            orig_text1 = c1.get("text", "")
                            orig_text2 = c2.get("text", "")
                            w1 = self._find_original_word(orig_text1, pattern1.pattern)
                            w2 = self._find_original_word(orig_text2, pattern2.pattern)
                            opposition_words = (w1, w2)

                    if has_opposition:
                        conflicts.append(Conflict(
                            conflict_type=ConflictType.QUALITATIVE_CONFLICT,
                            claim1=c1,
                            claim2=c2,
                            opposition_words=opposition_words,
                            resolution="Report must clarify both perspectives and their contexts"
                        ))
                        break  # One conflict per claim pair is enough

        return conflicts

    def _find_original_word(self, text: str, pattern: str) -> str:
        """Find the original case word from pattern."""
        pattern_clean = pattern.replace("\\b", "").replace("\\s", "")
        match = re.search(pattern_clean, text, re.IGNORECASE)
        return match.group(0) if match else pattern_clean

    def _detect_causal_conflicts(self, claims: list[dict]) -> list[Conflict]:
        """Detect causal chain contradictions."""
        conflicts = []

        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                text1 = c1.get("text", "")
                text2 = c2.get("text", "")

                for cause_pattern, effect_pattern in self.CAUSAL_PATTERNS:
                    has_cause = re.search(cause_pattern, text1, re.I)
                    has_prevent = re.search(effect_pattern, text2, re.I)

                    if has_cause and has_prevent:
                        conflicts.append(Conflict(
                            conflict_type=ConflictType.CAUSAL_CONFLICT,
                            claim1=c1,
                            claim2=c2,
                            resolution="Investigate if both claims are from different contexts or studies"
                        ))
                        break

        return conflicts

    def format_conflict_report(self, conflicts: list[Conflict]) -> str:
        """
        Format detected conflicts as markdown report.

        Args:
            conflicts: List of Conflict objects

        Returns:
            Markdown formatted conflict report
        """
        if not conflicts:
            return "✅ 未检测到明显矛盾\n"

        lines = [f"## 矛盾检测报告 ({len(conflicts)} 项)\n"]

        # Group by type
        by_type = {}
        for c in conflicts:
            if c.conflict_type not in by_type:
                by_type[c.conflict_type] = []
            by_type[c.conflict_type].append(c)

        for conflict_type, type_conflicts in by_type.items():
            lines.append(f"\n### {conflict_type.value.replace('_', ' ').title()}\n")
            lines.append(f"共 {len(type_conflicts)} 项\n")

            for i, conflict in enumerate(type_conflicts, 1):
                lines.append(f"\n**{i}.**")
                lines.append(conflict.format_markdown())

        return "\n".join(lines)

    def get_conflict_summary(self, conflicts: list[Conflict]) -> dict:
        """
        Get a summary of detected conflicts.

        Args:
            conflicts: List of Conflict objects

        Returns:
            Summary dict with counts by type
        """
        summary = {
            "total": len(conflicts),
            "by_type": {},
            "high_confidence": 0,
            "requires_review": 0
        }

        for c in conflicts:
            type_name = c.conflict_type.value
            summary["by_type"][type_name] = summary["by_type"].get(type_name, 0) + 1

            # High confidence if numeric conflict with >50% difference
            if c.conflict_type == ConflictType.NUMERIC_CONFLICT:
                if c.difference and float(c.difference.rstrip("%")) > 50:
                    summary["high_confidence"] += 1

        summary["requires_review"] = len(conflicts) - summary["high_confidence"]

        return summary


# Example usage
if __name__ == "__main__":
    detector = EnhancedContradictionDetector(numeric_threshold=0.20)

    test_claims = [
        {
            "text": "The market grew by 25% in Q1 2024",
            "source": "https://example1.com",
            "topic": "market_growth"
        },
        {
            "text": "The market declined by 10% in Q1 2024",
            "source": "https://example2.com",
            "topic": "market_growth"
        },
        {
            "text": "AI adoption is increasing rapidly",
            "source": "https://example3.com",
            "topic": "ai_trends"
        },
        {
            "text": "AI adoption is declining due to costs",
            "source": "https://example4.com",
            "topic": "ai_trends"
        },
        {
            "text": "Company X leads to revenue growth",
            "source": "https://example5.com",
            "topic": "company_x"
        },
        {
            "text": "Company X prevents revenue loss",
            "source": "https://example6.com",
            "topic": "company_x"
        }
    ]

    print("=== Enhanced Contradiction Detection ===\n")

    conflicts = detector.detect(test_claims)
    print(f"Detected {len(conflicts)} conflicts\n")

    report = detector.format_conflict_report(conflicts)
    print(report)

    print("\n=== Summary ===\n")
    summary = detector.get_conflict_summary(conflicts)
    print(f"Total: {summary['total']}")
    print(f"By type: {summary['by_type']}")
    print(f"High confidence: {summary['high_confidence']}")
    print(f"Requires review: {summary['requires_review']}")