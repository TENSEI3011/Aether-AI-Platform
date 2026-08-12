"""
============================================================
Query Executor — Executes validated Pandas code safely
============================================================
Key safety measures:
  1. Operates on an IN-MEMORY COPY of the DataFrame
  2. Only executes code that passed the validation layer
  3. Returns structured JSON results

ENHANCED:
  ✅ Multi-line code support — LLMs frequently generate
     multi-statement code (e.g. intermediate variables).
     ast introspection captures the last expression or
     assignment automatically without breaking on either.
============================================================
"""

import ast
import pandas as pd
import json
from typing import Dict, Any


def _is_single_expression(code: str) -> bool:
    """Return True if code is a single evaluable expression."""
    try:
        ast.parse(code, mode="eval")
        return True
    except SyntaxError:
        return False


def _get_last_result(code: str, exec_namespace: dict):
    """
    Execute multi-line code and return the value of the last statement.

    Strategy:
      - If last statement is an Expr (bare expression), evaluate it directly.
      - If last statement is an Assign, return the value of the assigned name.
      - Otherwise return None (result captured from namespace).
    """
    tree = ast.parse(code)
    if not tree.body:
        return None

    last_stmt = tree.body[-1]

    if isinstance(last_stmt, ast.Expr):
        # Last line is a bare expression — evaluate it
        exec(compile(tree, "<string>", "exec"), exec_namespace)
        return eval(
            compile(ast.Expression(body=last_stmt.value), "<string>", "eval"),
            exec_namespace,
        )

    if isinstance(last_stmt, ast.Assign):
        # Last line is an assignment — run all code then return the assigned var
        exec(compile(tree, "<string>", "exec"), exec_namespace)
        targets = last_stmt.targets
        if targets and isinstance(targets[0], ast.Name):
            return exec_namespace.get(targets[0].id)
        return None

    # Fallback: run all code, look for common result variable names
    exec(compile(tree, "<string>", "exec"), exec_namespace)
    for name in ("result", "output", "df_result", "out"):
        if name in exec_namespace:
            return exec_namespace[name]
    return None


def execute_query(df: pd.DataFrame, code: str) -> Dict[str, Any]:
    """
    Execute a validated Pandas code string on a COPY of the DataFrame.

    Handles both single-expression and multi-line code from the LLM.
    Returns a structured result dict.

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
        df_copy = df.copy()
        exec_namespace = {
            "df": df_copy,
            "pd": pd,
            "__builtins__": __builtins__,
        }

        # ── Execute ───────────────────────────────────────────────
        if _is_single_expression(code):
            # Fast path: single expression
            result = eval(compile(code, "<string>", "eval"), exec_namespace)
        else:
            # Multi-line path: exec + capture last result
            result = _get_last_result(code, exec_namespace)

        # ── Format result ─────────────────────────────────────────
        if isinstance(result, pd.DataFrame):
            truncated = result.head(500)
            return {
                "success":   True,
                "data":      json.loads(truncated.to_json(orient="records", date_format="iso")),
                "columns":   list(truncated.columns),
                "row_count": int(len(result)),
                "error":     None,
            }
        elif isinstance(result, pd.Series):
            result_df = result.reset_index()
            if len(result_df.columns) == 2:
                result_df.columns = [str(result_df.columns[0]), "value"]
            return {
                "success":   True,
                "data":      json.loads(result_df.to_json(orient="records", date_format="iso")),
                "columns":   list(result_df.columns),
                "row_count": int(len(result)),
                "error":     None,
            }
        elif isinstance(result, (int, float)):
            return {
                "success":   True,
                "data":      [{"value": result}],
                "columns":   ["value"],
                "row_count": 1,
                "error":     None,
            }
        elif result is None:
            return {
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "error": "Code executed but produced no output. Make sure the last line is an expression that returns a value.",
            }
        else:
            return {
                "success":   True,
                "data":      [{"value": str(result)}],
                "columns":   ["value"],
                "row_count": 1,
                "error":     None,
            }

    except Exception as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "error": str(e),
        }
