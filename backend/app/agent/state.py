from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_id: int
    session_id: int
    dataset_id: int
    user_query: str
    dataset_metadata: dict[str, Any]
    dataset_schema: list[dict[str, Any]]
    recent_messages: list[dict[str, Any]]
    final_answer: str
    metadata: dict[str, Any]
