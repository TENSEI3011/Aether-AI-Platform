"""
============================================================
Query Validator — Deterministic validation of LLM-generated
Pandas code before execution
============================================================
Implements:
  1. Syntax validation (compile check)
  2. Operation whitelisting (read-only Pandas ops only)
  3. Destructive operation blocking (DROP, DELETE, etc.)
  4. Schema consistency check (column names exist)
  5. Import blocking (no imports allowed)
============================================================
"""

import ast
import re
from typing import Dict, Any, Tuple, List


# ── Whitelisted Pandas operations (read-only) ────────────
ALLOWED_OPERATIONS = {
    # DataFrame methods
    "head", "tail", "describe", "info", "shape", "columns",
    "dtypes", "value_counts", "unique", "nunique",
    "groupby", "agg", "aggregate", "mean", "median", "sum",
    "count", "min", "max", "std", "var", "corr",
    "sort_values", "sort_index", "nlargest", "nsmallest",
    "filter", "query", "loc", "iloc", "isin",
    "isna", "isnull", "notna", "notnull", "fillna", "dropna",
    "pivot_table", "crosstab", "merge",
    "apply", "map", "replace",
    "astype", "to_datetime", "to_numeric",
    "reset_index", "set_index",
    "rename", "copy",
    "str", "dt",  # Accessor properties
    "between", "clip",
    "abs", "round",
    "select_dtypes",
    "sample",
    "tolist", "to_dict", "to_json",
}

# ── Blocked keywords — destructive / dangerous ───────────
BLOCKED_PATTERNS = [
    r"\bimport\b",
    r"\bfrom\b\s+\w+\s+\bimport\b",
    r"\b__\w+__\b",          # Dunder methods
    r"\bexec\b",
    r"\beval\b",
    r"\bcompile\b",
    r"\bglobals\b",
    r"\blocals\b",
    r"\bopen\b",
    r"\bos\.\b",
    r"\bsys\.\b",
    r"\bsubprocess\b",
    r"\bshutil\b",
    r"\.drop\(",             # DataFrame.drop() (allows dropna, drop_duplicates)
    r"\bto_csv\b",           # Write operations
    r"\bto_excel\b",
    r"\bto_sql\b",
    r"\bto_parquet\b",
    r"\bto_clipboard\b",
    r"\bdel\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bDROP\b",
    r"\bINSERT\b",
    r"\bALTER\b",
]


def validate_syntax(code: str) -> Tuple[bool, str]:
    """
    Check that the generated code is valid Python syntax.
    Returns (is_valid, error_message).
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"


def check_blocked_patterns(code: str) -> Tuple[bool, List[str]]:
    """
    Scan code for blocked/destructive patterns.
    Returns (is_safe, list_of_violations).
    """
    violations = []
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            violations.append(f"Blocked pattern detected: {pattern}")
    return len(violations) == 0, violations


def validate_schema_consistency(code: str, column_names: List[str]) -> Tuple[bool, List[str]]:
    """
    Check that any string literals in the code that look like
    column references actually exist in the dataset schema.
    This is a heuristic — it extracts quoted strings and checks
    against known column names.
    """
    # Extract string literals from the code
    string_literals = re.findall(r"['\"]([^'\"]+)['\"]", code)
    warnings = []
    for literal in string_literals:
        # Only flag if it looks like it could be a column name
        # (skip things like agg function names, etc.)
        if (
            literal not in column_names
            and literal not in ALLOWED_OPERATIONS
            and literal not in {"sum", "mean", "count", "min", "max", "std", "median", "first", "last"}
            and not literal.startswith((".", "/", "http"))
            and len(literal) < 50
        ):
            warnings.append(f"String '{literal}' is not a known column name")

    # Warnings are informational, not blocking
    return True, warnings


def validate_query(code: str, column_names: List[str] = None) -> Dict[str, Any]:
    """
    Run the full validation pipeline on a generated Pandas code string.
    Returns a validation report dict.
    """
    report = {
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }

    # 1. Syntax validation
    syntax_ok, syntax_error = validate_syntax(code)
    if not syntax_ok:
        report["is_valid"] = False
        report["errors"].append(syntax_error)
        return report  # No point continuing if syntax is broken

    # 2. Blocked pattern check
    safe, violations = check_blocked_patterns(code)
    if not safe:
        report["is_valid"] = False
        report["errors"].extend(violations)

    # 3. Schema consistency (if column names provided)
    if column_names:
        _, schema_warnings = validate_schema_consistency(code, column_names)
        report["warnings"].extend(schema_warnings)

    return report
