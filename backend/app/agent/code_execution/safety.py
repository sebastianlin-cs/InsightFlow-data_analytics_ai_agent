from __future__ import annotations

import ast
from typing import Any

from app.agent.code_execution.schemas import SafetyCheckResult

ALLOWED_FUNCTION_NAME = "analyze"
ALLOWED_IMPORTS = {"pandas", "numpy", "matplotlib", "matplotlib.pyplot"}
FORBIDDEN_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "pathlib",
    "shutil",
    "pickle",
    "multiprocessing",
    "threading",
}
FORBIDDEN_CALLS = {
    "open",
    "eval",
    "exec",
    "compile",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "read_csv",
    "read_excel",
    "read_pickle",
    "read_parquet",
    "read_json",
    "read_sql",
    "to_csv",
    "to_excel",
    "to_pickle",
    "to_parquet",
    "to_json",
    "savefig",
}
FORBIDDEN_ATTRIBUTES = {
    "__dict__",
    "__class__",
    "__bases__",
    "__subclasses__",
    "__globals__",
    "__code__",
}


def validate_generated_code(code: str) -> SafetyCheckResult:
    """Validate generated code with conservative AST checks before subprocess execution."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return _fail(f"Code did not parse: {exc}", [str(exc)])

    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    invalid_top_level = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom))
    ]
    if len(functions) != 1 or invalid_top_level:
        return _fail(
            "Code must define exactly one top-level function plus optional safe imports.",
            ["top_level"],
        )

    function = functions[0]
    if function.name != ALLOWED_FUNCTION_NAME:
        return _fail("Function must be named analyze.", [function.name])
    args = function.args.args
    if len(args) != 1 or args[0].arg != "df":
        return _fail("analyze must accept exactly one parameter named df.", ["signature"])
    if not any(isinstance(node, ast.Return) for node in ast.walk(function)):
        return _fail("analyze must contain a return statement.", ["return"])

    for node in ast.walk(tree):
        blocked = _blocked_node(node)
        if blocked:
            return _fail(blocked[0], blocked[1])

    return {
        "passed": True,
        "reason": None,
        "blocked_items": [],
        "warnings": [],
    }


def _blocked_node(node: ast.AST) -> tuple[str, list[str]] | None:
    if isinstance(node, ast.Import):
        for alias in node.names:
            module = alias.name
            if _is_forbidden_import(module):
                return f"Forbidden import: {module}", [module]
            if module not in ALLOWED_IMPORTS:
                return f"Import is not allowed: {module}", [module]
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        if _is_forbidden_import(module):
            return f"Forbidden import: {module}", [module]
        if module not in ALLOWED_IMPORTS:
            return f"Import is not allowed: {module}", [module]
    if isinstance(node, ast.Call):
        call_name = _call_name(node.func)
        if call_name in FORBIDDEN_CALLS:
            return f"Forbidden function call: {call_name}", [call_name]
    if isinstance(node, ast.Attribute):
        if node.attr in FORBIDDEN_ATTRIBUTES:
            return f"Forbidden attribute access: {node.attr}", [node.attr]
    if isinstance(node, ast.While):
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            return "while True loops are not allowed.", ["while True"]
    return None


def _is_forbidden_import(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in FORBIDDEN_IMPORTS


def _call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _fail(reason: str, blocked_items: list[str]) -> SafetyCheckResult:
    return {
        "passed": False,
        "reason": reason,
        "blocked_items": blocked_items,
        "warnings": [],
    }
