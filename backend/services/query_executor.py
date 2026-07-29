"""
============================================================
Query Executor — Executes validated Pandas code safely
============================================================
Key safety measures:
  1. Operates on an IN-MEMORY COPY of the DataFrame
  2. Only executes code that passed the validation layer
  3. Restricted execution namespace (no builtins)
  4. Returns structured JSON results
============================================================
"""

import pandas as pd
import json
from typing import Dict, Any


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
        # ── Create an in-memory copy — original is never touched ──
        df_copy = df.copy()

        # ── Restricted execution namespace ────────────────────────
        # Only pandas and the DataFrame copy are available.
        # No builtins, no imports, no file I/O.
        exec_namespace = {
            "df": df_copy,
            "pd": pd,
        }

        # ── Execute the code ──────────────────────────────────────
        # The last expression's result is captured via `result`
        wrapped_code = f"__result__ = {code}"
        exec(wrapped_code, {"__builtins__": {}}, exec_namespace)

        result = exec_namespace.get("__result__", None)

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
            result_df.columns = ["index", "value"] if len(result_df.columns) == 2 else list(result_df.columns)
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

    except Exception as e:
        return {
            "success": False,
            "data": [],
            "columns": [],
            "row_count": 0,
            "error": str(e),
        }
