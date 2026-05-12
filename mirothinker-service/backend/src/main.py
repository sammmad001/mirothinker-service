"""
MiroThinker Online Service - FastAPI Backend
Integrates Alibaba Bailian LLM with MCP tools for deep research.
Modular architecture with quality enhancement.
"""

from pathlib import Path
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.core.config import settings
from src.core.logging_config import logger, setup_logging
from src.routes.research import router as research_router
from src.routes.feishu import router as feishu_router

# Ensure data directories exist
settings.ensure_directories()

# Setup logging with file output
log_file = settings.LOGS_DIR / "mirothinker.log"
logger = setup_logging(log_file=log_file)

# App Setup
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
frontend_dir = Path(settings.FRONTEND_DIR)
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# Include routers
app.include_router(research_router, prefix="/api", tags=["research"])
app.include_router(feishu_router, tags=["feishu"])  # Already has /api/v1/feishu prefix


# Root endpoint - serve frontend
@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html."""
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "MiroThinker API - No frontend available"}


# Health Check
@app.get("/api/health")
async def health_check():
    from src.routes.research import research_semaphore

    return {
        "status": "healthy",
        "dashscope_configured": settings.validate_api_key(),
        "search_available": True,  # DuckDuckGo free, no API key needed
        "scrape_available": True,  # Trafilatura free, no API key needed
        "serper_configured": bool(settings.SERPER_API_KEY),  # Optional, backward compatible
        "jina_configured": bool(settings.JINA_API_KEY),      # Optional, backward compatible
        "feishu_configured": settings.validate_feishu_config(),  # Feishu bot status
        "concurrency": {
            "max": settings.MAX_CONCURRENT_TASKS,
            "available": research_semaphore._value if hasattr(research_semaphore, '_value') else "N/A",
        },
    }


# System Status
@app.get("/api/status")
async def system_status():
    """Get detailed system status including resource usage."""
    from src.routes.research import research_semaphore, task_results

    # Get process memory info
    try:
        import psutil
        process = psutil.Process(__import__("os").getpid())
        memory_info = {
            "rss_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "vms_mb": round(process.memory_info().vms / 1024 / 1024, 2),
        }
    except ImportError:
        memory_info = {"note": "psutil not installed, install with: pip install psutil"}

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "memory": memory_info,
        "concurrency": {
            "max_concurrent_tasks": settings.MAX_CONCURRENT_TASKS,
            "current_running": settings.MAX_CONCURRENT_TASKS - (research_semaphore._value if hasattr(research_semaphore, '_value') else 0),
            "available_slots": research_semaphore._value if hasattr(research_semaphore, '_value') else "N/A",
        },
        "tasks": {
            "total": len(task_results),
            "running": sum(1 for t in task_results.values() if t["status"] == "running"),
            "completed": sum(1 for t in task_results.values() if t["status"] == "completed"),
            "failed": sum(1 for t in task_results.values() if t["status"] == "failed"),
        },
    }


# Entry point
def start():
    """Start the uvicorn server."""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    start()
