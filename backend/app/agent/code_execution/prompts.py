from __future__ import annotations

import json
from typing import Any


def build_code_generation_prompt(
    *,
    user_query: str,
    dataset_schema: list[dict[str, Any]],
    analysis_plan: list[str],
) -> str:
    """Build a JSON-only prompt for generating controlled pandas code."""
    return f"""
You are generating safe pandas analysis code for a data analysis agent.

You must generate exactly one Python function:

def analyze(df):
    ...

The dataframe df is already loaded by the system.
Do not read files.
Do not write files.
Do not connect to databases.
Do not access the network.
Do not use shell commands.
Do not use environment variables.

Allowed libraries:
- pandas as pd
- numpy as np
- matplotlib.pyplot as plt

Forbidden modules:
- os
- sys
- subprocess
- socket
- requests
- pathlib
- shutil
- pickle
- multiprocessing
- threading

Forbidden functions:
- open
- eval
- exec
- compile
- input
- __import__
- globals
- locals
- vars
- dir
- getattr
- setattr
- delattr

Rules:
1. Use only columns that exist in the provided schema.
2. Return a JSON-serializable dictionary.
3. The return dictionary must contain:
   - answer: string
   - tables: object
   - charts: list
   - metadata: object
4. Do not print as the main output.
5. Do not use infinite loops.
6. Do not mutate external state.
7. Keep the code simple and deterministic.
8. If division is used, guard against division by zero.
9. Convert NumPy scalar types to normal Python types when possible.
10. DataFrame outputs must be converted with to_dict(orient="records").

Dataset schema:
{json.dumps(_safe_schema(dataset_schema), ensure_ascii=False)}

User query:
{user_query}

Analysis plan:
{json.dumps(analysis_plan, ensure_ascii=False)}

Return JSON only:
{{
  "code": string,
  "explanation": string,
  "columns_used": string[],
  "expected_result_keys": string[]
}}
""".strip()


def build_code_repair_prompt(
    *,
    user_query: str,
    dataset_schema: list[dict[str, Any]],
    analysis_plan: list[str],
    previous_code: str,
    execution_error: str | None,
    stderr: str,
    retry_count: int,
    max_retries: int,
) -> str:
    """Build a JSON-only prompt for repairing one failed generated-code attempt."""
    return f"""
You are repairing previously generated pandas analysis code for a controlled data analysis agent.

The previous code failed during execution.
Your task is to produce a corrected version of the same analyze(df) function.

You must follow the same safety and output contract.

Important rules:
1. Generate exactly one function: def analyze(df):
2. Use only the dataframe df and allowed libraries.
3. Do not read files.
4. Do not access the network.
5. Do not use os, sys, subprocess, requests, socket, pathlib, shutil, pickle.
6. Do not call open(), eval(), exec(), compile(), input(), __import__(), globals(), locals().
7. Return a JSON-serializable dictionary with keys:
   - answer
   - tables
   - charts
   - metadata
8. Use only columns from the provided schema.
9. Fix the specific error shown below.
10. Do not add unrelated new analysis.
11. If the error cannot be safely fixed, return code that provides a clear answer explaining the limitation, with empty tables and charts.
12. If a requested column is missing, only substitute another column if there is an obvious close match. Otherwise explain that the requested column does not exist.

User query:
{user_query}

Dataset schema:
{json.dumps(_safe_schema(dataset_schema), ensure_ascii=False)}

Analysis plan:
{json.dumps(analysis_plan, ensure_ascii=False)}

Previous code:
{previous_code}

Execution error:
{execution_error}

stderr:
{stderr}

Retry count:
{retry_count} / {max_retries}

Return JSON only:
{{
  "code": string,
  "repair_explanation": string,
  "changed_columns": {{
    "removed": string[],
    "added": string[]
  }},
  "columns_used": string[],
  "expected_result_keys": string[]
}}
""".strip()


def build_code_response_prompt(
    *,
    user_query: str,
    execution_mode: str,
    analysis_plan: list[str],
    code_execution_result: dict[str, Any],
    reentry_info: dict[str, Any],
) -> str:
    """Build a JSON-only prompt for explaining a code execution result."""
    return f"""
You are generating a user-facing explanation for a data analysis result.

You must only use the provided execution result.
Do not invent numbers.
Do not invent columns.
Do not infer business causes unless directly supported by the result.
If execution failed, clearly explain the limitation and ask a helpful follow-up question.

User query:
{user_query}

Execution mode:
{execution_mode}

Analysis plan:
{json.dumps(analysis_plan, ensure_ascii=False)}

Code execution result:
{json.dumps(code_execution_result, ensure_ascii=False)}

Reentry/debug info:
{json.dumps(reentry_info, ensure_ascii=False)}

Return JSON only:
{{
  "answer": string,
  "follow_up_questions": string[],
  "result_summary": object
}}
""".strip()


def _safe_schema(schema: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "column_name": row.get("column_name"),
            "normalized_column_name": row.get("normalized_column_name"),
            "semantic_type": row.get("semantic_type"),
            "raw_data_type": row.get("raw_data_type"),
            "is_measure": row.get("is_measure"),
            "is_dimension": row.get("is_dimension"),
            "is_time_column": row.get("is_time_column"),
        }
        for row in schema
    ]
