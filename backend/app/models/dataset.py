from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisSession
    from app.models.user import User


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", back_populates="datasets")
    schemas: Mapped[list["DatasetSchema"]] = relationship(
        "DatasetSchema",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(
        "AnalysisSession",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class DatasetSchema(Base):
    __tablename__ = "dataset_schemas"
    __table_args__ = (
        Index(
            "ix_dataset_schemas_dataset_id_normalized_column_name",
            "dataset_id",
            "normalized_column_name",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        index=True,
    )
    sheet_name: Mapped[str] = mapped_column(String(255), default="default", nullable=False)
    column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    semantic_type: Mapped[str] = mapped_column(String(50), nullable=False)
    nullable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unique_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unique_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_values_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    min_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sensitivity_tag: Mapped[str] = mapped_column(String(50), default="none", nullable=False)
    is_measure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dimension: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_time_column: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_identifier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="schemas")
