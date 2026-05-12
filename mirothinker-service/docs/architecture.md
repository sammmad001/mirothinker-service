# Architecture

MiroThinker Online Service architecture documentation.

## System Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Browser   │─────>│  Nginx       │─────>│  FastAPI App    │
│   (SPA)     │<─────│  (Reverse    │<─────│  (Research      │
│             │      │   Proxy)     │      │   Agent)        │
└─────────────┘      └──────────────┘      └─────────────────┘
                                                   │
                                    ┌──────────────┴──────────────┐
                                    │                              │
                            ┌───────▼──────┐            ┌─────────▼────────┐
                            │  DuckDuckGo  │            │  Alibaba Bailian │
                            │  (Search)    │            │  LLM (qwen)      │
                            └──────────────┘            └──────────────────┘
                                    │
                            ┌───────▼──────┐
                            │ Trafilatura  │
                            │ (Scraping)   │
                            └──────────────┘
```

## Component Architecture

### Backend Structure

```
backend/
├── src/
│   ├── core/              # Core infrastructure
│   │   ├── config.py      # - Environment configuration
│   │   └── logging_config.py  # - Structured logging
│   │
│   ├── routes/            # API layer
│   │   └── research.py    # - Research endpoints
│   │                      # - Task management
│   │                      # - Status polling
│   │
│   ├── services/          # Business logic
│   │   ├── agent.py       # - ResearchAgent core
│   │   │                  # - AgentState management
│   │   │                  # - Tier routing
│   │   │                  # - Tool execution
│   │   │
│   │   ├── quality.py     # - FixedChannelSearch
│   │   │                  # - SourceCredibilityScorer
│   │   │                  # - ContradictionDetector
│   │   │                  # - QualityCheckPipeline
│   │   │
│   │   └── search.py      # - ToolClient
│   │                      # - DuckDuckGo integration
│   │                      # - Trafilatura scraping
│   │
│   ├── utils/             # Utilities
│   │
│   └── main.py            # Application entry point
│                          # - FastAPI app setup
│                          # - Middleware configuration
│                          # - Route registration
│
└── tests/                 # Test suite
    ├── conftest.py        # Test fixtures
    ├── test_api.py        # API endpoint tests
    ├── test_config.py     # Configuration tests
    └── test_quality.py    # Quality module tests
```

## Data Flow

### Research Task Flow

```
1. Client Request
   └─> POST /api/research
       └─> Create task_id
           └─> Background task started

2. Tier Classification
   └─> classify_query(query)
       └─> qwen-flash classifies to TIER_1/2/3
           └─> Adjust max_turns accordingly

3. Domain Detection
   └─> detect_domain(query)
       └─> Returns: tech/finance/health/general
           └─> Build domain-specific system prompt

4. Research Loop
   └─> while turn < max_turns:
       ├─> Get context window
       ├─> Call LLM (qwen-plus)
       ├─> Check for "FINAL ANSWER:"
       │   └─> If found: Extract result, run quality checks, return
       │
       ├─> Parse tool calls
       │   ├─> google_search(query)
       │   │   └─> DuckDuckGo search
       │   │       └─> Score sources credibility
       │   │
       │   └─> scrape_webpage(url)
       │       └─> Trafilatura extract
       │
       ├─> Check early stopping
       │   ├─> Source saturation (>=25 sources)
       │   └─> Consecutive no-tool calls (>=3)
       │
       └─> Continue loop

5. Quality Checks
   └─> QualityCheckPipeline.run(result, metadata)
       ├─> Source count check
       ├─> Citation completeness
       ├─> Data support
       ├─> Contradiction handling
       ├─> Structure completeness
       └─> Language quality

6. Return Result
   └─> Update task_results dict
       └─> Client polls GET /api/research/{task_id}
```

## Key Design Patterns

### 1. Agent State Management

The `AgentState` class maintains conversation history with optimization:
- System prompt always retained
- User query preserved
- Last K tool/assistant messages kept (configurable)
- Tool results compressed to 500 chars

### 2. Tier Routing Strategy

| Tier | Use Case | Max Turns | Model | Cost |
|------|----------|-----------|-------|------|
| TIER_1 | Factual questions | 5 | qwen-flash | ~50 Credits |
| TIER_2 | Medium analysis | 50 | qwen-plus | ~500 Credits |
| TIER_3 | Deep research | 125 | qwen-plus | ~600 Credits |

### 3. Quality Enhancement

**Fixed Channel Search:**
- L1: Core sources (academic, tech, news, data)
- L2: Extended sources (domain-specific)
- L3: General search fallback

**Credibility Scoring:**
- Base weight (source reputation): 40%
- Content quality (data, citations, length): 30%
- Recency (publication date): 15%
- Citation integrity (references): 15%

**Contradiction Detection:**
- Numeric conflicts (>20% difference)
- Qualitative conflicts (opposition words)

### 4. Concurrency Control

```python
research_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def _run_research(task_id, req):
    async with research_semaphore:
        # Only MAX_CONCURRENT_TASKS run simultaneously
        # Others wait in queue
```

## Configuration Layers

```
1. pydantic-settings (config.py)
   └─> Loads from environment variables
       └─> Falls back to .env file
           └─> Uses defaults if not set

2. Docker environment
   └─> docker-compose.yml env_file
       └─> .env file on server

3. Application defaults
   └─> pyproject.toml
       └─> Dockerfile CMD
```

## Deployment Architecture

### Docker Containers

```
┌──────────────────────────────────────┐
│  Docker Host (2GB RAM)               │
│                                      │
│  ┌────────────────┐  ┌────────────┐ │
│  │  Nginx         │  │  FastAPI   │ │
│  │  (256MB limit) │  │  (1536MB)  │ │
│  │                │  │            │ │
│  │  Port 80/443   │─>│  Port 8000 │ │
│  └────────────────┘  └────────────┘ │
│                            │         │
│  ┌─────────────────────────▼──────┐ │
│  │  Volumes                       │ │
│  │  - data/traces                 │ │
│  │  - data/logs                   │ │
│  │  - data/cache                  │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### Network Flow

```
Internet
  └─> Port 80/443 (Nginx)
      ├─> Static files (/static, /)
      └─> Reverse proxy (/api/*)
          └─> FastAPI app:8000
              └─> External APIs
                  ├─> DashScope (LLM)
                  └─> DuckDuckGo (Search)
```

## Error Handling

### API Layer
- HTTPException for client errors (4xx)
- Background task errors captured and stored in task_results
- Health check endpoint for monitoring

### Agent Layer
- LLM API errors raise Exception
- Tool errors return error message instead of raising
- Network timeouts configured (120s for LLM, 30s for classification)

### Quality Layer
- Graceful degradation if quality modules fail
- Quality report optional (can be disabled)
- Contradiction detection non-blocking

## Performance Considerations

### Token Optimization
- Context compression: ~40% reduction
- Compact search results: ~50% token savings
- Tool result truncation: 1000 chars max

### Memory Management
- Single worker process (2GB server)
- Concurrency limit prevents memory spikes
- Log rotation prevents disk space exhaustion

### Response Times
- Tier classification: ~2 seconds
- Per research turn: ~5-15 seconds
- Total research: 30 seconds to 10 minutes
