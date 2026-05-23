from __future__ import annotations

from typing import Any

ALLOWED_TOOLS = {
    "profile_dataset_tool",
    "aggregate_tool",
    "correlation_tool",
    "basic_stats_tool",
    "generate_chart_tool",
}
ALLOWED_CHART_TYPES = {"bar", "line", "histogram", "scatter", None}
ALLOWED_EXECUTION_MODES = {"fixed_tool", "generated_code", None}


class LLMPlanValidationError(ValueError):
    """Raised when an LLM plan is unsafe or does not match the dataset schema."""


def validate_llm_plan(
    raw_plan: dict[str, Any],
    dataset_schema: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate and normalize an LLM-generated plan before any tool dispatch."""
    if not isinstance(raw_plan, dict):
        raise LLMPlanValidationError("LLM planner output must be a JSON object.")

    required_columns = _require_string_list(raw_plan.get("required_columns", []), "required_columns")
    analysis_plan = _require_string_list(raw_plan.get("analysis_plan", []), "analysis_plan")
    selected_tool = raw_plan.get("selected_tool")
    if selected_tool is not None and not isinstance(selected_tool, str):
        raise LLMPlanValidationError("selected_tool must be a string or null.")
    if selected_tool is not None and selected_tool not in ALLOWED_TOOLS:
        raise LLMPlanValidationError(f"Unsupported selected_tool: {selected_tool}")

    tool_input = raw_plan.get("tool_input", {})
    chart_config = raw_plan.get("chart_config", {})
    if not isinstance(tool_input, dict):
        raise LLMPlanValidationError("tool_input must be an object.")
    if not isinstance(chart_config, dict):
        raise LLMPlanValidationError("chart_config must be an object.")

    column_map = _column_map(dataset_schema)
    normalized_required = [_canonical_column(column, column_map) for column in required_columns]
    normalized_tool_input = _normalize_column_values(tool_input, column_map)
    normalized_chart_config = _normalize_column_values(chart_config, column_map)

    if selected_tool == "generate_chart_tool":
        chart_type = normalized_chart_config.get("chart_type")
        if chart_type not in ALLOWED_CHART_TYPES:
            raise LLMPlanValidationError(f"Unsupported chart_type: {chart_type}")
    execution_mode = raw_plan.get("execution_mode")
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        raise LLMPlanValidationError(f"Unsupported execution_mode: {execution_mode}")

    return {
        "required_columns": list(dict.fromkeys(normalized_required)),
        "analysis_plan": analysis_plan,
        "selected_tool": selected_tool,
        "tool_input": normalized_tool_input,
        "chart_config": normalized_chart_config,
        "execution_mode": execution_mode or "fixed_tool",
    }


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise LLMPlanValidationError(f"{field_name} must be a list of strings.")
    return value


def _column_map(dataset_schema: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in dataset_schema:
        column_name = str(row.get("column_name") or "")
        normalized = str(row.get("normalized_column_name") or "")
        for value in {column_name, normalized, column_name.lower(), normalized.lower()}:
            if value:
                mapping[_normalize_key(value)] = column_name
    return mapping


def _canonical_column(column: str, column_map: dict[str, str]) -> str:
    key = _normalize_key(column)
    if key not in column_map:
        raise LLMPlanValidationError(f"LLM plan referenced unknown column: {column}")
    return column_map[key]


def _normalize_column_values(value: Any, column_map: dict[str, str]) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, inner in value.items():
            if key in {"group_by", "metric", "x", "y"} and isinstance(inner, str):
                normalized[key] = _canonical_column(inner, column_map)
            elif key == "columns" and isinstance(inner, list):
                normalized[key] = [
                    _canonical_column(column, column_map)
                    for column in inner
                    if isinstance(column, str)
                ]
            else:
                normalized[key] = _normalize_column_values(inner, column_map)
        return normalized
    if isinstance(value, list):
        return [_normalize_column_values(item, column_map) for item in value]
    return value


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("_", " ")
