"""
MiroThinker - Research API Routes
Handles research task creation, status checking, and execution.
"""

import asyncio
import time
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.core.config import settings
from src.core.logging_config import logger
from src.services.agent import ResearchAgent, classify_query

router = APIRouter()

# Task storage
task_results: dict = {}

# Concurrency control
research_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)


# Request/Response Models
class ResearchRequest(BaseModel):
    query: str
    max_turns: int = 200
    context_keep: int = 5
    model: str = "qwen-plus"
    temperature: float = 0.7


class TaskResponse(BaseModel):
    task_id: str
    status: str = "running"
    turn_count: int = 0
    elapsed_time: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None
    domain: Optional[str] = None
    quality_report: Optional[dict] = None
    metadata: Optional[dict] = None


@router.post("/research", response_model=TaskResponse)
async def create_research_task(req: ResearchRequest):
    """Create a new research task."""
    task_id = str(uuid.uuid4())[:8]
    task_results[task_id] = {
        "status": "running",
        "turn_count": 0,
        "elapsed_time": 0.0,
        "result": None,
        "error": None,
        "start_time": time.time(),
    }

    # Run research in background
    asyncio.create_task(_run_research(task_id, req))

    return TaskResponse(task_id=task_id)


@router.get("/research/{task_id}", response_model=TaskResponse)
async def get_research_status(task_id: str):
    """Get research task status."""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_results[task_id]

    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        turn_count=task.get("turn_count", 0),
        elapsed_time=round(time.time() - task["start_time"], 2) if task["start_time"] else 0,
        result=task["result"],
        error=task["error"],
        domain=task.get("domain"),
        quality_report=task.get("quality_report"),
        metadata=task.get("metadata"),
    )


async def _run_research(task_id: str, req: ResearchRequest):
    """Background task to run research with concurrency control and Tier routing."""
    async with research_semaphore:
        # Update status to queued if semaphore is locked
        if research_semaphore.locked():
            task_results[task_id]["status"] = "queued"

        try:
            if not settings.validate_api_key():
                raise ValueError("DASHSCOPE_API_KEY not configured")

            # Tier routing: classify query first
            tier = await classify_query(req.query)
            task_results[task_id]["tier"] = tier

            # Define progress callback to update turn count in real-time
            def update_progress(turn: int, elapsed: float):
                task_results[task_id]["turn_count"] = turn
                task_results[task_id]["elapsed_time"] = elapsed

            # Enable quality enhancement by default
            agent = ResearchAgent(enable_quality_enhancement=True)
            result = await agent.run(
                query=req.query,
                max_turns=req.max_turns,
                context_keep=req.context_keep,
                model=req.model,
                temperature=req.temperature,
                tier=tier,
                progress_callback=update_progress,
            )

            task_results[task_id].update({
                "status": "completed",
                "turn_count": result["turn_count"],
                "elapsed_time": result["elapsed_time"],
                "result": result["result"],
                "domain": result.get("domain", "general"),
                "quality_report": result.get("quality_report"),
                "metadata": result.get("metadata"),
            })

            logger.info(f"Task {task_id} completed: tier={tier}, turns={result['turn_count']}")

        except Exception as e:
            task_results[task_id].update({
                "status": "failed",
                "error": str(e),
            })
            logger.error(f"Task {task_id} failed: {e}")
