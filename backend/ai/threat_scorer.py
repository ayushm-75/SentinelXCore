# Combined threat scoring
# backend/ai/threat_scorer.py
"""
Combined threat scorer — merges heuristic + AI scores.
Provides final per-entity threat assessment.
"""
from backend.core.state import state
from backend.core.settings import get_settings


def score_process(pid: int) -> float:
    """Get combined threat score for a process [0.0, 1.0]."""
    proc = state.processes.get(pid)
    if not proc:
        return 0.0
    return round(min(1.0, proc.threat_score), 3)


def score_connection(conn_key: str) -> float:
    """Get threat score for a connection [0.0, 1.0]."""
    conn = state.active_connections.get(conn_key)
    if not conn:
        return 0.0
    return round(min(1.0, conn.threat_score), 3)


def get_system_threat_level() -> dict:
    """
    Aggregate system-wide threat level.
    Returns: {level: "safe|warning|danger|critical", score: float}
    """
    counts = state.alert_count
    crit   = counts.get("critical", 0)
    high   = counts.get("high", 0)
    med    = counts.get("medium", 0)

    score  = min(1.0, (crit * 0.5 + high * 0.2 + med * 0.05))
    score  = round(score, 3)

    if score == 0:
        level = "safe"
    elif score < 0.3:
        level = "warning"
    elif score < 0.7:
        level = "danger"
    else:
        level = "critical"

    return {"level": level, "score": score, "alert_counts": counts}