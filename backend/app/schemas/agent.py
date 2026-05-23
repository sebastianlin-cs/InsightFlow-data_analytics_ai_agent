from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentQueryRequest(BaseModel):
    session_id: int
    query: str = Field(min_length=1)
    max_retries: int | None = Field(default=None, ge=0, le=3)

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Query must not be empty")
        return query


class AgentTrace(BaseModel):
    intent: str | None = None
    planner_source: str | None = None
    response_source: str | None = None
    selected_tool: str | None = None
    validated_columns: list[str] = Field(default_factory=list)
    chart_url: str | None = None
    fallback_reason: str | None = None
    llm_enabled: bool | None = None
    llm_provider: str | None = None
    execution_mode: str | None = None
    code_generation_source: str | None = None
    safety_check: str | None = None
    runner: str | None = None
    timeout_seconds: int | None = None
    execution_status: str | None = None
    execution_time_ms: int | None = None
    reentry_used: bool | None = None
    retry_count: int | None = None
    max_retries: int | None = None
    first_attempt: dict[str, Any] | None = None
    repair_attempt: dict[str, Any] | None = None
    generated_code_preview: str | None = None
    error: str | None = None
    steps: list[str] = Field(default_factory=list)


class AgentQueryResponse(BaseModel):
    session_id: int
    dataset_id: int
    intent: str | None = None
    answer: str
    analysis_plan: list[str] = Field(default_factory=list)
    tool_used: str | None = None
    tool_result: dict[str, Any] = Field(default_factory=dict)
    chart_url: str | None = None
    follow_up_questions: list[str] = Field(default_factory=list)
    agent_trace: AgentTrace | None = None
    execution_mode: str | None = None
    code_execution_result: dict[str, Any] | None = None
    generated_code_preview: str | None = None
    metadata: dict[str, Any]
