"""
============================================================
Query Executor — Executes validated Pandas code safely
============================================================
Key safety measures:
  1. Operates on an IN-MEMORY COPY of the DataFrame
  2. Only executes code that passed the validation layer
  3. AST-level attribute access blocking (dunder traversal)
  4. Restricted execution namespace (no builtins)
  5. Timeout protection against infinite loops
  6. Returns structured JSON results
============================================================
"""

import ast
import pandas as pd
import json
import signal
import threading
from typing import Dict, Any


# ── AST safety checker ────────────────────────────────────
# Blocks object-traversal attacks like:
#   ().__class__.__mro__[1].__subclasses__()
# which bypass __builtins__={} sandboxing.

_BLOCKED_ATTRS = {
    "__class__", "__mro__", "__subclasses__", "__bases__",
    "__globals__", "__code__", "__func__", "__self__",
    "__dict__", "__init__", "__new__", "__del__",
    "__getattr__", "__getattribute__", "__setattr__",
    "__delattr__", "__import__", "__builtins__",
    "__loader__", "__spec__", "__module__",
}


def _check_ast_safety(code: str) -> None:
    """
    Parse the code and walk the AST to reject dangerous patterns.
    Raises ValueError if any blocked attribute access is found.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in generated code: {e}")

    for node in ast.walk(tree):
        # Block dunder attribute access: obj.__class__, etc.
        if isinstance(node, ast.Attribute):
            if node.attr in _BLOCKED_ATTRS:
                raise ValueError(
                    f"Blocked attribute access: '{node.attr}' — "
                    f"potential sandbox escape"
                )
            # Block any double-underscore attribute
            if node.attr.startswith("__") and node.attr.endswith("__"):
                raise ValueError(
                    f"Blocked dunder attribute: '{node.attr}'"
                )

        # Block import statements
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Import statements are not allowed")

        # Block exec/eval/compile calls
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {
                "exec", "eval", "compile", "open",
                "getattr", "setattr", "delattr",
                "__import__", "globals", "locals",
                "breakpoint", "exit", "quit",
            }:
                raise ValueError(
                    f"Blocked function call: '{func.id}'"
                )


# ── Timeout helper (cross-platform) ──────────────────────

class _ExecutionTimeout(Exception):
    """Raised when code execution exceeds the time limit."""
    pass


def _run_with_timeout(func, timeout_seconds=5):
    """
    Run func() in a thread with a timeout.
    Returns the result or raises _ExecutionTimeout.
    """
    result = [None]
    error = [None]

    def target():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        raise _ExecutionTimeout(
            f"Code execution timed out after {timeout_seconds} seconds"
        )
    if error[0] is not None:
        raise error[0]
    return result[0]


def execute_query(df: pd.DataFrame, code: str) -> Dict[str, Any]:
    """
    Execute a validated Pandas code string on a COPY of the
    DataFrame. Returns a structured result dict.

    Parameters:
        df: The original DataFrame (will NOT be mutated)
        code: Validated Pandas code string

    Returns:
        {
            "success": bool,
            "data": list of dicts (table rows),
            "columns": list of column names,
            "row_count": int,
            "error": str or None
        }
    """
    try:
        # ── AST safety check — blocks dunder traversal ────────
        _check_ast_safety(f"__result__ = {code}")

        # ── Create an in-memory copy — original is never touched ──
        df_copy = df.copy()

        # ── Restricted execution namespace ────────────────────────
        # Only pandas and the DataFrame copy are available.
        # No builtins, no imports, no file I/O.
        exec_namespace = {
            "df": df_copy,
            "pd": pd,
        }

        # ── Execute the code with timeout ─────────────────────────
        wrapped_code = f"__result__ = {code}"

        def _do_exec():
            exec(wrapped_code, {"__builtins__": {}}, exec_namespace)
            return exec_namespace.get("__result__", None)

        result = _run_with_timeout(_do_exec, timeout_seconds=10)

        # ── Format the result ─────────────────────────────────────
        if isinstance(result, pd.DataFrame):
            # Limit to 500 rows for safety
            truncated = result.head(500)
            return {
                "success": True,
                "data": json.loads(truncated.to_json(orient="records", date_format="iso")),
                "columns": list(truncated.columns),
                "row_count": int(len(result)),
                "error": None,
            }
        elif isinstance(result, pd.Series):
            result_df = result.reset_index()
            # Preserve real column names: index.name = group key, series.name = metric
            idx_name   = result.index.name or "index"
            val_name   = result.name or "value"
            if len(result_df.columns) == 2:
                result_df.columns = [idx_name, val_name]
            return {
                "success": True,
                "data": json.loads(result_df.to_json(orient="records", date_format="iso")),
                "columns": list(result_df.columns),
                "row_count": int(len(result)),
                "error": None,
            }
        elif isinstance(result, (int, float)):
            return {
                "success": True,
                "data": [{"value": result}],
                "columns": ["value"],
                "row_count": 1,
                "error": None,
            }
        else:
            return {
                "success": True,
                "data": [{"value": str(result)}],
                "columns": ["value"],
                "row_count": 1,
                "error": None,
            }

    except _ExecutionTimeout as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "error": str(e),
        }
    except ValueError as e:
        # AST safety violations
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "error": f"Security check failed: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "error": str(e),
        }
