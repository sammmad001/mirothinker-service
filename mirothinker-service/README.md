# MiroThinker Online Service

Deep research agent powered by Alibaba Bailian LLM with MCP tools. Provides automated multi-turn research with quality enhancement, source credibility scoring, and contradiction detection.

## Features

- **Deep Research**: Multi-turn autonomous research with intelligent tool usage (search + scrape)
- **Quality Enhancement**: Fixed channel search, source credibility scoring, contradiction detection
- **Tier Routing**: Automatic query classification (TIER_1/2/3) for cost optimization
- **Smart Early Stopping**: Information saturation detection to prevent over-researching
- **Context Management**: Recency-based context window with compression for token efficiency
- **Free Search Tools**: DuckDuckGo + Trafilatura (zero API cost)
- **RESTful API**: FastAPI backend with async support
- **Web Interface**: Vanilla HTML/CSS/JS frontend
- **Docker Deployment**: Multi-stage builds optimized for 2GB memory servers

## Quick Start

### Prerequisites

- Python 3.10+
- Alibaba Bailian API key ([Get API Key](https://bailian.console.aliyun.com/))

### Local Development

```bash
# 1. Clone repository
git clone <repository-url>
cd mirothinker-service

# 2. Setup environment
./scripts/setup.sh

# 3. Configure API key
cp .env.example .env
# Edit .env and add your DASHSCOPE_API_KEY

# 4. Start development server
make run
# Or: ./scripts/start.sh dev

# 5. Visit http://localhost:8000
```

### Docker Deployment

```bash
# Build and start
make docker-up
# Or: docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f app
```

### Production Deployment

```bash
# Deploy to remote server
./scripts/deploy.sh

# Requires:
# - REMOTE_HOST environment variable
# - SSH key configured
# - .env.production file
```

## Project Structure

```
mirothinker-service/
├── backend/
│   ├── src/
│   │   ├── core/           # Configuration and logging
│   │   │   ├── config.py
│   │   │   └── logging_config.py
│   │   ├── routes/         # API endpoints
│   │   │   └── research.py
│   │   ├── services/       # Business logic
│   │   │   ├── agent.py    # Research agent core
│   │   │   ├── quality.py  # Quality enhancement modules
│   │   │   └── search.py   # Search and scraping tools
│   │   ├── utils/          # Utilities
│   │   └── main.py         # Application entry point
│   ├── tests/              # Test suite
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_config.py
│   │   └── test_quality.py
│   └── requirements.txt
├── frontend/               # Web interface
│   ├── index.html
│   └── static/
│       ├── css/
│       └── js/
├── scripts/                # Engineering scripts
│   ├── setup.sh            # Environment setup
│   ├── start.sh            # Application start
│   ├── deploy.sh           # Production deployment
│   └── backup.sh           # Data backup
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD pipeline
│   └── ci.yml
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Docker orchestration
├── docker-compose.prod.yml # Production configuration
├── pyproject.toml          # Project metadata
├── Makefile                # Build commands
└── .env.example            # Environment template
```

## API Documentation

### Create Research Task

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the impact of AI on healthcare?",
    "max_turns": 50,
    "context_keep": 5,
    "model": "qwen-plus",
    "temperature": 0.7
  }'
```

Response:
```json
{
  "task_id": "a1b2c3d4",
  "status": "running"
}
```

### Get Task Status

```bash
curl http://localhost:8000/api/research/a1b2c3d4
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

### System Status

```bash
curl http://localhost:8000/api/status
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHSCOPE_API_KEY` | - | Alibaba Bailian API key (required) |
| `DEFAULT_MODEL` | `qwen-plus` | Default LLM model |
| `DEFAULT_MAX_TURNS` | `200` | Maximum research turns |
| `MAX_CONCURRENT_TASKS` | `2` | Max concurrent research tasks |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `WORKERS` | `1` | Number of uvicorn workers |

## Development

### Running Tests

```bash
make test
# Or: pytest backend/tests -v
```

### Code Linting

```bash
make lint
# Or: ruff check backend/src backend/tests
```

### Code Formatting

```bash
make format
# Or: ruff format backend/src backend/tests
```

### Test Coverage

```bash
make test-cov
# Or: pytest backend/tests --cov=backend/src --cov-report=html
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

- **Test**: Runs on every push/PR (Python 3.10, 3.11, 3.12)
- **Build**: Builds and pushes Docker image to GHCR
- **Deploy**: Deploys to production on main branch push

## Cost Optimization

MiroThinker uses a tier-based routing system to minimize costs:

| Tier | Type | Max Turns | Estimated Cost |
|------|------|-----------|----------------|
| TIER_1 | Simple factual | 5 | ~50 Credits |
| TIER_2 | Medium analysis | 50 | ~500 Credits |
| TIER_3 | Deep research | 125 | ~600 Credits |

With Bailian's ¥198/month package (100K Credits), you can perform approximately 166-2000 research tasks per month.

## License

MIT

## Support

- Documentation: See `docs/` directory
- Issues: Create a GitHub issue
- Email: [your-email@example.com]
