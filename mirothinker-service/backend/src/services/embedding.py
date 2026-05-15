"""
MiroThinker - Bailian Embedding Service
OpenAI-compatible interface for Alibaba's text-embedding-v4.
Uses 100万Token free quota (90 days), then ¥0.0005/千Token.
"""

from typing import Optional
import os

# OpenAI SDK for OpenAI-compatible API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class BailianEmbedder:
    """
    Alibaba Bailian Embedding Service.

    Model: text-embedding-v4
    - 100万Token free quota (90 days)
    - Then ¥0.0005/千Token

    Usage:
        embedder = BailianEmbedder()
        vector = embedder.embed("Hello world")
        vectors = embedder.embed_batch(["Hello", "World"])
    """

    MODEL_NAME = "text-embedding-v4"
    BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Pricing (after free quota)
    PRICE_PER_1K_TOKENS = 0.0005  # ¥0.0005

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: DASHSCOPE_API_KEY. Falls back to env var.
        """
        if OpenAI is None:
            raise ImportError("openai package required: pip install openai")

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not set")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.BASE_URL
        )
        self._dimension = None  # Lazy load

    @property
    def dimension(self) -> int:
        """Get embedding dimension (1536 for text-embedding-v4)."""
        if self._dimension is None:
            # Query model info to get dimension
            # text-embedding-v4 uses 1536 dimensions
            self._dimension = 1536
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (list of floats)
        """
        response = self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in one API call.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Truncate very long texts to prevent token limit issues
        truncated = [t[:8000] for t in texts]  # ~2000 tokens max

        response = self.client.embeddings.create(
            model=self.MODEL_NAME,
            input=truncated
        )
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query

        Returns:
            Query embedding vector
        """
        # Queries are usually short, no truncation needed
        return self.embed(query)

    def estimate_cost(self, text: str) -> float:
        """
        Estimate API cost for a text.

        Args:
            text: Input text

        Returns:
            Estimated cost in ¥
        """
        # Rough estimate: ~4 chars per token for Chinese, ~5 for English
        chars = len(text)
        tokens = chars / 4  # Conservative estimate
        return tokens / 1000 * self.PRICE_PER_1K_TOKENS


class EmbeddingCache:
    """Simple in-memory cache for embeddings."""

    def __init__(self, max_size: int = 10000):
        self._cache: dict[str, list[float]] = {}
        self.max_size = max_size

    def get(self, text: str) -> Optional[list[float]]:
        """Get cached embedding."""
        # Use hash as key for consistent lookup
        key = str(hash(text))
        return self._cache.get(key)

    def set(self, text: str, embedding: list[float]):
        """Cache embedding."""
        if len(self._cache) >= self.max_size:
            # Simple eviction: clear half
            keys = list(self._cache.keys())[:self.max_size // 2]
            for k in keys:
                del self._cache[k]

        key = str(hash(text))
        self._cache[key] = embedding

    def clear(self):
        """Clear cache."""
        self._cache.clear()


class CachedBailianEmbedder(BailianEmbedder):
    """Bailian embedder with built-in caching."""

    def __init__(self, api_key: Optional[str] = None, cache_size: int = 10000):
        super().__init__(api_key)
        self._cache = EmbeddingCache(max_size=cache_size)

    def embed(self, text: str) -> list[float]:
        """Get from cache or generate new embedding."""
        cached = self._cache.get(text)
        if cached is not None:
            return cached

        embedding = super().embed(text)
        self._cache.set(text, embedding)
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Get from cache for existing, generate for new."""
        results = []
        to_embed = []
        indices = []

        # Check cache first
        for i, text in enumerate(texts):
            cached = self._cache.get(text)
            if cached is not None:
                results.append((i, cached))
            else:
                to_embed.append(text)
                indices.append(i)

        # Batch embed uncached
        if to_embed:
            new_embeddings = super().embed_batch(to_embed)
            for idx, emb in zip(indices, new_embeddings):
                self._cache.set(texts[idx], emb)
                results.append((idx, emb))

        # Sort by original order
        results.sort(key=lambda x: x[0])
        return [emb for _, emb in results]


# Example usage
if __name__ == "__main__":
    import os

    # Check for API key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("DASHSCOPE_API_KEY not set, skipping live test")
    else:
        print("=== Bailian Embedder Test ===\n")

        # Test cached embedder
        embedder = CachedBailianEmbedder(api_key)

        # Single embed
        text = "人工智能正在改变世界"
        embedding = embedder.embed(text)
        print(f"Single embed: {len(embedding)} dimensions")
        print(f"First 5 values: {embedding[:5]}")

        # Batch embed
        texts = ["机器学习", "深度学习", "自然语言处理"]
        embeddings = embedder.embed_batch(texts)
        print(f"\nBatch embed: {len(embeddings)} vectors")
        print(f"Each has {len(embeddings[0])} dimensions")

        # Cost estimate
        cost = embedder.estimate_cost("这是一个测试文本")
        print(f"\nEstimated cost: ¥{cost:.6f}")

        # Similarity check
        v1 = embedder.embed("人工智能")
        v2 = embedder.embed("机器学习")
        v3 = embedder.embed("今天天气很好")

        # Simple cosine similarity
        def cosine(a, b):
            return sum(x * y for x, y in zip(a, b)) / (
                (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
            )

        print(f"\nCosine similarity:")
        print(f"  AI vs ML: {cosine(v1, v2):.4f}")
        print(f"  AI vs Weather: {cosine(v1, v3):.4f}")