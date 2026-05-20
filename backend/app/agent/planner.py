from typing import Any


class LLMPlanner:
    """Placeholder for a future LLM-backed planner."""

    def plan(self, query: str, dataset_schema: list[dict[str, Any]]) -> dict[str, Any]:
        """Reserve the LLM planning boundary without making provider calls."""
        raise NotImplementedError("LLM planning is not implemented in v1.")


def build_rule_based_plan(
    query: str,
    intent: str,
    dataset_schema: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a small structured plan from query text and schema metadata."""
    normalized = query.strip().lower()
    matches = _matched_columns(normalized, dataset_schema)
    operation = _detect_operation(normalized)
    group_by = _column_after_by(normalized, dataset_schema)
    metric = _metric_column(normalized, dataset_schema, matches, group_by)
    unresolved_columns = _unresolved_column_mentions(normalized, matches, group_by, metric)

    selected_tool: str | None = None
    tool_input: dict[str, Any] = {}
    chart_config: dict[str, Any] = {}
    plan_steps = [
        "Load dataset context and schema.",
        "Validate referenced fields against the catalog.",
    ]

    if intent == "data_overview":
        selected_tool = "profile_dataset_tool"
        plan_steps.append("Profile rows, columns, missing values, and basic summaries.")
    elif intent == "analysis":
        if "correlation" in normalized:
            selected_tool = "correlation_tool"
            tool_input = {"columns": matches or None}
            plan_steps.append("Compute numeric correlations.")
        elif group_by and metric:
            selected_tool = "aggregate_tool"
            tool_input = {"group_by": group_by, "metric": metric, "operation": operation}
            plan_steps.append(f"Aggregate {metric} by {group_by} using {operation}.")
        else:
            selected_tool = "basic_stats_tool"
            tool_input = {"columns": matches}
            plan_steps.append("Compute descriptive statistics for selected numeric fields.")
    elif intent == "visualization":
        chart_type = _detect_chart_type(normalized)
        chart_config = {
            "chart_type": chart_type,
            "x": group_by,
            "y": metric,
            "aggregation": operation,
        }
        selected_tool = "generate_chart_tool"
        tool_input = dict(chart_config)
        plan_steps.append("Generate a chart from the selected fields.")
    elif intent == "schema_question":
        plan_steps.append("Summarize catalog fields, semantic types, and samples.")
    elif intent == "clarification":
        plan_steps.append("Ask for the missing analysis details.")
    else:
        plan_steps.append("Explain the v1 agent scope.")

    required_columns = [
        column for column in [group_by, metric, *matches, *unresolved_columns] if column
    ]
    return {
        "required_columns": list(dict.fromkeys(required_columns)),
        "analysis_plan": plan_steps,
        "selected_tool": selected_tool,
        "tool_input": tool_input,
        "chart_config": chart_config,
    }


def _matched_columns(query: str, dataset_schema: list[dict[str, Any]]) -> list[str]:
    matches: list[str] = []
    for column in dataset_schema:
        for key in ("column_name", "normalized_column_name"):
            value = str(column.get(key) or "").lower().replace("_", " ")
            tokens = [token for token in value.split() if len(token) > 2]
            if value and (value in query or any(token in query.split() for token in tokens)):
                matches.append(str(column.get("column_name")))
                break
    return list(dict.fromkeys(matches))


def _detect_operation(query: str) -> str:
    if "average" in query or "mean" in query:
        return "mean"
    if "sum" in query or "total" in query:
        return "sum"
    if "minimum" in query or " min" in query:
        return "min"
    if "maximum" in query or " max" in query:
        return "max"
    return "count" if "count" in query else "mean"


def _column_after_by(query: str, dataset_schema: list[dict[str, Any]]) -> str | None:
    if " by " not in query:
        return None
    tail = query.split(" by ", 1)[1]
    matches = _matched_columns(tail, dataset_schema)
    if matches:
        return matches[0]
    return None


def _metric_column(
    query: str,
    dataset_schema: list[dict[str, Any]],
    matches: list[str],
    group_by: str | None,
) -> str | None:
    measures = [str(row["column_name"]) for row in dataset_schema if row.get("is_measure")]
    for column in matches:
        if column != group_by and column in measures:
            return column
    for column in measures:
        if column.lower() in query:
            return column
    return None


def _detect_chart_type(query: str) -> str | None:
    for chart_type in ("bar", "line", "histogram", "scatter"):
        if chart_type in query:
            return chart_type
    return None


def _unresolved_column_mentions(
    query: str,
    matches: list[str],
    group_by: str | None,
    metric: str | None,
) -> list[str]:
    candidates: list[str] = []
    if not group_by and " by " in query:
        tail = query.split(" by ", 1)[1].strip().split()
        if tail:
            candidates.append(tail[0])

    metric_markers = {"average", "mean", "sum", "total", "min", "max"}
    words = query.replace("?", " ").split()
    if not metric:
        for index, word in enumerate(words[:-1]):
            if word not in metric_markers:
                continue
            candidate = words[index + 1]
            if candidate not in {"of", "by", "the", "a", "an"}:
                candidates.append(candidate)
            break

    matched_lower = {column.lower() for column in matches}
    return [
        candidate
        for candidate in dict.fromkeys(candidates)
        if candidate.lower() not in matched_lower
    ]
