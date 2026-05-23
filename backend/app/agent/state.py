from typing import Any, Literal, TypedDict


AgentIntent = Literal[
    "schema_question",
    "data_overview",
    "analysis",
    "visualization",
    "clarification",
    "unsupported",
]
ExecutionMode = Literal["fixed_tool", "generated_code"]


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
    execution_mode: ExecutionMode
    generated_code: str | None
    generated_code_preview: str | None
    code_generation_result: dict[str, Any] | None
    code_safety_result: dict[str, Any] | None
    code_execution_result: dict[str, Any] | None
    reentry_used: bool
    retry_count: int
    max_retries: int
    first_execution_error: str | None
    debug_generation_result: dict[str, Any] | None
    debug_safety_result: dict[str, Any] | None
    debug_execution_result: dict[str, Any] | None
    final_execution_result: dict[str, Any] | None
    execution_status: str | None
    execution_time_ms: int | None
    code_runner: str | None
    code_generation_source: str | None
    safety_check_status: str | None
    metadata: dict[str, Any]
