"""
MiroThinker - Persistent Task Storage

Replaces in-memory dict with SQLite for task persistence across restarts.
Implements proper task state machine: pending -> running -> completed/failed
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

from src.core.config import settings
from src.core.logging_config import logger


DB_PATH = settings.DATA_DIR / "tasks.db"


def _init_db():
    """Initialize SQLite database with tasks table."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            turn_count INTEGER DEFAULT 0,
            elapsed_time REAL DEFAULT 0.0,
            result TEXT,
            error TEXT,
            domain TEXT,
            tier TEXT,
            quality_report TEXT,
            metadata TEXT,
            query TEXT,
            model TEXT,
            temperature REAL,
            max_turns INTEGER,
            context_keep INTEGER,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON tasks(created_at)")
    conn.commit()
    conn.close()
    logger.info(f"Task store initialized at {DB_PATH}")


# Initialize on module load
_init_db()


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def create_task(
    task_id: str,
    query: str,
    model: str = "qwen-plus",
    temperature: float = 0.7,
    max_turns: int = 200,
    context_keep: int = 5,
) -> dict:
    """Create a new task record."""
    now = time.time()
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO tasks (task_id, status, query, model, temperature, max_turns, context_keep, created_at, updated_at)
        VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?)
        """,
        (task_id, query, model, temperature, max_turns, context_keep, now, now),
    )
    conn.commit()
    conn.close()
    return get_task(task_id)


def get_task(task_id: str) -> Optional[dict]:
    """Get task by ID. Returns None if not found."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def update_task(task_id: str, **fields) -> Optional[dict]:
    """Update task fields."""
    allowed = {
        "status", "turn_count", "elapsed_time", "result", "error",
        "domain", "tier", "quality_report", "metadata", "query",
        "model", "temperature", "max_turns", "context_keep",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_task(task_id)

    # Serialize dict/list fields
    for key in ["quality_report", "metadata"]:
        if key in updates and updates[key] is not None:
            updates[key] = json.dumps(updates[key], ensure_ascii=False)

    updates["updated_at"] = time.time()
    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [task_id]

    conn = _get_conn()
    conn.execute(f"UPDATE tasks SET {columns} WHERE task_id = ?", values)
    conn.commit()
    conn.close()
    return get_task(task_id)


def list_tasks(limit: int = 100, status: Optional[str] = None) -> list[dict]:
    """List recent tasks."""
    conn = _get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def cleanup_old_tasks(max_age_hours: float = 24) -> int:
    """Delete tasks older than max_age_hours. Returns deleted count."""
    cutoff = time.time() - (max_age_hours * 3600)
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM tasks WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        logger.info(f"Cleaned up {deleted} old tasks")
    return deleted


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert SQLite row to dict, deserializing JSON fields."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (row[0],))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {}

    result = dict(row)
    for key in ["quality_report", "metadata"]:
        val = result.get(key)
        if val and isinstance(val, str):
            try:
                result[key] = json.loads(val)
            except json.JSONDecodeError:
                pass
    return result
