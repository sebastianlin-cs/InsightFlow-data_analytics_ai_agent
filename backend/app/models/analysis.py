from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.user import User


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    current_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_intent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_filters_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_result_summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", back_populates="analysis_sessions")
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="analysis_sessions")
    messages: Mapped[list["AnalysisMessage"]] = relationship(
        "AnalysisMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class AnalysisMessage(Base):
    __tablename__ = "analysis_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_sessions.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_result_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["AnalysisSession"] = relationship(
        "AnalysisSession",
        back_populates="messages",
    )
