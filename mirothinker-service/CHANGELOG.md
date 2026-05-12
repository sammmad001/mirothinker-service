# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-12

### Added

#### Core Features
- Deep research agent with multi-turn autonomous research
- Tier-based query routing (TIER_1/2/3) for cost optimization
- Intelligent early stopping with information saturation detection
- Context management with recency-based window and compression
- Fixed channel search with priority-based sources (L1/L2/L3)
- Source credibility scoring system (A/B/C/D levels)
- Contradiction detection (numeric and qualitative)
- Quality check pipeline with 6 validation checks
- Domain auto-detection (tech, finance, health, general)

#### API
- FastAPI backend with async support
- RESTful endpoints for research tasks
- Health check and system status endpoints
- CORS middleware support
- Static file serving for frontend

#### Frontend
- Vanilla HTML/CSS/JS single-page application
- Real-time task status polling
- Research result display with markdown rendering

#### Infrastructure
- Docker multi-stage builds
- Docker Compose orchestration (Nginx + FastAPI)
- Production configuration optimized for 2GB memory
- CI/CD pipeline with GitHub Actions
- Automated testing with pytest
- Code linting with Ruff
- Environment configuration with pydantic-settings

#### Documentation
- Comprehensive README with API examples
- Architecture documentation
- Deployment guides
- Configuration reference

### Technical Details

#### Technology Stack
- **Backend**: FastAPI, Python 3.10+
- **LLM**: Alibaba Bailian (qwen-plus, qwen-flash)
- **Search**: DuckDuckGo (ddgs package)
- **Scraping**: Trafilatura
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: Docker, Docker Compose, Nginx

#### Architecture
- Modular backend structure:
  - `src/core/` - Configuration and logging
  - `src/routes/` - API endpoints
  - `src/services/` - Business logic (agent, quality, search)
  - `src/utils/` - Utilities

#### Performance
- Token-optimized context management (~40% reduction)
- Compact search result formatting (~50% token savings)
- Concurrency control with semaphores
- Memory-optimized for 2GB servers

#### Cost
- Free search tools (DuckDuckGo + Trafilatura)
- Tier routing: ¥198/month enables ~166-2000 research tasks
- Weighted average: ~303 Credits per research

---

## [Unreleased]

### Planned
- User authentication and task history
- Export research results (PDF, Markdown)
- Custom domain support
- Rate limiting improvements
- Monitoring and alerting integration
- WebSocket support for real-time updates
