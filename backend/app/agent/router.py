from app.agent.state import AgentIntent


def route_intent(query: str) -> AgentIntent:
    """Classify the user query with deterministic rules for v1."""
    normalized = query.strip().lower()
    words = normalized.split()

    if len(words) < 2:
        return "clarification"

    unsupported_terms = {
        "predict",
        "forecast",
        "stock price",
        "train model",
        "machine learning",
        "join",
        "merge datasets",
        "sql",
    }
    if any(term in normalized for term in unsupported_terms):
        return "unsupported"

    if any(term in normalized for term in {"plot", "chart", "visualize", "graph"}):
        return "visualization"
    if any(term in normalized for term in {"columns", "schema", "fields", "catalog"}):
        return "schema_question"
    if any(
        term in normalized
        for term in {"overview", "summary", "summarize", "missing", "null", "describe"}
    ):
        return "data_overview"
    if any(
        term in normalized
        for term in {
            "average",
            "mean",
            "sum",
            "count",
            "group",
            " by ",
            "correlation",
            "statistics",
            "stats",
            "min",
            "max",
        }
    ):
        return "analysis"

    return "clarification"
