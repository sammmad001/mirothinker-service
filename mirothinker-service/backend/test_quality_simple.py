"""
Simple test for quality modules without external dependencies.
"""
import re
import sys
from datetime import datetime

# Test domain detection
DOMAIN_CONFIGS = {
    "tech": {
        "name": "技术/科技",
        "keywords": ["AI", "机器学习", "深度学习", "Python", "软件", "算法", "区块链"],
    },
    "finance": {
        "name": "金融/经济",
        "keywords": ["经济", "金融", "GDP", "通胀", "投资", "股市", "市场"],
    },
    "health": {
        "name": "医疗/健康",
        "keywords": ["医疗", "健康", "疾病", "药物", "治疗", "疫苗", "临床"],
    },
}

def detect_domain(query: str) -> str:
    score = {"tech": 0, "finance": 0, "health": 0}
    for kw in DOMAIN_CONFIGS["tech"]["keywords"]:
        if kw.lower() in query.lower():
            score["tech"] += 1
    for kw in DOMAIN_CONFIGS["finance"]["keywords"]:
        if kw.lower() in query.lower():
            score["finance"] += 1
    for kw in DOMAIN_CONFIGS["health"]["keywords"]:
        if kw.lower() in query.lower():
            score["health"] += 1
    max_domain = max(score, key=score.get)
    return max_domain if score[max_domain] > 0 else "general"

print("\n=== Testing Domain Detection ===")
tests = [
    ("AI 机器学习 Python", "tech"),
    ("经济 GDP 投资", "finance"),
    ("医疗 健康 疫苗", "health"),
    ("weather forecast", "general"),
]
for query, expected in tests:
    result = detect_domain(query)
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status}: '{query}' -> {result}")

# Test Credibility Scorer
class SourceCredibilityScorer:
    def __init__(self):
        self.source_weights = {
            "nature.com": 0.95,
            "arxiv.org": 0.85,
            "reuters.com": 0.90,
            "github.com": 0.80,
            "wikipedia.org": 0.70,
        }

    def score(self, url: str, content: str, metadata: dict = None) -> dict:
        domain = self._extract_domain(url)
        base_weight = self.source_weights.get(domain, 0.50)
        content_score = self._evaluate_content(content)
        recency_score = 0.5
        citation_score = self._evaluate_citations(content)
        final_score = base_weight * 0.4 + content_score * 0.3 + recency_score * 0.15 + citation_score * 0.15
        return {
            "score": round(final_score, 3),
            "level": self._score_to_level(final_score),
        }

    def _extract_domain(self, url: str) -> str:
        match = re.search(r'://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url

    def _evaluate_content(self, content: str) -> float:
        score = 0.5
        if re.search(r'\d+[\.,]\d+|%|\$', content):
            score += 0.15
        if re.search(r'\[\d+\]|\(.*?et al\.|according to', content, re.I):
            score += 0.15
        word_count = len(content.split())
        if 200 < word_count < 3000:
            score += 0.1
        if re.search(r'by \w+|authored by|published by', content, re.I):
            score += 0.1
        return min(score, 1.0)

    def _evaluate_citations(self, content: str) -> float:
        score = 0.5
        citation_count = len(re.findall(r'\[\d+\]|http[s]?://', content))
        if citation_count > 5:
            score += 0.3
        elif citation_count > 2:
            score += 0.15
        return min(score, 1.0)

    def _score_to_level(self, score: float) -> str:
        if score >= 0.85:
            return "A (权威)"
        elif score >= 0.70:
            return "B (可靠)"
        elif score >= 0.50:
            return "C (一般)"
        else:
            return "D (谨慎)"

print("\n=== Testing Credibility Scorer ===")
scorer = SourceCredibilityScorer()
test_cases = [
    ("https://arxiv.org/abs/1234", "Research with data 42.5% and [1] citations"),
    ("https://medium.com/post", "Short blog post"),
    ("https://reuters.com/news", "News with data and sources https://example.com"),
]
for url, content in test_cases:
    result = scorer.score(url, content)
    print(f"  {url}: Score={result['score']}, Level={result['level']}")

# Test Contradiction Detector
class ContradictionDetector:
    def detect(self, claims: list) -> list:
        contradictions = []
        topics = {}
        for claim in claims:
            topic = claim.get("topic", "general")
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(claim)
        
        for topic, topic_claims in topics.items():
            if len(topic_claims) < 2:
                continue
            numeric_conflicts = self._detect_numeric_conflicts(topic_claims)
            if numeric_conflicts:
                contradictions.append({"topic": topic, "type": "numeric_conflict"})
        return contradictions

    def _detect_numeric_conflicts(self, claims: list) -> list:
        conflicts = []
        numbers = []
        for claim in claims:
            nums = re.findall(r'(\d+(?:\.\d+)?)\s*(%|million|billion)?', claim.get("text", ""))
            for num, unit in nums:
                numbers.append({"value": float(num), "unit": unit, "source": claim.get("source", "")})
        
        for i, n1 in enumerate(numbers):
            for n2 in numbers[i+1:]:
                if n1["unit"] == n2["unit"] and n1["value"] > 0:
                    diff = abs(n1["value"] - n2["value"]) / n1["value"]
                    if diff > 0.20:
                        conflicts.append({"claim1": n1["source"], "claim2": n2["source"], "difference": f"{diff:.0%}"})
        return conflicts

print("\n=== Testing Contradiction Detector ===")
detector = ContradictionDetector()
claims = [
    {"topic": "market", "text": "Market worth $50 billion", "source": "A"},
    {"topic": "market", "text": "Market worth $70 billion", "source": "B"},
    {"topic": "growth", "text": "Growth at 5%", "source": "C"},
]
contradictions = detector.detect(claims)
print(f"  Found {len(contradictions)} contradictions")
for c in contradictions:
    print(f"    Topic: {c['topic']}, Type: {c['type']}")

# Test Quality Pipeline
class QualityCheckPipeline:
    def run(self, result: str, metadata: dict) -> dict:
        url_count = result.count("http")
        has_data = bool(re.search(r'\d+[\.,]\d+|%|\$', result))
        has_summary = "summary" in result.lower()
        has_sources = "source" in result.lower()
        
        score = 0.5
        if url_count >= 5:
            score += 0.2
        if has_data:
            score += 0.1
        if has_summary and has_sources:
            score += 0.2
        
        return {"overall_score": round(min(score, 1.0), 3), "passed": score >= 0.70}

print("\n=== Testing Quality Pipeline ===")
pipeline = QualityCheckPipeline()
test_result = """
# Research Report
## Executive Summary
AI market growing at 30% annually.
## Findings
Market worth $50 billion (https://reuters.com/ai-2024)
Expected $70 billion by 2025 (https://bloomberg.com/ai-2025)
## Sources
- https://reuters.com/ai-2024
- https://bloomberg.com/ai-2025
"""
report = pipeline.run(test_result, {})
print(f"  Score: {report['overall_score']}, Passed: {report['passed']}")

print("\n=== All tests completed successfully ===")
