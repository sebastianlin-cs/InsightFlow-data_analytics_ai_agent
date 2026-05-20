from pathlib import Path
from typing import Any

import pandas as pd


def profile_dataset_tool(dataset_path: str) -> dict[str, Any]:
    """Return shape, columns, missing values, and simple column summaries."""
    try:
        dataframe = _read_dataframe(dataset_path)
        numeric = dataframe.select_dtypes(include="number")
        categorical = dataframe.select_dtypes(exclude="number")
        return {
            "shape": {"rows": int(dataframe.shape[0]), "columns": int(dataframe.shape[1])},
            "columns": [str(column) for column in dataframe.columns],
            "missing_values": _json_safe(dataframe.isna().sum().to_dict()),
            "numeric_summary": _describe(numeric),
            "categorical_summary": _categorical_summary(categorical),
            "error": None,
        }
    except Exception as exc:
        return _error_result("profile_dataset_tool", exc)


def aggregate_tool(
    dataset_path: str,
    group_by: str,
    metric: str,
    operation: str,
) -> dict[str, Any]:
    """Aggregate a metric column by a group column using a supported operation."""
    try:
        dataframe = _read_dataframe(dataset_path)
        _require_columns(dataframe, [group_by, metric])
        operation = operation.lower()
        if operation not in {"count", "mean", "sum", "min", "max"}:
            raise ValueError(f"Unsupported aggregation operation: {operation}")

        if operation == "count":
            result = dataframe.groupby(group_by, dropna=False)[metric].count()
        else:
            result = getattr(dataframe.groupby(group_by, dropna=False)[metric], operation)()

        rows = (
            result.reset_index(name=f"{operation}_{metric}")
            .head(100)
            .astype(object)
            .where(pd.notna(result.reset_index(name=f"{operation}_{metric}")), None)
        )
        return {
            "group_by": group_by,
            "metric": metric,
            "operation": operation,
            "rows": _records(rows),
            "error": None,
        }
    except Exception as exc:
        return _error_result("aggregate_tool", exc)


def correlation_tool(
    dataset_path: str,
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """Return numeric column correlations for selected or all numeric fields."""
    try:
        dataframe = _read_dataframe(dataset_path)
        if columns:
            _require_columns(dataframe, columns)
            dataframe = dataframe[columns]
        numeric = dataframe.select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("No numeric columns are available for correlation.")
        return {
            "columns": [str(column) for column in numeric.columns],
            "correlations": _json_safe(numeric.corr().round(4).to_dict()),
            "error": None,
        }
    except Exception as exc:
        return _error_result("correlation_tool", exc)


def basic_stats_tool(dataset_path: str, columns: list[str]) -> dict[str, Any]:
    """Return pandas describe output for selected numeric fields."""
    try:
        dataframe = _read_dataframe(dataset_path)
        if columns:
            _require_columns(dataframe, columns)
            dataframe = dataframe[columns]
        numeric = dataframe.select_dtypes(include="number")
        if numeric.empty:
            raise ValueError("No numeric columns are available for basic statistics.")
        return {
            "columns": [str(column) for column in numeric.columns],
            "summary": _describe(numeric),
            "error": None,
        }
    except Exception as exc:
        return _error_result("basic_stats_tool", exc)


def _read_dataframe(dataset_path: str) -> pd.DataFrame:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError("Dataset file does not exist.")
    if path.stat().st_size == 0:
        raise ValueError("Dataset file is empty.")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        with pd.ExcelFile(path) as excel_file:
            if not excel_file.sheet_names:
                raise ValueError("Excel file does not contain any sheets.")
            return pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
    raise ValueError(f"Unsupported dataset file type: {suffix}")


def _require_columns(dataframe: pd.DataFrame, columns: list[str]) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise ValueError(f"Column(s) not found in dataset: {', '.join(missing)}")


def _describe(dataframe: pd.DataFrame) -> dict[str, Any]:
    if dataframe.empty:
        return {}
    return _json_safe(dataframe.describe().round(4).to_dict())


def _categorical_summary(dataframe: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for column in dataframe.columns[:20]:
        series = dataframe[column]
        summary[str(column)] = {
            "unique_count": int(series.nunique(dropna=True)),
            "top_values": _json_safe(series.value_counts(dropna=False).head(5).to_dict()),
        }
    return summary


def _records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(column): _json_safe_value(value) for column, value in row.items()}
        for row in dataframe.to_dict(orient="records")
    ]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return _json_safe_value(value)


def _json_safe_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _error_result(tool_name: str, exc: Exception) -> dict[str, Any]:
    return {
        "error": {
            "tool": tool_name,
            "message": str(exc),
        }
    }
