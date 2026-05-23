from __future__ import annotations

from typing import Any, Literal, TypedDict


ExecutionMode = Literal["fixed_tool", "generated_code"]
ExecutionStatus = Literal["success", "error", "timeout", "blocked"]


class CodeGenerationResult(TypedDict, total=False):
    code: str
    explanation: str
    columns_used: list[str]
    expected_result_keys: list[str]
    error: str | None


class SafetyCheckResult(TypedDict, total=False):
    passed: bool
    reason: str | None
    blocked_items: list[str]
    warnings: list[str]


class CodeExecutionResult(TypedDict, total=False):
    status: ExecutionStatus
    answer: str | None
    tables: dict[str, Any]
    charts: list[Any]
    metadata: dict[str, Any]
    stdout: str
    stderr: str
    error: str | None
    execution_time_ms: int


class ReentryDecision(TypedDict, total=False):
    should_retry: bool
    reason: str
    retry_type: str | None
    max_retry_reached: bool


class DebugRepairResult(TypedDict, total=False):
    code: str
    repair_explanation: str
    changed_columns: dict[str, list[str]]
    columns_used: list[str]
    expected_result_keys: list[str]
    error: str | None
