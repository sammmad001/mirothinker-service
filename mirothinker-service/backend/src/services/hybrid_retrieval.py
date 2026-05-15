"""
MiroThinker - Hybrid Retrieval
BM25 + ChromaDB hybrid search for zero-cost RAG.
Combines keyword matching (BM25) with semantic similarity (ChromaDB).

Weights: BM25 0.3 + Vector 0.7 (adjustable)
"""

from typing import Optional
import os

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

from .embedding import BailianEmbedder, CachedBailianEmbedder


class HybridRetriever:
    """
    Hybrid search combining BM25 and vector retrieval.

    Features:
    - BM25 for exact keyword matching
    - ChromaDB for semantic similarity
    - Weighted fusion (default: BM25 0.3, Vector 0.7)
    - In-memory storage for zero cost

    Usage:
        retriever = HybridRetriever()
        retriever.index(documents)
        results = retriever.search("query", top_k=10)
    """

    DEFAULT_WEIGHTS = {"bm25": 0.3, "vector": 0.7}

    def __init__(
        self,
        embedder: Optional[CachedBailianEmbedder] = None,
        weights: dict = None,
        collection_name: str = "research"
    ):
        """
        Args:
            embedder: Bailian embedder instance (creates new if None)
            weights: Fusion weights {"bm25": 0.3, "vector": 0.7}
            collection_name: ChromaDB collection name
        """
        if chromadb is None:
            raise ImportError("chromadb required: pip install chromadb")
        if BM25Okapi is None:
            raise ImportError("rank-bm25 required: pip install rank-bm25")

        # Initialize embedder
        if embedder is None:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key:
                self.embedder = CachedBailianEmbedder(api_key)
            else:
                self.embedder = None
        else:
            self.embedder = embedder

        # Initialize ChromaDB (in-memory)
        self.chroma = chromadb.Client(ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True
        ))
        self.collection_name = collection_name
        self._ensure_collection()

        # BM25 components
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: list[str] = []
        self.doc_ids: list[str] = []

        # Fusion weights
        self.weights = weights or self.DEFAULT_WEIGHTS

    def _ensure_collection(self):
        """Ensure ChromaDB collection exists."""
        try:
            self.collection = self.chroma.get_collection(self.collection_name)
        except Exception:
            self.collection = self.chroma.create_collection(self.collection_name)

    def reset(self):
        """Reset the retriever - clear all indexed data."""
        self.chroma.reset()
        self._ensure_collection()
        self.bm25 = None
        self.corpus = []
        self.doc_ids = []

    def index(self, documents: list[dict], batch_size: int = 100):
        """
        Index documents for hybrid search.

        Args:
            documents: List of dicts with "id", "text", "metadata" keys
            batch_size: Batch size for embedding generation

        Usage:
            retriever.index([
                {"id": "1", "text": "AI is changing", "metadata": {"source": "example.com"}},
                {"id": "2", "text": "ML models improve", "metadata": {"source": "example.org"}},
            ])
        """
        if not documents:
            return

        # Extract texts and prepare ChromaDB data
        texts = [doc["text"] for doc in documents]
        ids = [doc.get("id", str(i)) for i, doc in enumerate(documents)]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        # Store in memory
        self.corpus = texts
        self.doc_ids = ids

        # Build BM25 index (tokenized)
        tokenized = [text.split() for text in texts]
        self.bm25 = BM25Okapi(tokenized)

        # Generate embeddings if embedder available
        if self.embedder:
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.embedder.embed_batch(batch)
                embeddings.extend(batch_embeddings)

            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )

    def add(self, text: str, doc_id: str = None, metadata: dict = None):
        """
        Add a single document to the index.

        Args:
            text: Document text
            doc_id: Optional document ID
            metadata: Optional metadata dict
        """
        if doc_id is None:
            doc_id = str(len(self.corpus))

        # Add to corpus
        self.corpus.append(text)
        self.doc_ids.append(doc_id)

        # Update BM25
        if self.bm25 is None:
            tokenized = [text.split() for text in self.corpus]
            self.bm25 = BM25Okapi(tokenized)
        else:
            self.bm25.add_tokenized([text.split()])

        # Add to ChromaDB
        if self.embedder:
            embedding = self.embedder.embed(text)
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )

    def search(
        self,
        query: str,
        top_k: int = 10,
        weights: dict = None,
        filter_metadata: dict = None
    ) -> list[dict]:
        """
        Hybrid search combining BM25 and vector retrieval.

        Args:
            query: Search query
            top_k: Number of results to return
            weights: Optional fusion weights override
            filter_metadata: Optional ChromaDB metadata filter

        Returns:
            List of result dicts with text, score, metadata
        """
        fusion_weights = weights or self.weights

        results = {"bm25": [], "vector": []}

        # BM25 search
        if self.bm25 and self.corpus:
            bm25_scores = self.bm25.get_scores(query.split())
            bm25_results = sorted(
                enumerate(bm25_scores),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]

            # Normalize BM25 scores to 0-1 range
            max_bm25 = bm25_results[0][1] if bm25_results else 1.0
            if max_bm25 > 0:
                results["bm25"] = [
                    {
                        "idx": idx,
                        "doc_id": self.doc_ids[idx],
                        "text": self.corpus[idx],
                        "bm25_score": score / max_bm25,  # Normalize
                        "raw_bm25": score
                    }
                    for idx, score in bm25_results
                ]

        # Vector search
        if self.embedder and self.collection.count() > 0:
            query_embedding = self.embedder.embed_query(query)
            vector_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )

            if vector_results and vector_results.get("ids"):
                results["vector"] = [
                    {
                        "doc_id": doc_id,
                        "text": doc,
                        "vector_score": 1 - distance,  # Convert distance to similarity
                        "raw_distance": distance,
                        "metadata": meta
                    }
                    for doc_id, doc, distance, meta in zip(
                        vector_results["ids"][0],
                        vector_results["documents"][0],
                        vector_results["distances"][0],
                        vector_results["metadatas"][0] or [None] * len(vector_results["ids"][0])
                    )
                ]

        # Fusion
        fused = self._fuse_results(results, top_k, fusion_weights)

        return fused

    def _fuse_results(
        self,
        results: dict,
        top_k: int,
        weights: dict
    ) -> list[dict]:
        """Fuse BM25 and vector results with weighted scoring."""
        fusion_scores = {}

        bm25_weight = weights.get("bm25", 0.3)
        vector_weight = weights.get("vector", 0.7)

        # Process BM25 results
        for item in results.get("bm25", []):
            doc_id = item["doc_id"]
            score = bm25_weight * item["bm25_score"]
            fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + score

        # Process vector results
        for item in results.get("vector", []):
            doc_id = item["doc_id"]
            score = vector_weight * item["vector_score"]
            fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + score

        # Sort by fusion score
        sorted_results = sorted(
            fusion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # Build final results
        final = []
        for doc_id, fusion_score in sorted_results:
            # Get text from corpus
            try:
                idx = self.doc_ids.index(doc_id)
                text = self.corpus[idx]
            except ValueError:
                # Get from vector results
                vector_item = next(
                    (v for v in results.get("vector", []) if v["doc_id"] == doc_id),
                    None
                )
                text = vector_item["text"] if vector_item else ""

            # Get metadata
            metadata = None
            vector_item = next(
                (v for v in results.get("vector", []) if v["doc_id"] == doc_id),
                None
            )
            if vector_item and vector_item.get("metadata"):
                metadata = vector_item["metadata"]

            final.append({
                "doc_id": doc_id,
                "text": text,
                "score": fusion_score,
                "metadata": metadata
            })

        return final

    def search_bm25_only(self, query: str, top_k: int = 10) -> list[dict]:
        """BM25 only search (keyword matching)."""
        if not self.bm25:
            return []

        scores = self.bm25.get_scores(query.split())
        results = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        return [
            {
                "doc_id": self.doc_ids[idx],
                "text": self.corpus[idx],
                "score": score
            }
            for idx, score in results
        ]

    def search_vector_only(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: dict = None
    ) -> list[dict]:
        """Vector only search (semantic similarity)."""
        if not self.embedder or self.collection.count() == 0:
            return []

        query_embedding = self.embedder.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )

        if not results or not results.get("ids"):
            return []

        return [
            {
                "doc_id": doc_id,
                "text": doc,
                "score": 1 - distance,
                "metadata": meta
            }
            for doc_id, doc, distance, meta in zip(
                results["ids"][0],
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0] or [None] * len(results["ids"][0])
            )
        ]

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "corpus_size": len(self.corpus),
            "doc_ids_count": len(self.doc_ids),
            "chroma_count": self.collection.count() if self.collection else 0,
            "bm25_ready": self.bm25 is not None,
            "embedder_ready": self.embedder is not None,
            "weights": self.weights
        }


