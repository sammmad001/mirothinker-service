"""
Test script for quality enhancement modules.
"""
import sys
sys.path.insert(0, '.')

from main import (
    SourceCredibilityScorer, 
    ContradictionDetector, 
    QualityCheckPipeline,
    detect_domain,
    CORE_SOURCES,
    DOMAIN_CONFIGS
)

def test_domain_detection():
    """Test domain detection functionality."""
    print("\n=== Testing Domain Detection ===")
    
    test_cases = [
        ("AI machine learning algorithm", "tech"),
        ("Python software development", "tech"),
        ("经济 GDP 通胀 投资", "finance"),
        ("medical health disease treatment", "health"),
        ("weather today forecast", "general"),
    ]
    
    for query, expected in test_cases:
        result = detect_domain(query)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}: '{query}' -> {result} (expected: {expected})")

def test_credibility_scorer():
    """Test source credibility scoring."""
    print("\n=== Testing Credibility Scorer ===")
    
    scorer = SourceCredibilityScorer()
    
    test_cases = [
        ("https://arxiv.org/abs/1234", "Research paper content with data 42.5% and [1] citations", "A"),
        ("https://medium.com/post", "Short blog post without citations", "C"),
        ("https://reuters.com/news", "News article with data and sources", "B"),
    ]
    
    for url, content, expected_level in test_cases:
        result = scorer.score(url, content)
        print(f"  URL: {url}")
        print(f"    Score: {result['score']}, Level: {result['level']}")
        print(f"    Breakdown: {result['breakdown']}")

def test_contradiction_detector():
    """Test contradiction detection."""
    print("\n=== Testing Contradiction Detector ===")
    
    detector = ContradictionDetector()
    
    # Test numeric conflicts
    claims = [
        {"topic": "market_size", "text": "The market is worth $50 billion", "source": "Source A"},
        {"topic": "market_size", "text": "The market is worth $70 billion", "source": "Source B"},
        {"topic": "growth", "text": "Growth rate is positive at 5%", "source": "Source C"},
        {"topic": "growth", "text": "Growth rate shows a decline of 3%", "source": "Source D"},
    ]
    
    contradictions = detector.detect(claims)
    print(f"  Found {len(contradictions)} contradictions:")
    for c in contradictions:
        print(f"    - Type: {c['type']}, Topic: {c['topic']}")
        print(f"      Resolution: {c['resolution']}")

def test_quality_pipeline():
    """Test quality check pipeline."""
    print("\n=== Testing Quality Check Pipeline ===")
    
    pipeline = QualityCheckPipeline()
    
    # Good quality result
    good_result = """
# AI Market Analysis

## Executive Summary
The AI market is growing rapidly with multiple sources confirming 30%+ growth.

## Research Findings

### Market Size
- The AI market reached $50 billion in 2024 (Source: https://reuters.com/tech/ai-2024)
- Expected to grow to $70 billion by 2025 (Source: https://bloomberg.com/ai-forecast-2025)

## Analysis
Multiple sources confirm the growth trend, with some variations in exact figures.

## Contradictions & Debates
Some sources differ on exact market size, but all agree on growth direction.

## Sources
- https://reuters.com/tech/ai-2024 (2024)
- https://bloomberg.com/ai-forecast-2025 (2025)
"""
    
    metadata = {"query": "AI market size", "domain": "tech"}
    report = pipeline.run(good_result, metadata)
    
    print(f"  Overall Score: {report['overall_score']}")
    print(f"  Passed: {report['passed']}")
    print(f"  Recommendation: {report['recommendation']}")
    print(f"  Individual Scores:")
    for check, score in report['scores'].items():
        print(f"    - {check}: {score}")
    
    if report['issues']:
        print(f"  Issues Found:")
        for issue in report['issues']:
            print(f"    - {issue}")

def test_core_sources():
    """Test core sources configuration."""
    print("\n=== Testing Core Sources Configuration ===")
    
    print(f"  Configured source categories: {list(CORE_SOURCES.keys())}")
    for name, config in CORE_SOURCES.items():
        print(f"    - {name}: {config['name']} (priority: {config['priority']})")
    
    print(f"\n  Configured domains: {list(DOMAIN_CONFIGS.keys())}")
    for domain, config in DOMAIN_CONFIGS.items():
        print(f"    - {domain}: {config['name']} ({len(config['keywords'])} keywords)")

if __name__ == "__main__":
    print("Running Quality Enhancement Module Tests...")
    
    test_domain_detection()
    test_credibility_scorer()
    test_contradiction_detector()
    test_quality_pipeline()
    test_core_sources()
    
    print("\n=== All tests completed ===")
