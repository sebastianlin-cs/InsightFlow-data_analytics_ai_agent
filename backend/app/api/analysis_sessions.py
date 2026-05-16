from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analysis import (
    AnalysisMessageCreate,
    AnalysisMessageResponse,
    AnalysisSessionCreate,
    AnalysisSessionResponse,
)
from app.services.analysis_session_service import (
    AnalysisSessionNotFoundError,
    DatasetNotFoundError,
    InvalidMessageRoleError,
    create_analysis_session,
    create_session_message,
    get_analysis_session,
    list_analysis_sessions,
    list_session_messages,
)

router = APIRouter()


@router.post("", response_model=AnalysisSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_create: AnalysisSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisSessionResponse:
    try:
        return create_analysis_session(
            db=db,
            current_user=current_user,
            dataset_id=session_create.dataset_id,
            title=session_create.title,
        )
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        ) from exc


@router.get("", response_model=list[AnalysisSessionResponse])
def list_sessions(
    dataset_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalysisSessionResponse]:
    try:
        return list_analysis_sessions(db, current_user, dataset_id)
    except DatasetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        ) from exc


@router.get("/{session_id}", response_model=AnalysisSessionResponse)
def read_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisSessionResponse:
    try:
        return get_analysis_session(db, current_user, session_id)
    except AnalysisSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found",
        ) from exc


@router.get("/{session_id}/messages", response_model=list[AnalysisMessageResponse])
def read_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalysisMessageResponse]:
    try:
        return list_session_messages(db, current_user, session_id)
    except AnalysisSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found",
        ) from exc


@router.post(
    "/{session_id}/messages",
    response_model=AnalysisMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    session_id: int,
    message_create: AnalysisMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisMessageResponse:
    try:
        return create_session_message(
            db=db,
            current_user=current_user,
            session_id=session_id,
            role=message_create.role,
            content=message_create.content,
            structured_result_json=message_create.structured_result_json,
        )
    except AnalysisSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis session not found",
        ) from exc
    except InvalidMessageRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message role",
        ) from exc
