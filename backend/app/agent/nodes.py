from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.llm_client import get_llm_client
from app.agent.planner import build_rule_based_plan
from app.agent.router import route_intent
from app.agent.state import AgentState
from app.agent.tools.chart_tools import generate_chart_tool
from app.agent.tools.dataframe_tools import (
    aggregate_tool,
    basic_stats_tool,
    correlation_tool,
    profile_dataset_tool,
)
from app.agent.validators import validate_llm_plan
from app.core.config import settings
from app.models.analysis import AnalysisMessage
from app.models.dataset import Dataset, DatasetSchema
from app.models.user import User
from app.services.analysis_session_service import (
    create_session_message,
    get_analysis_session,
)
from app.services.data_catalog_service import get_dataset_schema_rows

RECENT_MESSAGE_LIMIT = 10


class AgentDatasetNotFoundError(Exception):
    """Raised when the session dataset cannot be loaded for the current user."""


def load_context_node(db: Session, current_user: User, state: AgentState) -> AgentState:
    """Load session, dataset, schema, file path, and recent chat context."""
    session = get_analysis_session(db, current_user, state["session_id"])
    dataset = _get_user_dataset(db, current_user.id, session.dataset_id)
    if dataset is None:
        raise AgentDatasetNotFoundError

    schema_rows = get_dataset_schema_rows(db, dataset.id)
    recent_messages = _get_recent_messages(db, session.id)

    state.update(
        {
            "user_id": current_user.id,
            "session_id": session.id,
            "dataset_id": dataset.id,
            "dataset_metadata": _dataset_metadata(dataset),
            "dataset_schema": [_schema_metadata(row) for row in schema_rows],
            "dataset_path": dataset.file_path,
            "dataset_file_type": dataset.file_type,
            "recent_messages": [_message_metadata(message) for message in recent_messages],
            "llm_enabled": settings.LLM_ENABLED,
            "llm_provider": settings.LLM_PROVIDER,
        }
    )
    return state


def intent_router_node(state: AgentState) -> AgentState:
    """Classify the user query into a v1 supported intent."""
    state["intent"] = route_intent(state["user_query"])
    return state


def planning_node(state: AgentState) -> AgentState:
    """Build a structured plan with optional LLM planning and rule-based fallback."""
    if settings.LLM_ENABLED:
        try:
            raw_plan = get_llm_client(settings).generate_plan(
                query=state["user_query"],
                schema=state.get("dataset_schema", []),
                recent_messages=state.get("recent_messages", []),
                intent=state["intent"],
            )
            plan = validate_llm_plan(raw_plan, state.get("dataset_schema", []))
            state.update(plan)
            state["planner_source"] = "llm"
            return state
        except Exception as exc:
            _set_fallback_reason(state, str(exc))

    plan = build_rule_based_plan(
        query=state["user_query"],
        intent=state["intent"],
        dataset_schema=state.get("dataset_schema", []),
    )
    state.update(plan)
    state["planner_source"] = "rule_based"
    return state


def validation_node(state: AgentState) -> AgentState:
    """Validate dataset file and planned fields before dispatching tools."""
    dataset_path = state.get("dataset_path")
    if not dataset_path or not Path(dataset_path).exists():
        state["intent"] = "clarification"
        state["error"] = "Dataset file is missing from local storage."
        state["follow_up_questions"] = [
            "Please re-upload the dataset so I can access the source file."
        ]
        return state

    available_columns = _available_columns(state)
    missing = [
        column for column in state.get("required_columns", []) if column not in available_columns
    ]
    if missing:
        state["intent"] = "clarification"
        state["error"] = f"Unknown field(s): {', '.join(missing)}"
        state["follow_up_questions"] = [
            "Which of these available fields should I use? "
            + ", ".join(available_columns[:20])
        ]
        return state

    if state.get("intent") == "visualization":
        config = state.get("chart_config", {})
        needs_xy = config.get("chart_type") in {"bar", "line", "scatter"}
        missing_xy = needs_xy and (not config.get("x") or not config.get("y"))
        if (not config.get("x") and not config.get("y")) or missing_xy:
            state["intent"] = "clarification"
            state["follow_up_questions"] = [
                "Which fields should I use for the chart? Available fields: "
                + ", ".join(available_columns[:20])
            ]
    return state


