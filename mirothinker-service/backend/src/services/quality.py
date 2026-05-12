"""
MiroThinker - Quality Enhancement Modules
Fixed channels, credibility scoring, contradiction detection, and quality checks.
"""

import re
from datetime import datetime


class FixedChannelSearch:
    """Fixed channel search engine with priority-based sources."""

    def __init__(self, tool_client):
        self.tools = tool_client

    async def search_with_channels(self, query: str, domain: str = None) -> list[dict]:
        """
        Search by priority channels:
        1. Core sources (L1)
        2. Extended sources (L2)
        3. General search fallback (L3)
        """
        from src.core.config import CORE_SOURCES

        results = []

        # Phase 1: Core sources
        for source_name, source_config in CORE_SOURCES.items():
            source_query = source_config["search_template"].format(query=query)
            source_results = await self.tools.google_search(source_query, num_results=5)
            results.extend([
                {**r, "source_tier": "L1", "source_name": source_config["name"], "source_category": source_name}
                for r in source_results
            ])

        # Fallback to general search if insufficient results
        if len(results) < 10:
            general_results = await self.tools.google_search(query, num_results=10)
            results.extend([
                {**r, "source_tier": "L3", "source_name": "Generic Search", "source_category": "general"}
                for r in general_results
            ])

        return results


