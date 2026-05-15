from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import DatasetSchema
from app.services.dataset_parser import DatasetParseError
from app.services.schema_inference import (
    infer_agent_flags,
    infer_semantic_type,
    normalize_column_name,
)
from app.services.sensitivity_detector import detect_sensitivity_tag


def generate_dataset_catalog(
    db: Session,
    dataset_id: int,
    file_path: str,
    file_type: str,
) -> dict[str, int]:
    sheets = _read_dataset_sheets(file_path, file_type)
    if not sheets:
        raise DatasetParseError("Uploaded file does not contain readable data")

    db.query(DatasetSchema).filter(DatasetSchema.dataset_id == dataset_id).delete()

    schema_rows: list[DatasetSchema] = []
    first_dataframe = next(iter(sheets.values()))
    for sheet_name, dataframe in sheets.items():
        dataframe = dataframe.rename(columns=str)
        for column_index, column_name in enumerate(dataframe.columns):
            column_series = dataframe[column_name]
            schema_rows.append(
                _build_schema_row(
                    dataset_id=dataset_id,
                    sheet_name=sheet_name,
                    column_index=column_index,
                    column_name=str(column_name),
                    series=column_series,
                )
            )

    db.add_all(schema_rows)
    return {
        "row_count": int(len(first_dataframe.index)),
        "column_count": int(len(first_dataframe.columns)),
        "sheet_count": int(len(sheets)),
    }


def get_dataset_schema_rows(db: Session, dataset_id: int) -> list[DatasetSchema]:
    return list(
        db.scalars(
            select(DatasetSchema)
            .where(DatasetSchema.dataset_id == dataset_id)
            .order_by(DatasetSchema.sheet_name.asc(), DatasetSchema.column_index.asc())
        )
    )


def _read_dataset_sheets(file_path: str, file_type: str) -> dict[str, pd.DataFrame]:
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        raise DatasetParseError("Uploaded file is empty")

    try:
        if file_type == "csv":
            return {"default": pd.read_csv(path)}
        if file_type in {"xlsx", "xls"}:
            sheets = pd.read_excel(path, sheet_name=None)
            if not sheets:
                raise DatasetParseError("Excel file does not contain any sheets")
            return {str(sheet_name): dataframe for sheet_name, dataframe in sheets.items()}
    except DatasetParseError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DatasetParseError("Uploaded file is empty") from exc
    except Exception as exc:
        raise DatasetParseError("Failed to parse uploaded file") from exc

    raise DatasetParseError("Unsupported file type")


def _build_schema_row(
    dataset_id: int,
    sheet_name: str,
    column_index: int,
    column_name: str,
    series: pd.Series,
) -> DatasetSchema:
    normalized_column_name = normalize_column_name(column_name)
    semantic_type = infer_semantic_type(series, normalized_column_name)
    flags = infer_agent_flags(semantic_type)

    total_count = len(series)
    missing_count = int(series.isna().sum())
    unique_count = int(series.nunique(dropna=True))
    unique_ratio = float(unique_count / total_count) if total_count else None
    min_value, max_value = _safe_min_max(series)

    return DatasetSchema(
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        column_index=column_index,
        column_name=column_name,
        normalized_column_name=normalized_column_name,
        raw_data_type=str(series.dtype),
        semantic_type=semantic_type,
        nullable=missing_count > 0,
        missing_count=missing_count,
        missing_rate=float(missing_count / total_count) if total_count else 0.0,
        unique_count=unique_count,
        unique_ratio=unique_ratio,
        sample_values_json=_sample_values(series),
        min_value=min_value,
        max_value=max_value,
        sensitivity_tag=detect_sensitivity_tag(normalized_column_name),
        **flags,
    )


def _sample_values(series: pd.Series) -> list[Any]:
    values: list[Any] = []
    for value in series.dropna().head(20).tolist():
        safe_value = _to_json_safe_value(value)
        if safe_value is not None:
            values.append(safe_value)
        if len(values) >= 5:
            break
    return values


def _safe_min_max(series: pd.Series) -> tuple[str | None, str | None]:
    non_null = series.dropna()
    if non_null.empty:
        return None, None
    try:
        min_value = _to_json_safe_value(non_null.min())
        max_value = _to_json_safe_value(non_null.max())
    except Exception:
        return None, None
    return str(min_value), str(max_value)


def _to_json_safe_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
