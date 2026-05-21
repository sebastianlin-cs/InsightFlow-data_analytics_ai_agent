from typing import Any, Literal, TypedDict


AgentIntent = Literal[
    "schema_question",
    "data_overview",
    "analysis",
    "visualization",
    "clarification",
    "unsupported",
]


class AgentState(TypedDict, total=False):
    user_id: int
    session_id: int
    dataset_id: int
    user_query: str
    dataset_metadata: dict[str, Any]
    dataset_schema: list[dict[str, Any]]
    dataset_path: str
    dataset_file_type: str
    recent_messages: list[dict[str, Any]]
    intent: AgentIntent
    required_columns: list[str]
    analysis_plan: list[str]
    selected_tool: str | None
    tool_input: dict[str, Any]
    tool_result: dict[str, Any]
    chart_config: dict[str, Any]
    chart_path: str | None
    chart_url: str | None
    final_answer: str
    follow_up_questions: list[str]
    error: str | None
    llm_enabled: bool
    llm_provider: str
    planner_source: str
    response_source: str
    fallback_reason: str | None
    agent_trace: dict[str, Any]
    metadata: dict[str, Any]
