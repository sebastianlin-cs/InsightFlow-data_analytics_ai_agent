from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DatasetRead(BaseModel):
    id: int
    name: str
    description: str | None
    original_filename: str
    stored_filename: str
    file_type: str
    file_size_bytes: int
    file_hash: str
    storage_backend: str
    storage_uri: str
    status: str
    row_count: int | None
    column_count: int | None
    sheet_count: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetListItem(DatasetRead):
    pass


class DatasetSchemaRead(BaseModel):
    id: int
    dataset_id: int
    sheet_name: str
    column_index: int
    column_name: str
    normalized_column_name: str
    raw_data_type: str
    semantic_type: str
    nullable: bool
    missing_count: int
    missing_rate: float
    unique_count: int | None
    unique_ratio: float | None
    sample_values_json: list[Any] | None
    min_value: str | None
    max_value: str | None
    sensitivity_tag: str
    is_measure: bool
    is_dimension: bool
    is_time_column: bool
    is_identifier: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetDetail(DatasetRead):
    schema_: list[DatasetSchemaRead] = Field(alias="schema", serialization_alias="schema")
    preview_columns: list[str]
    preview_rows: list[dict[str, Any]]
    preview_row_count: int

    model_config = {"from_attributes": True, "populate_by_name": True}


class DatasetDeleteResponse(BaseModel):
    message: str
