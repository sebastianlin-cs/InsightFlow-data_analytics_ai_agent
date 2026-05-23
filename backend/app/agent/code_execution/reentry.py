from __future__ import annotations

from app.agent.code_execution.schemas import CodeExecutionResult, ReentryDecision, SafetyCheckResult

RETRYABLE_ERROR_TERMS = {
    "KeyError",
    "TypeError",
    "ValueError",
    "AttributeError",
    "NameError",
    "JSON",
    "not JSON serializable",
    "shape mismatch",
    "division by zero",
    "ZeroDivisionError",
}


def decide_reentry(
    *,
    execution_result: CodeExecutionResult,
    safety_result: SafetyCheckResult,
    retry_count: int,
    max_retries: int,
) -> ReentryDecision:
    """Decide whether a failed generated-code attempt should get one repair retry."""
    if retry_count >= max_retries:
        return {
            "should_retry": False,
            "reason": "Maximum debug retry count has already been reached.",
            "retry_type": None,
            "max_retry_reached": True,
        }
    if not safety_result.get("passed"):
        return {
            "should_retry": False,
            "reason": "Safety validation failed. The code will not be retried.",
            "retry_type": None,
            "max_retry_reached": False,
        }
    if execution_result.get("status") == "timeout":
        return {
            "should_retry": False,
            "reason": "Execution timed out. Timeout failures are not retried in v2.0.",
            "retry_type": None,
            "max_retry_reached": False,
        }
    if execution_result.get("status") != "error":
        return {
            "should_retry": False,
            "reason": "Execution did not fail with a retryable runtime error.",
            "retry_type": None,
            "max_retry_reached": False,
        }

    error = execution_result.get("error") or execution_result.get("stderr") or ""
    if any(term in error for term in RETRYABLE_ERROR_TERMS):
        return {
            "should_retry": True,
            "reason": f"The code failed with a retryable error: {error}",
            "retry_type": "debug_generated_code",
            "max_retry_reached": False,
        }
    return {
        "should_retry": False,
        "reason": f"The execution error is not retryable in v2.0: {error}",
        "retry_type": None,
        "max_retry_reached": False,
    }
