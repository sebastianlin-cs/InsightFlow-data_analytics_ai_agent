from __future__ import annotations

from typing import Any

from app.agent.code_execution.schemas import CodeExecutionResult


def normalize_execution_payload(
    payload: dict[str, Any],
    *,
    stdout: str = "",
    stderr: str = "",
    execution_time_ms: int = 0,
) -> CodeExecutionResult:
    """Normalize child-process result payload into the public execution result shape."""
    return {
        "status": payload.get("status", "success"),
        "answer": payload.get("answer"),
        "tables": payload.get("tables") if isinstance(payload.get("tables"), dict) else {},
        "charts": payload.get("charts") if isinstance(payload.get("charts"), list) else [],
        "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        "stdout": stdout,
        "stderr": stderr,
        "error": payload.get("error"),
        "execution_time_ms": execution_time_ms,
    }
