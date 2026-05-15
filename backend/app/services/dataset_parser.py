from pathlib import Path
from typing import Any

import pandas as pd


class DatasetParseError(ValueError):
    pass


def parse_dataset_metadata(file_path: str, file_type: str) -> dict[str, int]:
    path = Path(file_path)
    if not path.exists() or path.stat().st_size == 0:
        raise DatasetParseError("Uploaded file is empty")

    try:
        if file_type == "csv":
            dataframe = pd.read_csv(path)
            sheet_count = 1
        elif file_type in {"xlsx", "xls"}:
            excel_file = pd.ExcelFile(path)
            if not excel_file.sheet_names:
                raise DatasetParseError("Excel file does not contain any sheets")
            dataframe = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
            sheet_count = len(excel_file.sheet_names)
        else:
            raise DatasetParseError("Unsupported file type")
    except DatasetParseError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DatasetParseError("Uploaded file is empty") from exc
    except Exception as exc:
        raise DatasetParseError("Failed to parse uploaded file") from exc

    return {
        "row_count": int(len(dataframe.index)),
        "column_count": int(len(dataframe.columns)),
        "sheet_count": int(sheet_count),
    }


def parse_dataset_preview(
    file_path: str,
    file_type: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        raise DatasetParseError("Dataset file does not exist")
    if path.stat().st_size == 0:
        raise DatasetParseError("Dataset file is empty")

    try:
        if file_type == "csv":
            dataframe = pd.read_csv(path, nrows=limit)
        elif file_type in {"xlsx", "xls"}:
            excel_file = pd.ExcelFile(path)
            if not excel_file.sheet_names:
                raise DatasetParseError("Excel file does not contain any sheets")
            dataframe = pd.read_excel(
                excel_file,
                sheet_name=excel_file.sheet_names[0],
                nrows=limit,
            )
        else:
            raise DatasetParseError("Unsupported file type")
    except DatasetParseError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise DatasetParseError("Dataset file is empty") from exc
    except Exception as exc:
        raise DatasetParseError("Failed to parse dataset preview") from exc

    dataframe = dataframe.rename(columns=str)
    preview = dataframe.head(limit).astype(object).where(pd.notna(dataframe), None)
    return [
        {column: _to_json_safe_value(value) for column, value in row.items()}
        for row in preview.to_dict(orient="records")
    ]


def _to_json_safe_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
