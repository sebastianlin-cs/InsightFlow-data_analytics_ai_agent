from __future__ import annotations

import json
from typing import Any


def build_planner_prompt(
    *,
    query: str,
    schema: list[dict[str, Any]],
    recent_messages: list[dict[str, Any]],
    intent: str,
) -> str:
    """Build a JSON-only planning prompt for a constrained analysis planner."""
    return f"""
You are the planning component of InsightFlow, a data analysis assistant.

Return JSON only. Do not wrap it in markdown.

Allowed intents:
- schema_question
- data_overview
- analysis
- visualization
- clarification
- unsupported

Allowed selected_tool values:
- profile_dataset_tool
- aggregate_tool
- correlation_tool
- basic_stats_tool
- generate_chart_tool

Rules:
- Use only the provided schema.
- Do not invent columns.
- Do not request arbitrary Python execution.
- Do not choose tools outside the allowed list.
- Do not plan SQL, AutoML, model training, file deletion, or multi-agent work.
- Use null for selected_tool when no tool is needed.
- required_columns must contain only real column names from the schema.

Output shape:
{{
  "required_columns": ["column_name"],
  "analysis_plan": ["step"],
  "selected_tool": "aggregate_tool",
  "tool_input": {{"group_by": "region", "metric": "sales", "operation": "mean"}},
  "chart_config": {{"chart_type": "bar", "x": "region", "y": "sales", "aggregation": "mean"}}
}}

Intent: {intent}
User query: {query}
Schema JSON: {json.dumps(_safe_schema(schema), ensure_ascii=False)}
Recent messages JSON: {json.dumps(recent_messages[-5:], ensure_ascii=False)}
""".strip()


def build_response_prompt(
    *,
    query: str,
    schema: list[dict[str, Any]],
    analysis_plan: list[str],
    tool_result: dict[str, Any],
    chart_url: str | None = None,
    error: str | None = None,
    follow_up_questions: list[str] | None = None,
) -> str:
    """Build a response prompt that only summarizes already-computed results."""
    return f"""
You are the response writer for InsightFlow.

Write a concise user-facing answer. Do not call tools. Do not execute code.

Rules:
- Only summarize the provided tool_result, chart_url, error, and follow_up_questions.
- Do not invent values, columns, charts, causes, business implications, or unsupported insights.
- If there is an error or missing information, explain the limitation clearly and ask for the needed detail.
- If chart_url is present, include it exactly.

User query: {query}
Schema JSON: {json.dumps(_safe_schema(schema), ensure_ascii=False)}
Analysis plan JSON: {json.dumps(analysis_plan, ensure_ascii=False)}
Tool result JSON: {json.dumps(tool_result, ensure_ascii=False)}
Chart URL: {chart_url}
Error: {error}
Follow-up questions JSON: {json.dumps(follow_up_questions or [], ensure_ascii=False)}
""".strip()


def _safe_schema(schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "column_name": row.get("column_name"),
            "normalized_column_name": row.get("normalized_column_name"),
            "semantic_type": row.get("semantic_type"),
            "raw_data_type": row.get("raw_data_type"),
            "is_measure": row.get("is_measure"),
            "is_dimension": row.get("is_dimension"),
            "is_time_column": row.get("is_time_column"),
            "sample_values_json": row.get("sample_values_json"),
        }
        for row in schema
    ]
