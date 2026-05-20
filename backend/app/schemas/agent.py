from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentQueryRequest(BaseModel):
    session_id: int
    query: str = Field(min_length=1)

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Query must not be empty")
        return query


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
    metadata: dict[str, Any]
