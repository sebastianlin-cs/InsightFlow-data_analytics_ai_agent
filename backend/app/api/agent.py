from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.services.agent_service import AgentDatasetNotFoundError, run_langgraph_pandas_agent_query
from app.services.analysis_session_service import AnalysisSessionNotFoundError

router = APIRouter()


@router.post("/query", response_model=AgentQueryResponse)
def query_agent(
    request: AgentQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentQueryResponse:
    try:
        return run_langgraph_pandas_agent_query(
            db=db,
            current_user=current_user,
            session_id=request.session_id,
            query=request.query,
            max_retries=request.max_retries,
        )
    except (AnalysisSessionNotFoundError, AgentDatasetNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found",
        ) from exc
