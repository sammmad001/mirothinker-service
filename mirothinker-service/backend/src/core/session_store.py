"""
MiroThinker - Analysis Session Store

Persists ResearchMemory session snapshots (query → methodology → reasoning → findings)
for future convergence, pattern recognition, and methodology enrichment.

Storage model:
- Each analysis session = one row in analysis_sessions table
- Full snapshot stored as JSONB (query, methodologies, reasoning_log, findings, metrics)
- Indexed by domain, query keywords, created_at for fast retrieval
- Supports similarity search by query embeddings (prepared for future vector extension)
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.config import settings
from src.core.logging_config import logger


DB_PATH = settings.DATA_DIR / "tasks.db"


def _init_session_table():
    """Initialize analysis_sessions table alongside existing tasks table."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)

    # Main sessions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            domain TEXT,
            subtype TEXT,
            tier TEXT,
            status TEXT DEFAULT 'completed',
            thread_count INTEGER DEFAULT 0,
            finding_count INTEGER DEFAULT 0,
            l3_plus_ratio REAL DEFAULT 0.0,
            chain_count INTEGER DEFAULT 0,
            reasoning_turns INTEGER DEFAULT 0,
            overall_depth_score REAL DEFAULT 0.0,
            snapshot TEXT NOT NULL,          -- Full JSON snapshot
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)

    # Indexes for fast retrieval
    conn.execute("CREATE INDEX IF NOT EXISTS idx_as_domain ON analysis_sessions(domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_as_created ON analysis_sessions(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_as_query ON analysis_sessions(query)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_as_depth ON analysis_sessions(overall_depth_score)")

    # Methodology patterns table: extracted from sessions for convergence
    conn.execute("""
        CREATE TABLE IF NOT EXISTS methodology_patterns (
            pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            thread_title TEXT,
            methodology TEXT NOT NULL,
            usage_count INTEGER DEFAULT 1,
            avg_depth_score REAL DEFAULT 0.0,
            first_seen REAL NOT NULL,
            last_seen REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_domain ON methodology_patterns(domain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mp_title ON methodology_patterns(thread_title)")

    conn.commit()
    conn.close()
    logger.info(f"Session store tables initialized at {DB_PATH}")


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


# Initialize on module load
_init_session_table()


def save_session(session_id: str, snapshot: dict) -> dict:
    """Save a complete analysis session snapshot.

    Args:
        session_id: Unique session identifier (e.g., task_id)
        snapshot: Output of ResearchMemory.to_session_snapshot()

    Returns:
        Saved session record as dict
    """
    metrics = snapshot.get("metrics", {})
    now = time.time()

    conn = _get_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO analysis_sessions (
            session_id, query, domain, subtype, tier, status,
            thread_count, finding_count, l3_plus_ratio, chain_count,
            reasoning_turns, overall_depth_score, snapshot, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            snapshot.get("query", "")[:500],
            snapshot.get("domain", ""),
            "",  # subtype: reserved for future
            "",  # tier: reserved for future
            "completed",
            len(snapshot.get("main_threads", [])),
            metrics.get("finding_count", 0),
            metrics.get("l3_plus_ratio", 0.0),
            metrics.get("chain_count", 0),
            metrics.get("reasoning_turns", 0),
            0.0,  # overall_depth_score: updated by caller if available
            json.dumps(snapshot, ensure_ascii=False),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    # Extract and update methodology patterns for convergence
    _update_methodology_patterns(snapshot.get("domain", ""), snapshot)

    logger.info(
        f"Session saved: {session_id}, query='{snapshot.get('query', '')[:40]}', "
        f"findings={metrics.get('finding_count', 0)}, turns={metrics.get('reasoning_turns', 0)}"
    )
    return get_session(session_id)


def get_session(session_id: str) -> Optional[dict]:
    """Get session by ID. Returns None if not found."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM analysis_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return _deserialize_session(dict(row))


def list_sessions(
    domain: Optional[str] = None,
    min_depth_score: float = 0.0,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List analysis sessions with optional filters.

    Args:
        domain: Filter by domain (finance/tech/health/etc.)
        min_depth_score: Only return sessions with depth score >= this
        limit: Max results
        offset: Pagination offset

    Returns:
        List of session dicts (snapshot deserialized)
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row

    conditions = ["overall_depth_score >= ?"]
    params = [min_depth_score]

    if domain:
        conditions.append("domain = ?")
        params.append(domain)

    where_clause = " AND ".join(conditions)
    params.extend([limit, offset])

    rows = conn.execute(
        f"""
        SELECT * FROM analysis_sessions
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params,
    ).fetchall()
    conn.close()
    return [_deserialize_session(dict(r)) for r in rows]


def find_similar_sessions(query_keywords: list[str], domain: Optional[str] = None,
                          limit: int = 10) -> list[dict]:
    """Find sessions whose queries contain any of the given keywords.

    Simple keyword-based similarity. Future: upgrade to vector similarity.
    """
    if not query_keywords:
        return []

    # Build OR conditions for keyword matching
    conditions = []
    params = []
    for kw in query_keywords[:5]:  # Max 5 keywords
        conditions.append("query LIKE ?")
        params.append(f"%{kw}%")

    where_clause = " OR ".join(conditions)

    if domain:
        where_clause = f"({where_clause}) AND domain = ?"
        params.append(domain)

    params.append(limit)

    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""
        SELECT * FROM analysis_sessions
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    conn.close()
    return [_deserialize_session(dict(r)) for r in rows]


def get_methodology_patterns(
    domain: Optional[str] = None,
    min_usage: int = 1,
    limit: int = 20,
) -> list[dict]:
    """Retrieve extracted methodology patterns for convergence.

    Returns frequently used methodologies, sorted by usage count and avg depth score.
    This enables "methodology enrichment" — identifying what analytical approaches
    work best for different types of questions.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row

    conditions = ["usage_count >= ?"]
    params = [min_usage]

    if domain:
        conditions.append("domain = ?")
        params.append(domain)

    where_clause = " AND ".join(conditions)
    params.append(limit)

    rows = conn.execute(
        f"""
        SELECT * FROM methodology_patterns
        WHERE {where_clause}
        ORDER BY usage_count DESC, avg_depth_score DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_stats(domain: Optional[str] = None) -> dict:
    """Get aggregate statistics for analysis sessions.

    Useful for monitoring system performance and depth trends over time.
    """
    conn = _get_conn()

    domain_filter = "WHERE domain = ?" if domain else ""
    params = [domain] if domain else []

    row = conn.execute(
        f"""
        SELECT
            COUNT(*) as total_sessions,
            AVG(finding_count) as avg_findings,
            AVG(l3_plus_ratio) as avg_l3_ratio,
            AVG(chain_count) as avg_chains,
            AVG(reasoning_turns) as avg_turns,
            MAX(created_at) as latest_session
        FROM analysis_sessions
        {domain_filter}
        """,
        params,
    ).fetchone()
    conn.close()

    return {
        "total_sessions": row[0] or 0,
        "avg_findings": round(row[1] or 0, 2),
        "avg_l3_ratio": round(row[2] or 0, 3),
        "avg_chains": round(row[3] or 0, 2),
        "avg_turns": round(row[4] or 0, 2),
        "latest_session": datetime.fromtimestamp(row[5]).isoformat() if row[5] else None,
    }


def cleanup_old_sessions(max_age_days: float = 30) -> int:
    """Delete sessions older than max_age_days. Returns deleted count."""
    cutoff = time.time() - (max_age_days * 86400)
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM analysis_sessions WHERE created_at < ?", (cutoff,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        logger.info(f"Cleaned up {deleted} old analysis sessions")
    return deleted


# === Internal helpers ===


def _deserialize_session(row: dict) -> dict:
    """Deserialize a session row, parsing the JSON snapshot."""
    snapshot_json = row.get("snapshot", "{}")
    if isinstance(snapshot_json, str):
        try:
            row["snapshot"] = json.loads(snapshot_json)
        except json.JSONDecodeError:
            row["snapshot"] = {}
    return row


def _update_methodology_patterns(domain: str, snapshot: dict):
    """Extract methodology patterns from a session and update the patterns table.

    This is the core of "methodology convergence" — tracking which analytical
    approaches are used most frequently and how effective they are.
    """
    thread_methodologies = snapshot.get("thread_methodologies", {})
    if not thread_methodologies:
        return

    metrics = snapshot.get("metrics", {})
    depth_score = metrics.get("l3_plus_ratio", 0.0)
    now = time.time()

    conn = _get_conn()
    for thread_title, methodology in thread_methodologies.items():
        if not methodology or len(methodology) < 10:
            continue

        # Check if this exact methodology already exists
        existing = conn.execute(
            "SELECT pattern_id, usage_count, avg_depth_score FROM methodology_patterns "
            "WHERE domain = ? AND thread_title = ? AND methodology = ?",
            (domain, thread_title[:100], methodology[:500]),
        ).fetchone()

        if existing:
            # Update existing pattern
            pid, old_count, old_score = existing
            new_count = old_count + 1
            new_score = (old_score * old_count + depth_score) / new_count
            conn.execute(
                "UPDATE methodology_patterns SET usage_count = ?, avg_depth_score = ?, "
                "last_seen = ? WHERE pattern_id = ?",
                (new_count, round(new_score, 3), now, pid),
            )
        else:
            # Insert new pattern
            conn.execute(
                "INSERT INTO methodology_patterns (domain, thread_title, methodology, "
                "usage_count, avg_depth_score, first_seen, last_seen) "
                "VALUES (?, ?, ?, 1, ?, ?, ?)",
                (domain, thread_title[:100], methodology[:500], round(depth_score, 3), now, now),
            )

    conn.commit()
    conn.close()
