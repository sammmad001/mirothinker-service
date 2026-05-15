"""MiroThinker - Services Module"""

# Core existing services
from .quality import (
    ContradictionDetector,
    FixedChannelSearch,
    QualityCheckPipeline,
    SourceCredibilityScorer,
)
from .search import ToolClient, SearchCache, DateExtractor
from .agent import AgentState, ResearchAgent

# Phase 0: Zero-cost enhancements
from .url_validator import URLValidator, quick_check_url, quick_check_urls
from .citation_manager import CitationManager, Citation, InlineCitationBuilder
from .recency import RecencyScorer, DataCurrencyFormatter
from .contradiction import (
    EnhancedContradictionDetector,
    Conflict,
    ConflictType,
)
from .citation_integration import (
    CitationIntegration,
    CitationTracker,
    ResearchOutputFormatter,
)
from .incremental_research import (
    IncrementalResearchTracker,
    ResearchChangeNotifier,
    ContentChange,
    ResearchSnapshot,
)

# Phase 1: Bailian + RAG
from .embedding import (
    BailianEmbedder,
    CachedBailianEmbedder,
    EmbeddingCache,
)
from .hybrid_retrieval import HybridRetriever

# Phase 1-2: Bailian fact checking
from .fact_checker import (
    BailianFactChecker,
    VerificationResult,
    VerificationStatus,
    InlineFactChecker,
)

# Phase 2: Knowledge graph
from .knowledge_graph import (
    KnowledgeGraph,
    Entity,
    Relation,
    EntityType,
    RelationType,
)
from .entity_extractor import (
    BailianEntityExtractor,
    EntityExtractorWithMemory,
)
from .research_memory_enhanced import ResearchMemoryEnhanced

# Quality enhancement
from .quality_enhancement import (
    QualityEnhancer,
    QualityReportBuilder,
)

__all__ = [
    # Core services
    "ContradictionDetector",
    "FixedChannelSearch",
    "QualityCheckPipeline",
    "SourceCredibilityScorer",
    "ToolClient",
    "SearchCache",
    "DateExtractor",
    "AgentState",
    "ResearchAgent",

    # Phase 0: Zero-cost
    "URLValidator",
    "quick_check_url",
    "quick_check_urls",
    "CitationManager",
    "Citation",
    "InlineCitationBuilder",
    "RecencyScorer",
    "DataCurrencyFormatter",
    "EnhancedContradictionDetector",
    "Conflict",
    "ConflictType",
    "CitationIntegration",
    "CitationTracker",
    "ResearchOutputFormatter",
    "IncrementalResearchTracker",
    "ResearchChangeNotifier",
    "ContentChange",
    "ResearchSnapshot",

    # Phase 1: Bailian + RAG
    "BailianEmbedder",
    "CachedBailianEmbedder",
    "EmbeddingCache",
    "HybridRetriever",

    # Phase 1-2: Fact checking
    "BailianFactChecker",
    "VerificationResult",
    "VerificationStatus",
    "InlineFactChecker",

    # Phase 2: Knowledge graph
    "KnowledgeGraph",
    "Entity",
    "Relation",
    "EntityType",
    "RelationType",
    "BailianEntityExtractor",
    "EntityExtractorWithMemory",
    "ResearchMemoryEnhanced",

    # Quality enhancement
    "QualityEnhancer",
    "QualityReportBuilder",
]