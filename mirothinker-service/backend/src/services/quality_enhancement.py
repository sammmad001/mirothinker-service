"""
MiroThinker - Quality Enhancement Integration
Integrates BailianFactChecker and EnhancedContradictionDetector
into the research output pipeline.
"""

from typing import Optional
from .fact_checker import BailianFactChecker, InlineFactChecker, VerificationResult
from .contradiction import EnhancedContradictionDetector, Conflict


class QualityEnhancer:
    """
    Enhanced quality checking with fact verification.

    Integrates:
    - BailianFactChecker for claim verification
    - EnhancedContradictionDetector for conflict detection
    - URL validation (async)

    Usage:
        enhancer = QualityEnhancer()
        result = enhancer.enhance_report(raw_report, sources, citations)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        min_confidence: float = 0.6,
    ):
        """
        Args:
            api_key: DASHSCOPE_API_KEY (falls back to env)
            min_confidence: Minimum confidence for issue flagging
        """
        self.fact_checker = BailianFactChecker(api_key) if api_key else None
        self.inline_checker = InlineFactChecker(api_key) if api_key else None
        self.contradiction_detector = EnhancedContradictionDetector()
        self.min_confidence = min_confidence

    def enhance_report(
        self,
        report: str,
        sources: list[dict] = None,
        citations: list[str] = None,
        check_facts: bool = True,
        check_contradictions: bool = True,
    ) -> dict:
        """
        Enhance research report with quality checks.

        Args:
            report: Raw research report text
            sources: List of source dicts (from search results)
            citations: List of citation URLs
            check_facts: Whether to run fact verification
            check_contradictions: Whether to run contradiction detection

        Returns:
            Dict with enhanced report, issues, and metadata
        """
        result = {
            "report": report,
            "issues": [],
            "warnings": [],
            "verification_results": [],
            "contradiction_results": [],
            "url_validation": [],
        }

        # Step 1: Contradiction detection
        if check_contradictions and sources:
            contradictions = self.contradiction_detector.detect_from_results(sources)
            if contradictions:
                result["contradiction_results"] = contradictions
                report = self._add_contradiction_section(report, contradictions)
                result["report"] = report

        # Step 2: Fact verification (requires API key)
        if check_facts and self.fact_checker and self.inline_checker:
            verification_results = self.inline_checker.check_claims_in_text(
                report,
                min_confidence=self.min_confidence
            )

            # Filter for issues
            issues = [
                r for r in verification_results
                if r.confidence < self.min_confidence or r.status.value == "contradicted"
            ]

            if issues:
                result["verification_results"] = issues
                report = self._add_fact_check_section(report, issues)
                result["report"] = report

        return result

    def check_claim(self, claim: str, context: str = None) -> VerificationResult:
        """
        Check a single claim.

        Args:
            claim: The claim to verify
            context: Optional context

        Returns:
            VerificationResult
        """
        if not self.fact_checker:
            return VerificationResult(
                status=None,
                claim=claim,
                verdict="Fact checker not initialized (no API key)",
                details="Set DASHSCOPE_API_KEY to enable",
                confidence=0.0,
                sources=[],
            )

        return self.fact_checker.verify(claim, context)

    def check_contradictions(self, sources: list[dict]) -> list[Conflict]:
        """
        Check for contradictions in sources.

        Args:
            sources: List of source dicts

        Returns:
            List of detected conflicts
        """
        return self.contradiction_detector.detect_from_results(sources)

    def _add_contradiction_section(self, report: str, conflicts: list[Conflict]) -> str:
        """Add contradiction section to report."""
        conflict_report = self.contradiction_detector.format_conflict_report(conflicts)

        # Insert before final section or at end
        if "## 结论" in report:
            parts = report.split("## 结论")
            report = parts[0] + conflict_report + "\n\n## 结论" + parts[1]
        else:
            report = report + "\n\n" + conflict_report

        return report

    def _add_fact_check_section(self, report: str, issues: list[VerificationResult]) -> str:
        """Add fact check section to report."""
        section = ["\n\n## 事实核查\n"]

        for i, result in enumerate(issues, 1):
            status_icon = "❌" if result.status.value == "contradicted" else "⚠️"
            section.append(f"{status_icon} **声明{i}**: {result.claim}")
            section.append(f"   - 判断: {result.verdict}")
            section.append(f"   - 置信度: {result.confidence:.0%}")
            if result.suggestions:
                section.append(f"   - 建议: {result.suggestions}")
            section.append("")

        return report + "\n".join(section)


class QualityReportBuilder:
    """
    Builds research reports with integrated quality checks.

    Usage:
        builder = QualityReportBuilder()
        builder.add_sources(search_results)
        report = builder.build(
            raw_content,
            check_facts=True,
            add_references=True,
        )
    """

    def __init__(self, api_key: Optional[str] = None):
        self.enhancer = QualityEnhancer(api_key)
        self.sources: list[dict] = []
        self.citations: list[str] = []

    def add_sources(self, sources: list[dict]):
        """Add sources from search results."""
        self.sources.extend(sources)
        for s in sources:
            url = s.get("url") or s.get("link")
            if url and url not in self.citations:
                self.citations.append(url)

    def build(
        self,
        content: str,
        check_facts: bool = True,
        check_contradictions: bool = True,
        add_references: bool = True,
    ) -> dict:
        """
        Build enhanced report.

        Args:
            content: Raw research content
            check_facts: Run fact verification
            check_contradictions: Run contradiction detection
            add_references: Add reference section

        Returns:
            Dict with enhanced report and metadata
        """
        # Run quality enhancement
        result = self.enhancer.enhance_report(
            report=content,
            sources=self.sources,
            citations=self.citations,
            check_facts=check_facts,
            check_contradictions=check_contradictions,
        )

        # Add reference section
        if add_references and self.sources:
            result["report"] = self._add_references(result["report"])

        return result

    def _add_references(self, report: str) -> str:
        """Add reference section."""
        if not self.sources:
            return report

        lines = ["\n\n---\n\n## 参考来源\n"]

        for i, source in enumerate(self.sources, 1):
            title = source.get("title", "Unknown")
            url = source.get("url") or source.get("link", "")
            date = source.get("extracted_date") or source.get("date", "")

            lines.append(f"[{i}] {title}")
            if url:
                lines.append(f"   URL: {url}")
            if date:
                lines.append(f"   日期: {date}")
            lines.append("")

        return report + "\n".join(lines)

    def get_url_list(self) -> str:
        """Get all URLs as copyable list."""
        return "\n".join(self.citations)

    def clear(self):
        """Clear all sources."""
        self.sources.clear()
        self.citations.clear()


# Example usage
if __name__ == "__main__":
    import os

    api_key = os.getenv("DASHSCOPE_API_KEY")

    print("=== Quality Enhancement Test ===\n")

    # Test with sample data
    enhancer = QualityEnhancer(api_key)

    # Sample sources with potential contradictions
    sources = [
        {"title": "AI market grew 25%", "snippet": "The AI market grew by 25% in 2024", "url": "https://example1.com"},
        {"title": "AI market grew 15%", "snippet": "The AI market grew by 15% in 2024", "url": "https://example2.com"},
        {"title": "DL improves accuracy", "snippet": "Deep learning improves accuracy to 95%", "url": "https://example3.com"},
        {"title": "DL accuracy declining", "snippet": "Deep learning accuracy is declining", "url": "https://example4.com"},
    ]

    # Check contradictions
    print("Checking for contradictions...")
    conflicts = enhancer.check_contradictions(sources)
    print(f"Found {len(conflicts)} conflicts")

    for c in conflicts:
        print(f"  - {c.conflict_type.value}: {c.claim1.get('source', '')} vs {c.claim2.get('source', '')}")

    # Test report enhancement
    print("\n\nEnhancing report...")
    report = """
    ## 研究发现

    人工智能市场在2024年增长了25%。深度学习技术在图像识别任务上取得了重大进展。

    结论：AI技术正在快速发展。
    """

    result = enhancer.enhance_report(report, sources)

    print("\nEnhanced Report:")
    print(result["report"][:500] + "...")

    if result["contradiction_results"]:
        print(f"\n⚠️ Found {len(result['contradiction_results'])} contradictions")

    # Test with QualityReportBuilder
    print("\n\n=== QualityReportBuilder Test ===\n")

    builder = QualityReportBuilder(api_key)
    builder.add_sources(sources)

    built = builder.build(
        "AI市场正在快速增长，技术创新不断涌现。",
        check_facts=True,
        add_references=True,
    )

    print("Built Report:")
    print(built["report"])