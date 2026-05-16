from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.models.analysis import AnalysisMessage
from app.models.dataset import Dataset, DatasetSchema
from app.models.user import User
from app.schemas.agent import AgentQueryResponse
from app.services.analysis_session_service import (
    AnalysisSessionNotFoundError,
    create_session_message,
    get_analysis_session,
)
from app.services.data_catalog_service import get_dataset_schema_rows

RECENT_MESSAGE_LIMIT = 10


class AgentDatasetNotFoundError(Exception):
    pass


def run_minimal_agent_query(
    db: Session,
    current_user: User,
    session_id: int,
    query: str,
) -> AgentQueryResponse:
    session = get_analysis_session(db, current_user, session_id)
    dataset = _get_user_dataset(db, current_user.id, session.dataset_id)
    if dataset is None:
        raise AgentDatasetNotFoundError

    schema_rows = get_dataset_schema_rows(db, dataset.id)
    recent_messages = _get_recent_messages(db, session.id)

    create_session_message(
        db=db,
        current_user=current_user,
        session_id=session.id,
        role="user",
        content=query,
        structured_result_json=None,
    )

    state: AgentState = {
        "user_id": current_user.id,
        "session_id": session.id,
        "dataset_id": dataset.id,
        "user_query": query,
        "dataset_metadata": _dataset_metadata(dataset),
        "dataset_schema": [_schema_metadata(row) for row in schema_rows],
        "recent_messages": [_message_metadata(message) for message in recent_messages],
    }
    answer = _generate_rule_based_answer(state)
    metadata = {
        "mode": "minimal_agent",
        "used_schema": bool(schema_rows),
        "used_recent_messages": bool(recent_messages),
        "message_saved": True,
        "schema_column_count": len(schema_rows),
    }

    create_session_message(
        db=db,
        current_user=current_user,
        session_id=session.id,
        role="assistant",
        content=answer,
        structured_result_json=metadata,
    )

    return AgentQueryResponse(
        session_id=session.id,
        dataset_id=dataset.id,
        answer=answer,
        metadata=metadata,
    )


def _get_user_dataset(db: Session, user_id: int, dataset_id: int) -> Dataset | None:
    return db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        )
    )


def _get_recent_messages(db: Session, session_id: int) -> list[AnalysisMessage]:
    messages = list(
        db.scalars(
            select(AnalysisMessage)
            .where(AnalysisMessage.session_id == session_id)
            .order_by(AnalysisMessage.created_at.desc(), AnalysisMessage.id.desc())
            .limit(RECENT_MESSAGE_LIMIT)
        )
    )
    return list(reversed(messages))


def _dataset_metadata(dataset: Dataset) -> dict:
    return {
        "id": dataset.id,
        "name": dataset.name,
        "original_filename": dataset.original_filename,
        "file_type": dataset.file_type,
        "row_count": dataset.row_count,
        "column_count": dataset.column_count,
        "sheet_count": dataset.sheet_count,
        "status": dataset.status,
    }


def _schema_metadata(schema_row: DatasetSchema) -> dict:
    return {
        "column_name": schema_row.column_name,
        "normalized_column_name": schema_row.normalized_column_name,
        "semantic_type": schema_row.semantic_type,
        "sensitivity_tag": schema_row.sensitivity_tag,
        "is_measure": schema_row.is_measure,
        "is_dimension": schema_row.is_dimension,
        "is_time_column": schema_row.is_time_column,
        "is_identifier": schema_row.is_identifier,
    }


def _message_metadata(message: AnalysisMessage) -> dict:
    return {
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def _generate_rule_based_answer(state: AgentState) -> str:
    query = state["user_query"].lower()
    dataset_metadata = state["dataset_metadata"]
    schema = state["dataset_schema"]

    if _is_schema_question(query):
        return _schema_summary(schema)
    if _is_dataset_summary_question(query):
        return _dataset_capability_summary(dataset_metadata, schema)
    return (
        "I loaded the dataset context and session history successfully. "
        "Full analytical tools will be added in the next version. Right now I can "
        "summarize the dataset schema and available fields."
    )


def _is_schema_question(query: str) -> bool:
    return any(
        phrase in query
        for phrase in {
            "columns",
            "schema",
            "fields",
            "catalog",
            "what data",
            "what is in this dataset",
        }
    )


def _is_dataset_summary_question(query: str) -> bool:
    return any(
        phrase in query
        for phrase in {
            "summarize this dataset",
            "describe this dataset",
            "what can i analyze",
            "what can I analyze".lower(),
            "analyze",
        }
    )


def _schema_summary(schema: list[dict]) -> str:
    if not schema:
        return "I loaded the session, but this dataset does not have schema catalog records yet."

    measures = _columns_by_flag(schema, "is_measure")
    dimensions = _columns_by_flag(schema, "is_dimension")
    time_columns = _columns_by_flag(schema, "is_time_column")
    identifiers = _columns_by_flag(schema, "is_identifier")
    sensitive = [
        column["normalized_column_name"]
        for column in schema
        if column["sensitivity_tag"] != "none"
    ]

    parts = [f"This dataset has {len(schema)} columns."]
    parts.append(_format_column_group("Measures", measures))
    parts.append(_format_column_group("Dimensions", dimensions))
    parts.append(_format_column_group("Time columns", time_columns))
    parts.append(_format_column_group("Identifier columns", identifiers))
    if sensitive:
        parts.append(_format_column_group("Sensitive fields", sensitive))
    return " ".join(part for part in parts if part)


def _dataset_capability_summary(dataset_metadata: dict, schema: list[dict]) -> str:
    row_count = dataset_metadata.get("row_count")
    column_count = dataset_metadata.get("column_count") or len(schema)
    measures = _columns_by_flag(schema, "is_measure")
    dimensions = _columns_by_flag(schema, "is_dimension")
    time_columns = _columns_by_flag(schema, "is_time_column")
    sensitive = [
        column["normalized_column_name"]
        for column in schema
        if column["sensitivity_tag"] != "none"
    ]

    answer = (
        f"I loaded the dataset context successfully. This dataset has "
        f"{row_count if row_count is not None else 'unknown'} rows and "
        f"{column_count if column_count is not None else 'unknown'} columns."
    )
    suggestions: list[str] = []
    if time_columns and measures:
        suggestions.append(f"analyze {measures[0]} trends over {time_columns[0]}")
    if dimensions and measures:
        suggestions.append(f"compare {measures[0]} by {dimensions[0]}")
    if len(dimensions) > 1 and measures:
        suggestions.append(f"break down {measures[0]} by {dimensions[1]}")
    if suggestions:
        answer += " Based on the catalog, you can " + ", ".join(suggestions) + "."
    if sensitive:
        answer += " Sensitive fields are present, so future analysis should handle them carefully."
    return answer


def _columns_by_flag(schema: list[dict], flag: str) -> list[str]:
    return [column["normalized_column_name"] for column in schema if column.get(flag)]


def _format_column_group(label: str, columns: list[str]) -> str:
    if not columns:
        return ""
    return f"{label} include {', '.join(columns)}."
