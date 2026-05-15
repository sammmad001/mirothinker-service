"""
MiroThinker - URL Availability Checker
Zero-cost solution for URL validation using httpx async requests.
"""

import asyncio
from typing import Optional
import httpx


class URLValidator:
    """Async URL availability checker with retry support."""

    def __init__(self, timeout: float = 10.0, max_retries: int = 2):
        """
        Args:
            timeout: Request timeout in seconds
            max_retries: Number of retries on failure
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def check_url(self, url: str) -> dict:
        """
        Check URL availability with retries.

        Args:
            url: URL to check

        Returns:
            dict with status, status_code, error, and response_time
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.head(url)

                return {
                    "url": url,
                    "status": "available",
                    "status_code": response.status_code,
                    "error": None,
                    "response_time": None,  # httpx doesn't expose this easily
                    "checked": True,
                    "valid": 200 <= response.status_code < 400
                }

            except httpx.TimeoutException:
                last_error = "timeout"
            except httpx.ConnectError as e:
                last_error = f"connection_error: {str(e)}"
            except httpx.HTTPStatusError as e:
                return {
                    "url": url,
                    "status": "error",
                    "status_code": e.response.status_code,
                    "error": f"http_status_{e.response.status_code}",
                    "checked": True,
                    "valid": False
                }
            except Exception as e:
                last_error = str(e)

        # All retries failed
        return {
            "url": url,
            "status": "unavailable",
            "status_code": None,
            "error": last_error,
            "checked": True,
            "valid": False
        }

    async def check_urls(self, urls: list[str], max_concurrent: int = 10) -> list[dict]:
        """
        Check multiple URLs concurrently.

        Args:
            urls: List of URLs to check
            max_concurrent: Maximum concurrent requests

        Returns:
            List of check results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_with_semaphore(url: str) -> dict:
            async with semaphore:
                return await self.check_url(url)

        tasks = [check_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def check_urls_safe(self, urls: list[str], max_concurrent: int = 10) -> list[dict]:
        """
        Safe wrapper that catches all exceptions and returns valid results.

        Args:
            urls: List of URLs to check
            max_concurrent: Maximum concurrent requests

        Returns:
            List of check results (always has same length as input)
        """
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        for url in urls:
            async with semaphore:
                try:
                    result = await self.check_url(url)
                    results.append(result)
                except Exception as e:
                    results.append({
                        "url": url,
                        "status": "exception",
                        "status_code": None,
                        "error": str(e),
                        "checked": True,
                        "valid": False
                    })

        return results


async def quick_check_url(url: str) -> dict:
    """Quick single URL check helper function."""
    validator = URLValidator(timeout=5.0)
    return await validator.check_url(url)


async def quick_check_urls(urls: list[str]) -> list[dict]:
    """Quick multiple URL check helper function."""
    validator = URLValidator(timeout=5.0)
    return await validator.check_urls_safe(urls)


# Example usage
if __name__ == "__main__":
    async def main():
        urls = [
            "https://www.example.com",
            "https://httpbin.org/status/200",
            "https://httpbin.org/status/404",
        ]

        print("Checking URLs...")
        results = await quick_check_urls(urls)

        for r in results:
            status_icon = "✅" if r["valid"] else "❌"
            print(f"{status_icon} {r['url']} - {r['status']} ({r.get('status_code', 'N/A')})")

    asyncio.run(main())