# Example usage
if __name__ == "__main__":
    print("=== Hybrid Retriever Test ===\n")

    # Create retriever (will use env API key if available)
    try:
        retriever = HybridRetriever()

        # Sample documents
        docs = [
            {"id": "1", "text": "人工智能正在改变各行各业的工作方式", "metadata": {"source": "tech.com"}},
            {"id": "2", "text": "机器学习算法可以从数据中自动提取模式", "metadata": {"source": "ml.com"}},
            {"id": "3", "text": "深度学习模型在图像识别领域取得突破", "metadata": {"source": "ai.com"}},
            {"id": "4", "text": "自然语言处理技术让人机交互更加自然", "metadata": {"source": "nlp.com"}},
            {"id": "5", "text": "股票市场今天上涨了2个百分点", "metadata": {"source": "finance.com"}},
        ]

        print("Indexing documents...")
        retriever.index(docs)
        print(f"Stats: {retriever.get_stats()}\n")

        # Search
        query = "人工智能 机器学习"
        print(f"Query: {query}\n")

        # Hybrid search
        results = retriever.search(query, top_k=3)
        print("Hybrid Results:")
        for r in results:
            print(f"  Score: {r['score']:.4f} - {r['text'][:50]}...")

        print("\nBM25 Only:")
        results_bm25 = retriever.search_bm25_only(query, top_k=3)
        for r in results_bm25:
            print(f"  Score: {r['score']:.4f} - {r['text'][:50]}...")

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install chromadb rank-bm25 openai")
    except ValueError as e:
        print(f"Config error: {e}")
        print("Set DASHSCOPE_API_KEY in environment")