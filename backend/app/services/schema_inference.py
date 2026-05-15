import re

import pandas as pd
from pandas.api import types as pd_types

CURRENCY_TERMS = {
    "revenue",
    "sales",
    "price",
    "cost",
    "profit",
    "income",
    "salary",
    "amount",
    "balance",
    "asset",
    "loan",
    "debt",
}
PERCENTAGE_TERMS = {"rate", "ratio", "percentage", "percent", "margin"}
DATE_TERMS = {"date", "time", "datetime", "created_at", "updated_at", "timestamp"}
ID_TERMS = {"id", "uuid", "guid", "key", "code", "number", "no"}


def normalize_column_name(column_name: str) -> str:
    normalized = column_name.strip().lower()
    normalized = re.sub(r"[$€£¥￥]", "", normalized)
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_") or "column"


def infer_semantic_type(series: pd.Series, normalized_column_name: str) -> str:
    name_parts = set(normalized_column_name.split("_"))
    lowered_name = normalized_column_name.lower()
    non_null = series.dropna()

    if _looks_like_datetime_name(lowered_name) or pd_types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd_types.is_bool_dtype(series):
        return "boolean"
    if _looks_like_id(lowered_name, name_parts):
        return "id"
    if _contains_any(lowered_name, CURRENCY_TERMS):
        return "currency"
    if _contains_any(lowered_name, PERCENTAGE_TERMS):
        return "percentage"
    if pd_types.is_numeric_dtype(series):
        return "numeric"

    unique_ratio = _unique_ratio(series)
    if non_null.empty:
        return "unknown"

    string_values = non_null.astype(str)
    average_length = string_values.str.len().mean()
    if unique_ratio <= 0.5 or non_null.nunique(dropna=True) <= 50:
        return "categorical"
    if unique_ratio > 0.8 or average_length > 50:
        return "text"
    return "unknown"


def infer_agent_flags(semantic_type: str) -> dict[str, bool]:
    return {
        "is_measure": semantic_type in {"numeric", "currency", "percentage"},
        "is_dimension": semantic_type in {"categorical", "boolean"},
        "is_time_column": semantic_type == "datetime",
        "is_identifier": semantic_type == "id",
    }


def _unique_ratio(series: pd.Series) -> float:
    total_count = len(series)
    if total_count == 0:
        return 0.0
    return float(series.nunique(dropna=True) / total_count)


def _looks_like_datetime_name(name: str) -> bool:
    parts = set(name.split("_"))
    return bool(parts & DATE_TERMS) or any(term in name for term in DATE_TERMS)


def _looks_like_id(name: str, parts: set[str]) -> bool:
    if "id" in parts:
        return True
    return name.endswith("_id") or name in ID_TERMS or any(name.endswith(f"_{term}") for term in ID_TERMS)


def _contains_any(name: str, terms: set[str]) -> bool:
    return any(term in name for term in terms)
