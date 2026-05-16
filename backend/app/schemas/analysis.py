from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalysisSessionCreate(BaseModel):
    dataset_id: int
    title: str | None = None


class AnalysisSessionResponse(BaseModel):
    id: int
    user_id: int
    dataset_id: int
    title: str
    current_topic: str | None
    current_intent: str | None
    current_filters_json: dict[str, Any] | None
    last_result_summary_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisMessageCreate(BaseModel):
    role: str
    content: str = Field(min_length=1)
    structured_result_json: dict[str, Any] | list[Any] | None = None


class AnalysisMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    structured_result_json: dict[str, Any] | list[Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
