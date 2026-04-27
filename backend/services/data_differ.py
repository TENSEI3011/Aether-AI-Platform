"""
============================================================
Data Differ — Compare Two Datasets
============================================================
Compares two DataFrames and returns:
  - Added rows (in df2 but not df1)
  - Removed rows (in df1 but not df2)
  - Summary stat deltas (mean, sum, count changes)
  - Column diffs (added/removed columns)
============================================================
"""

import pandas as pd
from typing import Dict, Any, List


def compare_datasets(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare two DataFrames and return a structured diff report.

    Parameters:
        df1: The "before" / baseline dataset
        df2: The "after" / comparison dataset

    Returns:
        {
            "summary": { rows_added, rows_removed, columns_added, columns_removed },
            "columns_added": [...],
            "columns_removed": [...],
            "stat_deltas": [ { column, before_mean, after_mean, delta, delta_pct } ],
            "sample_added": [...],   # up to 20 sample rows
            "sample_removed": [...], # up to 20 sample rows
        }
    """
    result = {}

    # ── Column Differences ────────────────────────────────
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    columns_added = sorted(cols2 - cols1)
    columns_removed = sorted(cols1 - cols2)
    common_cols = sorted(cols1 & cols2)

    result["columns_added"] = columns_added
    result["columns_removed"] = columns_removed

    # ── Row Differences (using common columns) ────────────
    if common_cols:
        # Convert to string for comparison to handle type mismatches
        df1_str = df1[common_cols].astype(str)
        df2_str = df2[common_cols].astype(str)

        # Create row hashes for set operations
        df1_hashes = df1_str.apply(lambda row: hash(tuple(row)), axis=1)
        df2_hashes = df2_str.apply(lambda row: hash(tuple(row)), axis=1)

        hash_set_1 = set(df1_hashes.values)
        hash_set_2 = set(df2_hashes.values)

        added_mask = df2_hashes.isin(hash_set_2 - hash_set_1)
        removed_mask = df1_hashes.isin(hash_set_1 - hash_set_2)

        rows_added = int(added_mask.sum())
        rows_removed = int(removed_mask.sum())

        # Sample rows
        result["sample_added"] = (
            df2[added_mask].head(20).to_dict("records") if rows_added > 0 else []
        )
        result["sample_removed"] = (
            df1[removed_mask].head(20).to_dict("records") if rows_removed > 0 else []
        )
    else:
        rows_added = len(df2)
        rows_removed = len(df1)
        result["sample_added"] = df2.head(20).to_dict("records")
        result["sample_removed"] = df1.head(20).to_dict("records")

    # ── Statistical Deltas (numeric columns) ──────────────
    stat_deltas = []
    numeric_common = [
        c for c in common_cols
        if pd.api.types.is_numeric_dtype(df1[c]) and pd.api.types.is_numeric_dtype(df2[c])
    ]

    for col in numeric_common:
        before_mean = float(df1[col].mean()) if not df1[col].empty else 0
        after_mean = float(df2[col].mean()) if not df2[col].empty else 0
        before_sum = float(df1[col].sum()) if not df1[col].empty else 0
        after_sum = float(df2[col].sum()) if not df2[col].empty else 0
        delta = after_mean - before_mean
        delta_pct = (delta / abs(before_mean) * 100) if before_mean != 0 else 0

        stat_deltas.append({
            "column": col,
            "before_mean": round(before_mean, 2),
            "after_mean": round(after_mean, 2),
            "before_sum": round(before_sum, 2),
            "after_sum": round(after_sum, 2),
            "delta": round(delta, 2),
            "delta_pct": round(delta_pct, 1),
        })

    result["stat_deltas"] = stat_deltas

    # ── Summary ───────────────────────────────────────────
    result["summary"] = {
        "before_rows": len(df1),
        "after_rows": len(df2),
        "rows_added": rows_added,
        "rows_removed": rows_removed,
        "columns_added": len(columns_added),
        "columns_removed": len(columns_removed),
        "common_columns": len(common_cols),
        "stat_changes": len([d for d in stat_deltas if abs(d["delta_pct"]) > 1]),
    }

    return result
