"""
MiroThinker - Search and Scraping Tools
Free tools: DuckDuckGo + Trafilatura (zero cost).
"""


class ToolClient:
    """Self-developed search and scraping - zero cost solution."""

    def __init__(self):
        # No API keys needed, using free open-source libraries
        pass

    async def google_search(self, query: str, num_results: int = 10) -> list[dict]:
        """Search using DuckDuckGo (free)."""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=min(num_results, 5))]

            return [{
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", "")[:150]
            } for r in results]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]

    async def scrape_webpage(self, url: str) -> str:
        """Lightweight scraping using Trafilatura."""
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded, include_comments=False)
                return (content or "")[:800]
            return f"Failed to fetch {url}"
        except Exception as e:
            return f"Scrape failed: {str(e)}"
