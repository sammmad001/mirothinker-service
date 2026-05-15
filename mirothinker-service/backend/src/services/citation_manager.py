"""
MiroThinker - Citation Manager
Handles inline citation formatting and claim-URL pairing.
Zero-cost solution for improving source attribution.
"""

import re
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Citation:
    """Represents a single citation reference."""
    index: int
    url: str
    title: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None

    def format_markdown(self, use_brackets: bool = True) -> str:
        """Format citation as markdown link."""
        display = f"[{self.index}]"
        if self.url:
            return f"[{display}]({self.url})"
        return display


@dataclass
class Claim:
    """Represents a claim that can be cited."""
    text: str
    start_pos: int
    end_pos: int
    citations: list[int] = field(default_factory=list)


class CitationManager:
    """
    Manages inline citations and claim-URL pairing.

    Usage:
        manager = CitationManager()
        manager.add_source("https://example.com", title="Example", date="2024-01-15")
        formatted = manager.format_with_citations(claim_text, citations=[1])
    """

    def __init__(self):
        self.citations: list[Citation] = []
        self._url_index_map: dict[str, int] = {}

    def add_source(self, url: str, title: Optional[str] = None,
                   date: Optional[str] = None, source: Optional[str] = None) -> int:
        """
        Add a source URL and return its citation index.

        Args:
            url: Source URL
            title: Optional title
            date: Optional publication date
            source: Optional source name

        Returns:
            Citation index (1-based)
        """
        # Deduplicate by URL
        if url in self._url_index_map:
            return self._url_index_map[url]

        citation = Citation(
            index=len(self.citations) + 1,
            url=url,
            title=title,
            date=date,
            source=source
        )
        self.citations.append(citation)
        self._url_index_map[url] = citation.index
        return citation.index

    def add_sources_from_results(self, search_results: list[dict]) -> list[int]:
        """
        Add multiple sources from search results.

        Args:
            search_results: List of dicts with url, title, date keys

        Returns:
            List of citation indices
        """
        indices = []
        for result in search_results:
            url = result.get("url")
            if url:
                idx = self.add_source(
                    url=url,
                    title=result.get("title"),
                    date=result.get("date"),
                    source=result.get("source")
                )
                indices.append(idx)
        return indices

    def format_with_citations(self, text: str, citations: list[int]) -> str:
        """
        Insert inline citation markers into text.

        Args:
            text: Original text
            citations: List of citation indices to insert

        Returns:
            Text with inline citations like [1][2]
        """
        if not citations:
            return text

        # Create citation marker
        marker = "".join(f"[{idx}]" for idx in citations)

        # Simple insertion at end of sentence or end of text
        text = text.rstrip()
        if text.endswith("."):
            return text[:-1] + f" {marker}."
        else:
            return text + f" {marker}"

    def format_claim_with_mapping(self, claim: str, url: str) -> str:
        """
        Format a claim with a specific URL (Claim-URL pairing).

        Args:
            claim: The claim text
            url: The source URL

        Returns:
            Claim with inline citation
        """
        idx = self.add_source(url)
        return self.format_with_citations(claim, [idx])

    def get_citation_list(self) -> list[dict]:
        """
        Get formatted citation list for references section.

        Returns:
            List of dicts with index, url, title, date
        """
        return [
            {
                "index": c.index,
                "url": c.url,
                "title": c.title or c.url,
                "date": c.date,
                "source": c.source
            }
            for c in self.citations
        ]

    def format_references_markdown(self) -> str:
        """
        Format citations as Markdown references section.

        Returns:
            Markdown formatted references
        """
        if not self.citations:
            return ""

        lines = ["## 参考来源\n"]

        for c in self.citations:
            index_marker = f"[{c.index}]:"
            title = c.title or c.url

            if c.url:
                lines.append(f"{index_marker} {title}")
                lines.append(f"    URL: {c.url}")
            else:
                lines.append(f"{index_marker} {title}")

            if c.date:
                lines.append(f"    日期: {c.date}")
            if c.source:
                lines.append(f"    来源: {c.source}")
            lines.append("")  # Blank line between entries

        return "\n".join(lines)

    def copy_all_urls(self) -> str:
        """
        Get all URLs as a copyable string (one per line).

        Returns:
            All URLs as newline-separated string
        """
        return "\n".join(c.url for c in self.citations if c.url)

    def clear(self):
        """Clear all citations."""
        self.citations.clear()
        self._url_index_map.clear()

    @staticmethod
    def extract_citations_from_text(text: str) -> list[int]:
        """
        Extract citation indices from text.

        Args:
            text: Text with citations like [1][2][3]

        Returns:
            List of citation indices
        """
        matches = re.findall(r'\[(\d+)\]', text)
        return [int(m) for m in matches]

    @staticmethod
    def extract_urls_from_text(text: str) -> list[str]:
        """
        Extract URLs from text.

        Args:
            text: Text containing URLs

        Returns:
            List of URLs
        """
        url_pattern = r'https?://[^\s\)\]"\'<>]+'
        return re.findall(url_pattern, text)


