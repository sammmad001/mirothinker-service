# API Reference

Complete API documentation for MiroThinker Online Service.

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication required for local deployment. Add authentication middleware for production.

---

## Endpoints

### 1. Serve Frontend

```http
GET /
```

Returns the frontend single-page application (index.html).

**Response:**
- Content-Type: `text/html`
- Status: `200 OK`

---

### 2. Create Research Task

```http
POST /api/research
```

Creates a new research task and starts background processing.

**Request Body:**
```json
{
  "query": "string (required)",
  "max_turns": "integer (default: 200)",
  "context_keep": "integer (default: 5)",
  "model": "string (default: qwen-plus)",
  "temperature": "float (default: 0.7)"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Research question or topic |
| max_turns | int | No | 200 | Maximum research iterations |
| context_keep | int | No | 5 | Number of recent turns to keep in context |
| model | string | No | qwen-plus | LLM model to use (qwen-flash, qwen-turbo, qwen-plus, qwen-max) |
| temperature | float | No | 0.7 | Creativity (0.0-1.0) |

**Response:**
```json
{
  "task_id": "a1b2c3d4",
  "status": "running",
  "turn_count": 0,
  "elapsed_time": 0.0,
  "result": null,
  "error": null,
  "domain": null,
  "quality_report": null,
  "metadata": null
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest trends in renewable energy?",
    "max_turns": 50,
    "model": "qwen-plus",
    "temperature": 0.7
  }'
```

---

### 3. Get Research Status

```http
GET /api/research/{task_id}
```

Retrieves the status and results of a research task.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| task_id | string | Task ID returned from create endpoint |

**Response (Running):**
```json
{
  "task_id": "a1b2c3d4",
  "status": "running",
  "turn_count": 12,
  "elapsed_time": 45.2,
  "result": null,
  "error": null,
  "domain": "tech",
  "quality_report": null,
  "metadata": null
}
```

**Response (Completed):**
```json
{
  "task_id": "a1b2c3d4",
  "status": "completed",
  "turn_count": 25,
  "elapsed_time": 120.5,
  "result": "# Renewable Energy Trends\n\n## Executive Summary...\n\n## Sources\n- https://...",
  "error": null,
  "domain": "tech",
  "quality_report": {
    "overall_score": 0.85,
    "passed": true,
    "scores": {
      "_check_source_count": 1.0,
      "_check_citation_completeness": 0.8,
      "_check_data_support": 0.9,
      "_check_contradictions": 0.7,
      "_check_structure": 1.0,
      "_check_language_quality": 0.8
    },
    "issues": [],
    "recommendation": "Excellent quality, ready for delivery"
  },
  "metadata": {
    "query": "What are the latest trends in renewable energy?",
    "domain": "tech",
    "sources": [
      {
        "url": "https://example.com/article",
        "title": "Renewable Energy Report",
        "credibility_score": 0.85,
        "credibility_level": "A (Authoritative)"
      }
    ],
    "claims": []
  }
}
```

**Response (Failed):**
```json
{
  "task_id": "a1b2c3d4",
  "status": "failed",
  "turn_count": 3,
  "elapsed_time": 15.2,
  "result": null,
  "error": "LLM API error: 401 - Invalid API key",
  "domain": null,
  "quality_report": null,
  "metadata": null
}
```

**Example:**
```bash
curl http://localhost:8000/api/research/a1b2c3d4
```

---

### 4. Health Check

```http
GET /api/health
```

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "dashscope_configured": true,
  "search_available": true,
  "scrape_available": true,
  "serper_configured": false,
  "jina_configured": false,
  "concurrency": {
    "max": 2,
    "available": 2
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

---

### 5. System Status

```http
GET /api/status
```

Returns detailed system status including resource usage.

**Response:**
```json
{
  "service": "MiroThinker Online Service",
  "version": "1.0.0",
  "memory": {
    "rss_mb": 245.6,
    "vms_mb": 512.3
  },
  "concurrency": {
    "max_concurrent_tasks": 2,
    "current_running": 1,
    "available_slots": 1
  },
  "tasks": {
    "total": 15,
    "running": 1,
    "completed": 12,
    "failed": 2
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/status
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Models

### ResearchRequest
```python
class ResearchRequest(BaseModel):
    query: str                          # Research question
    max_turns: int = 200               # Maximum research iterations
    context_keep: int = 5              # Context window size
    model: str = "qwen-plus"           # LLM model name
    temperature: float = 0.7           # Temperature (0.0-1.0)
```

### TaskResponse
```python
class TaskResponse(BaseModel):
    task_id: str                        # Unique task identifier
    status: str                         # running, completed, failed, queued
    turn_count: int = 0                # Number of research turns
    elapsed_time: float = 0.0          # Time since task start (seconds)
    result: Optional[str] = None       # Research result (markdown)
    error: Optional[str] = None        # Error message if failed
    domain: Optional[str] = None       # Detected domain
    quality_report: Optional[dict] = None  # Quality check results
    metadata: Optional[dict] = None    # Research metadata
```

### QualityReport
```python
class QualityReport:
    overall_score: float               # Overall quality score (0.0-1.0)
    passed: bool                       # Whether quality threshold met
    scores: dict                       # Individual check scores
    issues: list[str]                  # List of quality issues
    recommendation: str                # Human-readable recommendation
```

---

## Rate Limiting

No rate limiting configured by default. Add middleware for production:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/research")
@limiter.limit("10/minute")
async def create_research_task(request: Request, req: ResearchRequest):
    ...
```

---

## WebSocket (Future)

Real-time updates via WebSocket planned for future release.

```javascript
// Planned API
const ws = new WebSocket('ws://localhost:8000/ws/research/{task_id}');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update.status, update.turn_count);
};
```

---

## CORS

CORS is enabled for all origins by default. Restrict for production:

```python
# In .env
CORS_ORIGINS=["https://your-domain.com", "https://www.your-domain.com"]
```

---

## Best Practices

1. **Polling Interval**: Poll task status every 2-5 seconds
2. **Timeout**: Set client timeout to 10 minutes for deep research
3. **Error Handling**: Always check `status` field before accessing `result`
4. **Model Selection**: Use `qwen-flash` for simple queries, `qwen-plus` for complex research
5. **Context Keep**: Lower values (3-5) for memory-constrained environments
