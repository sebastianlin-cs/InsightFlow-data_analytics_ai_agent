from __future__ import annotations

from typing import Any

from app.agent.code_execution.schemas import CodeGenerationResult, DebugRepairResult
from app.agent.llm_client import BaseLLMClient


def generate_analysis_code(
    *,
    llm_client: BaseLLMClient,
    user_query: str,
    dataset_schema: list[dict[str, Any]],
    analysis_plan: list[str],
) -> CodeGenerationResult:
    """Generate analyze(df) code through the configured LLM client."""
    raw = llm_client.generate_code(
        user_query=user_query,
        dataset_schema=dataset_schema,
        analysis_plan=analysis_plan,
    )
    return {
        "code": _require_string(raw, "code"),
        "explanation": str(raw.get("explanation") or ""),
        "columns_used": _string_list(raw.get("columns_used")),
        "expected_result_keys": _string_list(raw.get("expected_result_keys")),
        "error": None,
    }


def repair_analysis_code(
    *,
    llm_client: BaseLLMClient,
    user_query: str,
    dataset_schema: list[dict[str, Any]],
    analysis_plan: list[str],
    previous_code: str,
    execution_error: str | None,
    stderr: str,
    retry_count: int,
    max_retries: int,
) -> DebugRepairResult:
    """Generate one repaired analyze(df) function through the configured LLM client."""
    raw = llm_client.repair_code(
        user_query=user_query,
        dataset_schema=dataset_schema,
        analysis_plan=analysis_plan,
        previous_code=previous_code,
        execution_error=execution_error,
        stderr=stderr,
        retry_count=retry_count,
        max_retries=max_retries,
    )
    return {
        "code": _require_string(raw, "code"),
        "repair_explanation": str(raw.get("repair_explanation") or ""),
        "changed_columns": raw.get("changed_columns")
        if isinstance(raw.get("changed_columns"), dict)
        else {"removed": [], "added": []},
        "columns_used": _string_list(raw.get("columns_used")),
        "expected_result_keys": _string_list(raw.get("expected_result_keys")),
        "error": None,
    }


def _require_string(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"LLM code response missing required string field: {key}")
    return value


def _string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