def dispatch_node(state: AgentState) -> AgentState:
    """Dispatch state to the handler that matches the current intent."""
    handlers = {
        "schema_question": schema_handler,
        "data_overview": overview_handler,
        "analysis": analysis_handler,
        "visualization": visualization_handler,
        "clarification": clarification_handler,
        "unsupported": unsupported_handler,
    }
    return handlers.get(state.get("intent", "unsupported"), unsupported_handler)(state)


def schema_handler(state: AgentState) -> AgentState:
    """Prepare schema catalog content for response generation."""
    state["tool_result"] = {
        "columns": [
            {
                "name": row.get("column_name"),
                "type": row.get("semantic_type"),
                "raw_type": row.get("raw_data_type"),
                "samples": row.get("sample_values_json"),
                "missing_rate": row.get("missing_rate"),
            }
            for row in state.get("dataset_schema", [])
        ],
        "error": None,
    }
    state["selected_tool"] = None
    return state


def overview_handler(state: AgentState) -> AgentState:
    """Run the dataset profile pandas tool."""
    state["selected_tool"] = "profile_dataset_tool"
    state["tool_result"] = profile_dataset_tool(state["dataset_path"])
    _copy_tool_error(state)
    return state


def analysis_handler(state: AgentState) -> AgentState:
    """Run the selected pandas analysis tool."""
    selected_tool = state.get("selected_tool")
    tool_input = state.get("tool_input", {})
    if selected_tool == "aggregate_tool":
        state["tool_result"] = aggregate_tool(
            dataset_path=state["dataset_path"],
            group_by=tool_input.get("group_by"),
            metric=tool_input.get("metric"),
            operation=tool_input.get("operation", "mean"),
        )
    elif selected_tool == "correlation_tool":
        state["tool_result"] = correlation_tool(
            dataset_path=state["dataset_path"],
            columns=tool_input.get("columns"),
        )
    else:
        state["selected_tool"] = "basic_stats_tool"
        state["tool_result"] = basic_stats_tool(
            dataset_path=state["dataset_path"],
            columns=tool_input.get("columns", []),
        )
    _copy_tool_error(state)
    return state


def visualization_handler(state: AgentState) -> AgentState:
    """Generate a static chart with matplotlib."""
    config = state.get("chart_config", {})
    output_dir = Path(settings.UPLOAD_DIR) / "charts" / f"session_{state['session_id']}"
    result = generate_chart_tool(
        dataset_path=state["dataset_path"],
        chart_type=config.get("chart_type"),
        x=config.get("x"),
        y=config.get("y"),
        aggregation=config.get("aggregation"),
        output_dir=str(output_dir),
    )
    state["selected_tool"] = "generate_chart_tool"
    state["tool_result"] = result
    state["chart_path"] = result.get("chart_path")
    state["chart_url"] = result.get("chart_url")
    _copy_tool_error(state)
    return state


def clarification_handler(state: AgentState) -> AgentState:
    """Prepare clarification questions when the request lacks usable fields."""
    if not state.get("follow_up_questions"):
        fields = ", ".join(_available_columns(state)[:20])
        state["follow_up_questions"] = [
            f"Please specify the metric and grouping field. Available fields: {fields}"
        ]
    state["tool_result"] = {"error": state.get("error")}
    return state


def unsupported_handler(state: AgentState) -> AgentState:
    """Return the current v1 capability boundary."""
    state["tool_result"] = {"error": "This request is outside the v1 data analysis scope."}
    state["follow_up_questions"] = [
        "Try asking for schema, overview, grouped aggregation, correlation, basic stats, or a simple chart."
    ]
    return state


