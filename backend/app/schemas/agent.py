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
    answer: str
    metadata: dict[str, Any]
