from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.dataset_parser import DatasetParseError


def load_head_preview(
    file_path: str,
    file_type: str,
    limit: int = 5,
) -> dict[str, Any]:
    dataframe = _read_head_dataframe(file_path, file_type, limit)
    dataframe = dataframe.rename(columns=str)
    preview = dataframe.head(limit).astype(object).where(pd.notna(dataframe), None)
    rows = [
        {column: _to_json_safe_value(value) for column, value in row.items()}
        for row in preview.to_dict(orient="records")
    ]
    return {
        "preview_columns": list(dataframe.columns),
        "preview_rows": rows,
        "preview_row_count": len(rows),
    }


def _read_head_dataframe(file_path: str, file_type: str, limit: int) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise DatasetParseError("Dataset file does not exist")
    if path.stat().st_size == 0:
        raise DatasetParseError("Dataset file is empty")

    try:
        if file_type == "csv":
            return pd.read_csv(path, nrows=limit)
        if file_type in {"xlsx", "xls"}:
            with pd.ExcelFile(path) as excel_file:
                if not excel_file.sheet_names:
                    raise DatasetParseError("Excel file does not contain any sheets")
                return pd.read_excel(
                    excel_file,
                    sheet_name=excel_file.sheet_names[0],
                    nrows=limit,
                )
    except DatasetParseError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DatasetParseError("Dataset file is empty") from exc
    except Exception as exc:
        raise DatasetParseError("Failed to parse dataset preview") from exc

    raise DatasetParseError("Unsupported file type")


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