class InlineCitationBuilder:
    """
    Build inline citations from research results.

    Usage:
        builder = InlineCitationBuilder()
        builder.add_result("Title 1", "https://example1.com", "2024-01-15")
        builder.add_result("Title 2", "https://example2.com", "2024-02-20")
        result_text = builder.format_claim_with_inlines("This is a claim.", [1, 2])
    """

    def __init__(self):
        self.manager = CitationManager()
        self.results: list[dict] = []

    def add_result(self, title: str, url: str, date: Optional[str] = None,
                   source: Optional[str] = None):
        """Add a search result as a citation source."""
        self.results.append({
            "title": title,
            "url": url,
            "date": date,
            "source": source
        })
        self.manager.add_source(url, title, date, source)

    def add_results(self, results: list[dict]):
        """Add multiple search results."""
        for r in results:
            self.add_result(
                title=r.get("title", ""),
                url=r.get("url", ""),
                date=r.get("date"),
                source=r.get("source")
            )

    def format_claim_with_inlines(self, claim: str, source_indices: list[int]) -> str:
        """Format a claim with inline citation markers."""
        return self.manager.format_with_citations(claim, source_indices)

    def get_references(self) -> str:
        """Get formatted references section."""
        return self.manager.format_references_markdown()

    def get_all_urls(self) -> str:
        """Get all URLs as copyable string."""
        return self.manager.copy_all_urls()


# Example usage
if __name__ == "__main__":
    # Example 1: Basic citation management
    manager = CitationManager()

    manager.add_source(
        url="https://www.example.com/article",
        title="Example Article",
        date="2024-01-15",
        source="Example.com"
    )
    manager.add_source(
        url="https://www.another.com/research",
        title="Research Paper",
        date="2024-02-20"
    )

    text = "Machine learning is transforming industries."
    formatted = manager.format_with_citations(text, citations=[1, 2])
    print(f"Formatted: {formatted}")

    print("\nReferences:")
    print(manager.format_references_markdown())

    print("\nAll URLs:")
    print(manager.copy_all_urls())

    # Example 2: Claim-URL pairing
    print("\n--- Claim-URL Pairing ---")
    claim = "According to recent studies, AI adoption is accelerating."
    paired = manager.format_claim_with_mapping(claim, "https://www.example.com/article")
    print(f"Claim: {paired}")

    # Example 3: InlineCitationBuilder
    print("\n--- Inline Citation Builder ---")
    builder = InlineCitationBuilder()
    builder.add_result("Research on AI", "https://example1.com", "2024-01-01")
    builder.add_result("AI Market Analysis", "https://example2.com", "2024-02-01")
    builder.add_result("Tech Trends 2024", "https://example3.com", "2024-03-01")

    claim = "The AI market is growing rapidly."
    result = builder.format_claim_with_inlines(claim, [1, 2])
    print(f"Result: {result}")
    print("\nReferences:")
    print(builder.get_references())