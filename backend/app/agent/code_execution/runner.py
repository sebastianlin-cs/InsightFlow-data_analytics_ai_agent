from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from app.agent.code_execution.result_parser import normalize_execution_payload
from app.agent.code_execution.schemas import CodeExecutionResult


def run_generated_code_subprocess(
    *,
    code: str,
    dataset_path: str,
    session_id: int,
    timeout_seconds: int = 8,
    output_dir: str,
    chart_output_dir: str,
) -> CodeExecutionResult:
    """Run validated generated code in a timeout-limited child Python process."""
    start = time.perf_counter()
    resolved_dataset_path = Path(dataset_path).resolve()
    if not resolved_dataset_path.exists():
        return {
            "status": "error",
            "answer": None,
            "tables": {},
            "charts": [],
            "metadata": {"runner": "subprocess"},
            "stdout": "",
            "stderr": "",
            "error": f"Dataset file does not exist: {resolved_dataset_path}",
            "execution_time_ms": _elapsed_ms(start),
        }
    output_path = Path(output_dir)
    chart_path = Path(chart_output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    chart_path.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"insightflow_code_session_{session_id}_") as tmpdir:
        tmp_path = Path(tmpdir)
        code_file = tmp_path / "generated_analysis.py"
        runner_file = tmp_path / "runner.py"
        result_file = tmp_path / "result.json"
        code_file.write_text(code, encoding="utf-8")
        runner_file.write_text(_runner_script(), encoding="utf-8")

        command = [
            sys.executable,
            str(runner_file),
            str(code_file),
            str(resolved_dataset_path),
            str(result_file),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(tmp_path),
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "timeout",
                "answer": None,
                "tables": {},
                "charts": [],
                "metadata": {"runner": "subprocess", "timeout_seconds": timeout_seconds},
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "error": f"Generated code timed out after {timeout_seconds} seconds.",
                "execution_time_ms": _elapsed_ms(start),
            }

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if not result_file.exists():
            return {
                "status": "error",
                "answer": None,
                "tables": {},
                "charts": [],
                "metadata": {"runner": "subprocess", "returncode": completed.returncode},
                "stdout": stdout,
                "stderr": stderr,
                "error": "Generated code did not produce a result.json file.",
                "execution_time_ms": _elapsed_ms(start),
            }

        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {
                "status": "error",
                "answer": None,
                "tables": {},
                "charts": [],
                "metadata": {"runner": "subprocess", "returncode": completed.returncode},
                "stdout": stdout,
                "stderr": stderr,
                "error": f"result.json was not valid JSON: {exc}",
                "execution_time_ms": _elapsed_ms(start),
            }

        result = normalize_execution_payload(
            payload,
            stdout=stdout,
            stderr=stderr,
            execution_time_ms=_elapsed_ms(start),
        )
        result["metadata"] = {
            **result.get("metadata", {}),
            "runner": "subprocess",
            "returncode": completed.returncode,
            "timeout_seconds": timeout_seconds,
        }
        return result


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _runner_script() -> str:
    return r'''
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _read_dataframe(dataset_path):
    path = Path(dataset_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        with pd.ExcelFile(path) as excel_file:
            if not excel_file.sheet_names:
                raise ValueError("Excel file does not contain any sheets.")
            return pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0])
    raise ValueError(f"Unsupported dataset file type: {suffix}")


def _write_result(result_path, payload):
    Path(result_path).write_text(json.dumps(_json_safe(payload)), encoding="utf-8")


def main():
    code_path, dataset_path, result_path = sys.argv[1:4]
    namespace = {"pd": pd, "np": np}
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        namespace["plt"] = plt
    except Exception:
        namespace["plt"] = None

    try:
        code = Path(code_path).read_text(encoding="utf-8")
        exec(compile(code, str(code_path), "exec"), namespace)
        analyze = namespace.get("analyze")
        if not callable(analyze):
            raise ValueError("Generated code did not define analyze(df).")
        df = _read_dataframe(dataset_path)
        result = analyze(df)
        if not isinstance(result, dict):
            raise ValueError("analyze(df) must return a dictionary.")
        payload = {
            "status": "success",
            "answer": result.get("answer"),
            "tables": result.get("tables", {}),
            "charts": result.get("charts", []),
            "metadata": result.get("metadata", {}),
            "error": None,
        }
        _write_result(result_path, payload)
    except Exception as exc:
        payload = {
            "status": "error",
            "answer": None,
            "tables": {},
            "charts": [],
            "metadata": {},
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(limit=6),
        }
        _write_result(result_path, payload)


if __name__ == "__main__":
    main()
'''.lstrip()
