from pathlib import Path
from typing import Any

import pandas as pd


def generate_chart_tool(
    dataset_path: str,
    chart_type: str,
    x: str | None,
    y: str | None,
    aggregation: str | None,
    output_dir: str,
) -> dict[str, Any]:
    """Generate a simple matplotlib chart and return filesystem and URL paths."""
    try:
        dataframe = _read_dataframe(dataset_path)
        chart_type = chart_type or _default_chart_type(dataframe, x, y)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(9, 5))
        if chart_type in {"bar", "line"}:
            if not x or not y:
                raise ValueError("Bar and line charts require both x and y fields.")
            _require_columns(dataframe, [x, y])
            operation = aggregation or "mean"
            if operation not in {"count", "mean", "sum", "min", "max"}:
                operation = "mean"
            grouped = _aggregate_for_chart(dataframe, x, y, operation).head(30)
            if chart_type == "bar":
                ax.bar(grouped[x].astype(str), grouped[y])
                ax.tick_params(axis="x", rotation=35)
            else:
                ax.plot(grouped[x].astype(str), grouped[y], marker="o")
                ax.tick_params(axis="x", rotation=35)
        elif chart_type == "histogram":
            column = y or x or _first_numeric_column(dataframe)
            if not column:
                raise ValueError("Histogram requires a numeric field.")
            _require_columns(dataframe, [column])
            dataframe[column].dropna().plot(kind="hist", ax=ax, bins=20)
            ax.set_xlabel(column)
        elif chart_type == "scatter":
            if not x or not y:
                numeric_columns = list(dataframe.select_dtypes(include="number").columns)
                if len(numeric_columns) < 2:
                    raise ValueError("Scatter chart requires two numeric fields.")
                x, y = str(numeric_columns[0]), str(numeric_columns[1])
            _require_columns(dataframe, [x, y])
            ax.scatter(dataframe[x], dataframe[y], alpha=0.75)
            ax.set_xlabel(x)
            ax.set_ylabel(y)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        ax.set_title(f"{chart_type.title()} chart")
        fig.tight_layout()
        filename = "chart.png"
        file_path = output_path / filename
        fig.savefig(file_path)
        plt.close(fig)

        return {
            "chart_type": chart_type,
            "chart_path": str(file_path),
            "chart_url": f"/charts/{output_path.name}/{filename}",
            "x": x,
            "y": y,
            "aggregation": aggregation,
            "error": None,
        }
    except Exception as exc:
        return {
            "error": {
                "tool": "generate_chart_tool",
                "message": str(exc),
            }
        }


def _read_dataframe(dataset_path: str) -> pd.DataFrame:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError("Dataset file does not exist.")
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


def _aggregate_for_chart(
    dataframe: pd.DataFrame,
    x: str,
    y: str,
    operation: str,
) -> pd.DataFrame:
    if operation == "count":
        result = dataframe.groupby(x, dropna=False)[y].count()
    else:
        result = getattr(dataframe.groupby(x, dropna=False)[y], operation)()
    return result.reset_index(name=y)


def _default_chart_type(dataframe: pd.DataFrame, x: str | None, y: str | None) -> str:
    if x and y:
        if _is_time_like(dataframe[x]) if x in dataframe.columns else False:
            return "line"
        return "bar"
    if y or x:
        return "histogram"
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    return "scatter" if len(numeric_columns) >= 2 else "histogram"


def _is_time_like(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    converted = pd.to_datetime(series, errors="coerce")
    return bool(converted.notna().mean() > 0.8)


def _first_numeric_column(dataframe: pd.DataFrame) -> str | None:
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    return str(numeric_columns[0]) if numeric_columns else None