def response_generation_node(state: AgentState) -> AgentState:
    """Generate an answer with optional LLM rewriting and template fallback."""
    if settings.LLM_ENABLED:
        try:
            answer = get_llm_client(settings).generate_response(
                query=state["user_query"],
                schema=state.get("dataset_schema", []),
                analysis_plan=state.get("analysis_plan", []),
                tool_result=state.get("tool_result", {}),
                chart_url=state.get("chart_url"),
                error=state.get("error"),
                follow_up_questions=state.get("follow_up_questions"),
            )
            state["final_answer"] = _coerce_llm_answer(answer)
            state["response_source"] = "llm"
            state["metadata"] = _response_metadata(state)
            return state
        except Exception as exc:
            _set_fallback_reason(state, str(exc))

    _apply_template_response(state)
    state["response_source"] = "template"
    state["metadata"] = _response_metadata(state)
    return state


def _apply_template_response(state: AgentState) -> None:
    """Populate final_answer using the deterministic v1 template responses."""
    intent = state.get("intent", "unsupported")
    result = state.get("tool_result", {})
    if intent == "schema_question":
        state["final_answer"] = _schema_answer(state)
    elif intent == "data_overview":
        state["final_answer"] = _overview_answer(result)
    elif intent == "analysis":
        state["final_answer"] = _analysis_answer(state)
    elif intent == "visualization":
        state["final_answer"] = _visualization_answer(state)
    elif intent == "clarification":
        state["final_answer"] = "I need one more detail before running this analysis. " + " ".join(
            state.get("follow_up_questions", [])
        )
    else:
        state["final_answer"] = (
            "This v1 agent supports dataset schema questions, overview profiling, "
            "basic pandas statistics, grouped aggregations, correlations, and simple charts."
        )


def save_session_node(db: Session, current_user: User, state: AgentState) -> AgentState:
    """Save the user message and assistant answer to the analysis session."""
    create_session_message(
        db=db,
        current_user=current_user,
        session_id=state["session_id"],
        role="user",
        content=state["user_query"],
        structured_result_json=None,
    )
    agent_trace = build_agent_trace(state, include_saved_step=True)
    state["agent_trace"] = agent_trace
    message_metadata = {
        "intent": state.get("intent"),
        "analysis_plan": state.get("analysis_plan"),
        "selected_tool": state.get("selected_tool"),
        "chart_url": state.get("chart_url"),
        "error": state.get("error"),
        "llm_enabled": state.get("llm_enabled"),
        "llm_provider": state.get("llm_provider"),
        "planner_source": state.get("planner_source"),
        "response_source": state.get("response_source"),
        "fallback_reason": state.get("fallback_reason"),
        "agent_trace": agent_trace,
    }
    create_session_message(
        db=db,
        current_user=current_user,
        session_id=state["session_id"],
        role="assistant",
        content=state["final_answer"],
        structured_result_json=message_metadata,
    )
    state["metadata"]["message_saved"] = True
    state["agent_trace"] = agent_trace
    return state


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


def _dataset_metadata(dataset: Dataset) -> dict[str, Any]:
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


def _schema_metadata(schema_row: DatasetSchema) -> dict[str, Any]:
    return {
        "column_name": schema_row.column_name,
        "normalized_column_name": schema_row.normalized_column_name,
        "raw_data_type": schema_row.raw_data_type,
        "semantic_type": schema_row.semantic_type,
        "nullable": schema_row.nullable,
        "missing_count": schema_row.missing_count,
        "missing_rate": schema_row.missing_rate,
        "unique_count": schema_row.unique_count,
        "sample_values_json": schema_row.sample_values_json,
        "sensitivity_tag": schema_row.sensitivity_tag,
        "is_measure": schema_row.is_measure,
        "is_dimension": schema_row.is_dimension,
        "is_time_column": schema_row.is_time_column,
        "is_identifier": schema_row.is_identifier,
    }