class SourceCredibilityScorer:
    """Source credibility scoring engine."""

    def __init__(self):
        # Pre-defined source weights
        self.source_weights = {
            "nature.com": 0.95,
            "science.org": 0.95,
            "arxiv.org": 0.85,
            "reuters.com": 0.90,
            "apnews.com": 0.90,
            "bbc.com": 0.85,
            "github.com": 0.80,
            "wikipedia.org": 0.70,
            "stackoverflow.com": 0.75,
            "medium.com": 0.50,
            "zhihu.com": 0.45,
            "worldbank.org": 0.90,
            "imf.org": 0.90,
            "pubmed.ncbi.nlm.nih.gov": 0.95,
        }

    def score(self, url: str, content: str, metadata: dict = None) -> dict:
        """Comprehensive credibility scoring."""
        domain = self._extract_domain(url)

        # 1. Base weight
        base_weight = self.source_weights.get(domain, 0.50)

        # 2. Content quality score
        content_score = self._evaluate_content(content)

        # 3. Recency score
        recency_score = self._evaluate_recency(metadata)

        # 4. Citation integrity
        citation_score = self._evaluate_citations(content)

        # Weighted final score
        final_score = (
            base_weight * 0.4 +
            content_score * 0.3 +
            recency_score * 0.15 +
            citation_score * 0.15
        )

        return {
            "score": round(final_score, 3),
            "level": self._score_to_level(final_score),
            "breakdown": {
                "base_weight": round(base_weight, 3),
                "content_score": round(content_score, 3),
                "recency_score": round(recency_score, 3),
                "citation_score": round(citation_score, 3),
            }
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url

    def _evaluate_content(self, content: str) -> float:
        """Evaluate content quality."""
        score = 0.5

        # Has data support
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$', content))
        if has_data:
            score += 0.15

        # Has citations
        has_citations = bool(re.search(r'\[\d+\]|\(.*?et al\.|according to', content, re.I))
        if has_citations:
            score += 0.15

        # Appropriate length
        word_count = len(content.split())
        if 200 < word_count < 3000:
            score += 0.1

        # Has author/institution
        has_author = bool(re.search(r'by \w+|authored by|published by', content, re.I))
        if has_author:
            score += 0.1

        return min(score, 1.0)

    def _evaluate_recency(self, metadata: dict) -> float:
        """Evaluate recency."""
        if not metadata or "date" not in metadata:
            return 0.5

        try:
            date = datetime.fromisoformat(metadata["date"])
            days_old = (datetime.now() - date).days

            if days_old < 30:
                return 1.0
            elif days_old < 365:
                return 0.8
            elif days_old < 3 * 365:
                return 0.6
            else:
                return 0.3
        except:
            return 0.5

    def _evaluate_citations(self, content: str) -> float:
        """Evaluate citation integrity."""
        score = 0.5
        citation_count = len(re.findall(r'\[\d+\]|http[s]?://', content))

        if citation_count > 5:
            score += 0.3
        elif citation_count > 2:
            score += 0.15

        return min(score, 1.0)

    def _score_to_level(self, score: float) -> str:
        """Convert score to level."""
        if score >= 0.85:
            return "A (Authoritative)"
        elif score >= 0.70:
            return "B (Reliable)"
        elif score >= 0.50:
            return "C (Average)"
        else:
            return "D (Caution)"


class ContradictionDetector:
    """Detect contradictions across multiple claims."""

    def detect(self, claims: list[dict]) -> list[dict]:
        """Detect contradictions between claims."""
        contradictions = []

        # Group by topic
        topics = self._group_by_topic(claims)

        for topic, topic_claims in topics.items():
            if len(topic_claims) < 2:
                continue

            # Detect numeric contradictions
            numeric_conflicts = self._detect_numeric_conflicts(topic_claims)
            if numeric_conflicts:
                contradictions.append({
                    "topic": topic,
                    "type": "numeric_conflict",
                    "details": numeric_conflicts,
                    "resolution": "Requires human judgment or third-party verification"
                })

            # Detect qualitative contradictions
            qualitative_conflicts = self._detect_qualitative_conflicts(topic_claims)
            if qualitative_conflicts:
                contradictions.append({
                    "topic": topic,
                    "type": "qualitative_conflict",
                    "details": qualitative_conflicts,
                    "resolution": "Report must clarify both perspectives"
                })

        return contradictions

    def _group_by_topic(self, claims: list[dict]) -> dict:
        """Group claims by topic."""
        topics = {}
        for claim in claims:
            topic = claim.get("topic", "general")
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(claim)
        return topics

    def _detect_numeric_conflicts(self, claims: list[dict]) -> list[dict]:
        """Detect numeric contradictions."""
        conflicts = []
        numbers = []

        for claim in claims:
            nums = re.findall(r'(\d+(?:\.\d+)?)\s*(%|million|billion|万|亿)?', claim.get("text", ""))
            for num, unit in nums:
                numbers.append({
                    "value": float(num),
                    "unit": unit,
                    "source": claim.get("source", ""),
                    "credibility": claim.get("credibility_score", 0)
                })

        # Same unit but >20% difference
        for i, n1 in enumerate(numbers):
            for n2 in numbers[i+1:]:
                if n1["unit"] == n2["unit"] and n1["value"] > 0:
                    diff = abs(n1["value"] - n2["value"]) / n1["value"]
                    if diff > 0.20:
                        conflicts.append({
                            "claim1": n1,
                            "claim2": n2,
                            "difference": f"{diff:.0%}"
                        })

        return conflicts

    def _detect_qualitative_conflicts(self, claims: list[dict]) -> list[dict]:
        """Detect qualitative contradictions."""
        conflicts = []

        # Simple opposition word detection
        oppositions = [
            ("increase", "decrease"),
            ("rise", "fall"),
            ("positive", "negative"),
            ("支持", "反对"),
            ("增长", "下降"),
            ("优点", "缺点"),
        ]

        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                text1 = c1.get("text", "").lower()
                text2 = c2.get("text", "").lower()

                for word1, word2 in oppositions:
                    if (word1.lower() in text1 and word2.lower() in text2) or \
                       (word2.lower() in text1 and word1.lower() in text2):
                        conflicts.append({
                            "claim1": c1.get("source", ""),
                            "claim2": c2.get("source", ""),
                            "opposition": (word1, word2)
                        })
                        break

        return conflicts


class QualityCheckPipeline:
    """Research results quality check pipeline."""

    def __init__(self):
        self.checks = [
            self._check_source_count,
            self._check_citation_completeness,
            self._check_data_support,
            self._check_contradictions,
            self._check_structure,
            self._check_language_quality,
        ]

    def run(self, result: str, metadata: dict) -> dict:
        """Run all quality checks."""
        issues = []
        scores = {}

        for check in self.checks:
            check_result = check(result, metadata)
            issues.extend(check_result.get("issues", []))
            scores[check.__name__] = check_result.get("score", 0)

        overall_score = sum(scores.values()) / len(scores) if scores else 0

        return {
            "overall_score": round(overall_score, 3),
            "passed": overall_score >= 0.70,
            "scores": scores,
            "issues": issues,
            "recommendation": self._get_recommendation(overall_score),
        }

    def _check_source_count(self, result: str, metadata: dict) -> dict:
        """Check citation count."""
        url_count = result.count("http")
        score = min(url_count / 10, 1.0)
        issues = []
        if url_count < 5:
            issues.append(f"Too few sources ({url_count}), recommend at least 10")
        return {"score": score, "issues": issues}

    def _check_citation_completeness(self, result: str, metadata: dict) -> dict:
        """Check citation completeness."""
        complete_citations = len(re.findall(r'http.*?\d{4}', result))
        total_citations = result.count("http")
        completeness = complete_citations / max(total_citations, 1)
        issues = []
        if completeness < 0.5:
            issues.append(f"Incomplete citations, {int((1-completeness)*100)}% missing date info")
        return {"score": completeness, "issues": issues}

    def _check_data_support(self, result: str, metadata: dict) -> dict:
        """Check data support."""
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$', result))
        data_density = len(re.findall(r'\d+', result)) / max(len(result.split()), 1)
        score = min(data_density * 100, 1.0) if has_data else 0.3
        issues = []
        if not has_data:
            issues.append("Lacks data support, mostly qualitative descriptions")
        return {"score": score, "issues": issues}

    def _check_contradictions(self, result: str, metadata: dict) -> dict:
        """Check contradiction handling."""
        has_contradictions_section = "矛盾" in result or "contradiction" in result.lower()
        has_debate_section = "debate" in result.lower() or "分歧" in result
        score = 0.7 if (has_contradictions_section or has_debate_section) else 0.4
        issues = []
        if not has_contradictions_section and not has_debate_section:
            issues.append("No explicit contradictions标注")
        return {"score": score, "issues": issues}

    def _check_structure(self, result: str, metadata: dict) -> dict:
        """Check structure completeness."""
        required_sections = ["summary", "finding", "source"]
        present = [s for s in required_sections if s in result.lower()]
        score = len(present) / len(required_sections)
        missing = [s for s in required_sections if s not in result.lower()]
        issues = [f"Missing required section: {', '.join(missing)}"] if missing else []
        return {"score": score, "issues": issues}

    def _check_language_quality(self, result: str, metadata: dict) -> dict:
        """Check language quality."""
        sentences = re.split(r'[.!?。！？]', result)
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        has_transitions = bool(re.search(r'however|therefore|moreover|然而|因此|此外', result, re.I))
        score = 0.6
        if 10 < avg_length < 30:
            score += 0.2
        if has_transitions:
            score += 0.2
        return {"score": min(score, 1.0), "issues": []}

    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score."""
        if score >= 0.85:
            return "Excellent quality, ready for delivery"
        elif score >= 0.70:
            return "Good quality, recommend human review"
        elif score >= 0.50:
            return "Average quality, recommend re-research or major revision"
        else:
            return "Poor quality, recommend re-executing research process"
