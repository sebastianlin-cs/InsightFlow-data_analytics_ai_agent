from sqlalchemy.orm import Session

from app.agent.graph import run_agent_graph
from app.agent.nodes import AgentDatasetNotFoundError
from app.agent.state import AgentState
from app.models.user import User
from app.schemas.agent import AgentQueryResponse


def run_langgraph_pandas_agent_query(
    db: Session,
    current_user: User,
    session_id: int,
    query: str,
) -> AgentQueryResponse:
    """Run the v1 LangGraph/Pandas agent and return a frontend-compatible response."""
    state: AgentState = {
        "session_id": session_id,
        "user_query": query,
        "follow_up_questions": [],
        "required_columns": [],
        "analysis_plan": [],
        "tool_input": {},
        "tool_result": {},
        "chart_config": {},
        "chart_path": None,
        "chart_url": None,
        "error": None,
    }
    final_state = run_agent_graph(db, current_user, state)
    metadata = final_state.get("metadata", {})

    return AgentQueryResponse(
        session_id=final_state["session_id"],
        dataset_id=final_state["dataset_id"],
        intent=final_state.get("intent"),
        answer=final_state.get("final_answer", ""),
        analysis_plan=final_state.get("analysis_plan", []),
        tool_used=final_state.get("selected_tool"),
        tool_result=final_state.get("tool_result", {}),
        chart_url=final_state.get("chart_url"),
        follow_up_questions=final_state.get("follow_up_questions", []),
        metadata=metadata,
    )


def run_minimal_agent_query(
    db: Session,
    current_user: User,
    session_id: int,
    query: str,
) -> AgentQueryResponse:
    """Backward-compatible service alias for the upgraded v1 agent."""
    return run_langgraph_pandas_agent_query(
        db=db,
        current_user=current_user,
        session_id=session_id,
        query=query,
    )