def _message_metadata(message: AnalysisMessage) -> dict[str, str]:
    return {
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def _available_columns(state: AgentState) -> list[str]:
    return [str(row.get("column_name")) for row in state.get("dataset_schema", [])]


def _copy_tool_error(state: AgentState) -> None:
    error = state.get("tool_result", {}).get("error")
    if error:
        state["error"] = error.get("message") if isinstance(error, dict) else str(error)


def _set_fallback_reason(state: AgentState, reason: str) -> None:
    if not state.get("fallback_reason"):
        state["fallback_reason"] = reason


def _response_metadata(state: AgentState) -> dict[str, Any]:
    return {
        "mode": "langgraph_pandas_agent_v1_1",
        "used_schema": bool(state.get("dataset_schema")),
        "used_recent_messages": bool(state.get("recent_messages")),
        "message_saved": False,
        "intent": state.get("intent"),
        "selected_tool": state.get("selected_tool"),
        "chart_url": state.get("chart_url"),
        "error": state.get("error"),
        "llm_enabled": bool(state.get("llm_enabled")),
        "llm_provider": state.get("llm_provider"),
        "planner_source": state.get("planner_source"),
        "response_source": state.get("response_source"),
        "fallback_reason": state.get("fallback_reason"),
    }


def build_agent_trace(state: AgentState, *, include_saved_step: bool = False) -> dict[str, Any]:
    """Build a compact observable trace for API responses and message metadata."""
    steps = [
        "Loaded dataset context",
        "Classified user intent",
        "Generated analysis plan",
        "Validated required columns",
        "Executed selected tool",
        "Generated final response",
    ]
    if include_saved_step:
        steps.append("Saved analysis message")
    return {
        "intent": state.get("intent"),
        "planner_source": state.get("planner_source"),
        "response_source": state.get("response_source"),
        "selected_tool": state.get("selected_tool"),
        "validated_columns": state.get("required_columns", []),
        "chart_url": state.get("chart_url"),
        "fallback_reason": state.get("fallback_reason"),
        "llm_enabled": state.get("llm_enabled"),
        "llm_provider": state.get("llm_provider"),
        "steps": steps,
    }


def _coerce_llm_answer(answer: str | dict[str, Any]) -> str:
    if isinstance(answer, str):
        clean_answer = answer.strip()
        if clean_answer:
            return clean_answer
        raise RuntimeError("LLM response was empty.")
    if isinstance(answer, dict):
        for key in ("answer", "content", "message"):
            value = answer.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    raise RuntimeError("LLM response must be a non-empty string or contain an answer field.")


def _schema_answer(state: AgentState) -> str:
    schema = state.get("dataset_schema", [])
    if not schema:
        return "I loaded the session, but this dataset does not have catalog fields yet."
    names = [str(row.get("column_name")) for row in schema]
    return f"This dataset has {len(schema)} columns: {', '.join(names)}."


def _overview_answer(result: dict[str, Any]) -> str:
    if result.get("error"):
        return f"I could not profile the dataset: {result['error']}"
    shape = result.get("shape", {})
    return (
        f"The dataset has {shape.get('rows')} rows and {shape.get('columns')} columns. "
        "I also computed missing values plus numeric and categorical summaries."
    )


def _analysis_answer(state: AgentState) -> str:
    if state.get("error"):
        return f"I could not complete the analysis: {state['error']}"
    selected_tool = state.get("selected_tool")
    if selected_tool == "aggregate_tool":
        tool_input = state.get("tool_input", {})
        return (
            f"I calculated {tool_input.get('operation')} of {tool_input.get('metric')} "
            f"by {tool_input.get('group_by')}. The structured result contains the rows."
        )
    if selected_tool == "correlation_tool":
        return "I calculated numeric correlations. The structured result contains the correlation matrix."
    return "I calculated descriptive statistics. The structured result contains the summary table."


def _visualization_answer(state: AgentState) -> str:
    if state.get("error"):
        return f"I could not generate the chart: {state['error']}"
    return f"I generated a chart for this request: {state.get('chart_url')}."
