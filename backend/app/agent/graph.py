from sqlalchemy.orm import Session

from app.agent.nodes import (
    dispatch_node,
    intent_router_node,
    load_context_node,
    planning_node,
    response_generation_node,
    save_session_node,
    validation_node,
)
from app.agent.state import AgentState
from app.models.user import User


def run_agent_graph(db: Session, current_user: User, initial_state: AgentState) -> AgentState:
    """Run the v1 workflow through LangGraph when available, with a local fallback."""
    try:
        return _run_langgraph(db, current_user, initial_state)
    except ImportError:
        return _run_sequential(db, current_user, initial_state)


def _run_langgraph(db: Session, current_user: User, initial_state: AgentState) -> AgentState:
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)
    workflow.add_node("load_context", lambda state: load_context_node(db, current_user, state))
    workflow.add_node("intent_router", intent_router_node)
    workflow.add_node("planning", planning_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("dispatch", dispatch_node)
    workflow.add_node("response_generation", response_generation_node)
    workflow.add_node("save_session", lambda state: save_session_node(db, current_user, state))

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "intent_router")
    workflow.add_edge("intent_router", "planning")
    workflow.add_edge("planning", "validation")
    workflow.add_edge("validation", "dispatch")
    workflow.add_edge("dispatch", "response_generation")
    workflow.add_edge("response_generation", "save_session")
    workflow.add_edge("save_session", END)

    app = workflow.compile()
    return app.invoke(initial_state)


def _run_sequential(db: Session, current_user: User, state: AgentState) -> AgentState:
    state = load_context_node(db, current_user, state)
    state = intent_router_node(state)
    state = planning_node(state)
    state = validation_node(state)
    state = dispatch_node(state)
    state = response_generation_node(state)
    return save_session_node(db, current_user, state)
