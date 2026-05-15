"""
MiroThinker - Citation Integration
Integrates CitationManager into ResearchAgent output pipeline.
Adds inline citation markers [1][2] and generates reference sections.
"""

from typing import Optional, list
from .citation_manager import CitationManager, Citation, InlineCitationBuilder
from .url_validator import URLValidator, quick_check_urls


class CitationIntegration:
    """
    Citation tracking for research output.

    Integrates with research pipeline to:
    - Track all sources used
    - Generate inline citation markers [1][2]
    - Create reference sections
    - Validate URL availability

    Usage:
        integrator = CitationIntegration()
        integrator.add_sources(search_results)
        formatted_text = integrator.format_with_citations(raw_text)
        references = integrator.get_references()
    """

    def __init__(self):
        self.manager = CitationManager()
        self.url_validator = URLValidator()

    def add_sources(self, sources: list[dict]):
        """
        Add sources from search results.

        Args:
            sources: List of dicts with 'url', 'title', 'date' keys
        """
        self.manager.add_sources_from_results(sources)

    def add_source(self, url: str, title: str = None, date: str = None):
        """Add a single source."""
        self.manager.add_source(url, title=title, date=date)

    def format_with_citations(self, text: str, citation_indices: list[int]) -> str:
        """
        Format text with inline citation markers.

        Args:
            text: Text to format
            citation_indices: List of citation indices to insert

        Returns:
            Formatted text with [1][2] markers
        """
        return self.manager.format_with_citations(text, citation_indices)

    def format_claim_with_url(self, claim: str, url: str, title: str = None) -> str:
        """
        Format a claim with direct URL citation (Claim-URL pairing).

        Args:
            claim: The claim text
            url: Source URL
            title: Optional source title

        Returns:
            Claim with inline citation
        """
        return self.manager.format_claim_with_mapping(claim, url)

    def get_references_markdown(self) -> str:
        """Get formatted reference section."""
        return self.manager.format_references_markdown()

    def get_all_urls(self) -> str:
        """Get all URLs as copyable string."""
        return self.manager.copy_all_urls()

    async def validate_urls(self, max_concurrent: int = 10) -> list[dict]:
        """
        Validate all tracked URLs asynchronously.

        Returns:
            List of validation results
        """
        urls = [c.url for c in self.manager.citations if c.url]
        if not urls:
            return []

        return await quick_check_urls(urls)

    def get_stats(self) -> dict:
        """Get citation statistics."""
        return {
            "total_sources": len(self.manager.citations),
            "urls": [c.url for c in self.manager.citations if c.url],
        }


class ResearchOutputFormatter:
    """
    Formats research output with proper citations and references.

    Usage:
        formatter = ResearchOutputFormatter()
        formatter.add_sources(search_results)
        output = formatter.format_research_report(raw_report)
    """

    def __init__(self):
        self.integration = CitationIntegration()

    def add_sources(self, sources: list[dict]):
        """Add sources from search results."""
        self.integration.add_sources(sources)

    def format_research_report(
        self,
        report: str,
        validate_urls: bool = True,
    ) -> str:
        """
        Format research report with citations and references.

        Args:
            report: Raw research report
            validate_urls: Whether to validate URLs

        Returns:
            Formatted report with references section
        """
        # Add reference section
        references = self.integration.get_references_markdown()

        if references:
            report = f"{report}\n\n{references}"

        # Optionally validate URLs
        if validate_urls:
            # This is async, so we just return a placeholder
            # The actual validation can be done separately
            pass

        return report

    def format_with_inline_citations(
        self,
        sections: list[dict],
    ) -> str:
        """
        Format multiple sections with proper citations.

        Args:
            sections: List of dicts with 'content', 'citations' keys

        Returns:
            Formatted text with all sections
        """
        parts = []

        for section in sections:
            content = section.get("content", "")
            citations = section.get("citations", [])

            if citations:
                formatted = self.integration.format_with_citations(content, citations)
            else:
                formatted = content

            parts.append(formatted)

        return "\n\n".join(parts)

    def get_copyable_urls(self) -> str:
        """Get all source URLs as copyable text."""
        return self.integration.get_all_urls()


class CitationTracker:
    """
    Tracks citations across research turns.

    Accumulates sources and provides deduplication.
    """

    def __init__(self):
        self.sources: dict[str, dict] = {}  # url -> source info
        self.citation_map: dict[str, int] = {}  # url -> citation index
        self.next_index = 1

    def add_source(
        self,
        url: str,
        title: str = None,
        date: str = None,
        snippet: str = None,
    ) -> int:
        """
        Add a source and return its citation index.

        Deduplicates by URL.
        """
        if url in self.citation_map:
            return self.citation_map[url]

        self.sources[url] = {
            "title": title,
            "date": date,
            "snippet": snippet,
        }
        self.citation_map[url] = self.next_index
        self.next_index += 1

        return self.citation_map[url]

    def add_sources_from_results(self, results: list[dict]):
        """Add multiple sources from search results."""
        indices = []
        for r in results:
            url = r.get("url") or r.get("link")
            if url:
                idx = self.add_source(
                    url=url,
                    title=r.get("title"),
                    date=r.get("extracted_date"),
                    snippet=r.get("snippet"),
                )
                indices.append(idx)
        return indices

    def get_citation_index(self, url: str) -> Optional[int]:
        """Get citation index for a URL."""
        return self.citation_map.get(url)

    def format_citation_marker(self, url: str) -> str:
        """Format citation marker for a URL."""
        idx = self.get_citation_index(url)
        if idx:
            return f"[{idx}]"
        return ""

    def format_references(self) -> str:
        """Format references section."""
        if not self.sources:
            return ""

        lines = ["## 参考来源\n"]

        for url, info in self.sources.items():
            idx = self.citation_map[url]
            title = info.get("title") or url
            date = info.get("date")

            lines.append(f"[{idx}] {title}")
            lines.append(f"    URL: {url}")
            if date:
                lines.append(f"    日期: {date}")
            lines.append("")

        return "\n".join(lines)

    def clear(self):
        """Clear all tracked sources."""
        self.sources.clear()
        self.citation_map.clear()
        self.next_index = 1


# Example usage
if __name__ == "__main__":
    print("=== Citation Integration Test ===\n")

    # Test CitationIntegration
    integrator = CitationIntegration()

    # Add sources
    sources = [
        {"url": "https://example.com/ai", "title": "AI发展报告", "date": "2026-01-01"},
        {"url": "https://example.com/ml", "title": "机器学习研究", "date": "2025-12-15"},
        {"url": "https://example.com/dl", "title": "深度学习进展", "date": "2025-11-20"},
    ]
    integrator.add_sources(sources)

    # Format with citations
    claim = "人工智能正在改变各行各业"
    formatted = integrator.format_with_citations(claim, [1, 2])
    print(f"Formatted: {formatted}")

    # Get references
    print("\nReferences:")
    print(integrator.get_references_markdown())

    # Test CitationTracker
    print("\n=== Citation Tracker Test ===\n")

    tracker = CitationTracker()

    # Add sources
    results = [
        {"url": "https://source1.com", "title": "Source 1", "extracted_date": "2026-01-01"},
        {"url": "https://source2.com", "title": "Source 2", "extracted_date": "2025-12-01"},
    ]
    indices = tracker.add_sources_from_results(results)
    print(f"Added sources, indices: {indices}")

    # Dedup test
    tracker.add_source("https://source1.com", "Source 1 duplicate")
    print(f"After duplicate, next index: {tracker.next_index}")

    # Format references
    print("\nReferences:")
    print(tracker.format_references())