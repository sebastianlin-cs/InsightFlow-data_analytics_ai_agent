from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisMessage, AnalysisSession
from app.models.dataset import Dataset
from app.models.user import User

ALLOWED_MESSAGE_ROLES = {"user", "assistant", "system", "tool"}


class AnalysisSessionError(Exception):
    pass


class DatasetNotFoundError(AnalysisSessionError):
    pass


class AnalysisSessionNotFoundError(AnalysisSessionError):
    pass


class InvalidMessageRoleError(AnalysisSessionError):
    pass


def create_analysis_session(
    db: Session,
    current_user: User,
    dataset_id: int,
    title: str | None = None,
) -> AnalysisSession:
    dataset = _get_user_dataset(db, current_user.id, dataset_id)
    if dataset is None:
        raise DatasetNotFoundError

    clean_title = title.strip() if title else ""
    session = AnalysisSession(
        user_id=current_user.id,
        dataset_id=dataset.id,
        title=clean_title or f"Analysis Session for {dataset.name}",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_analysis_sessions(
    db: Session,
    current_user: User,
    dataset_id: int | None = None,
) -> list[AnalysisSession]:
    if dataset_id is not None and _get_user_dataset(db, current_user.id, dataset_id) is None:
        raise DatasetNotFoundError

    statement = select(AnalysisSession).where(AnalysisSession.user_id == current_user.id)
    if dataset_id is not None:
        statement = statement.where(AnalysisSession.dataset_id == dataset_id)

    return list(db.scalars(statement.order_by(AnalysisSession.updated_at.desc())))


def get_analysis_session(
    db: Session,
    current_user: User,
    session_id: int,
) -> AnalysisSession:
    session = db.scalar(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    if session is None:
        raise AnalysisSessionNotFoundError
    return session


def list_session_messages(
    db: Session,
    current_user: User,
    session_id: int,
) -> list[AnalysisMessage]:
    session = get_analysis_session(db, current_user, session_id)
    return list(
        db.scalars(
            select(AnalysisMessage)
            .where(AnalysisMessage.session_id == session.id)
            .order_by(AnalysisMessage.created_at.asc(), AnalysisMessage.id.asc())
        )
    )


def create_session_message(
    db: Session,
    current_user: User,
    session_id: int,
    role: str,
    content: str,
    structured_result_json: dict[str, Any] | list[Any] | None = None,
) -> AnalysisMessage:
    session = get_analysis_session(db, current_user, session_id)
    normalized_role = role.strip().lower()
    if normalized_role not in ALLOWED_MESSAGE_ROLES:
        raise InvalidMessageRoleError

    message = AnalysisMessage(
        session_id=session.id,
        role=normalized_role,
        content=content,
        structured_result_json=structured_result_json,
    )
    session.updated_at = datetime.utcnow()
    db.add(message)
    db.add(session)
    db.commit()
    db.refresh(message)
    return message


def _get_user_dataset(db: Session, user_id: int, dataset_id: int) -> Dataset | None:
    return db.scalar(
        select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
        )
    )
