"""
============================================================
Report Exporter — Generate downloadable Excel reports
============================================================
Converts query result data into XLSX format for download.
PDF and image exports are handled client-side.
============================================================
"""

import io
import pandas as pd
from typing import Dict, Any, List


def export_to_excel(data: List[Dict], columns: List[str]) -> bytes:
    """
    Convert query result data into an Excel file (XLSX bytes).

    Parameters:
        data: list of row dicts (from query executor)
        columns: list of column names

    Returns:
        bytes: XLSX file content
    """
    if not data:
        # Return an empty Excel file
        df = pd.DataFrame(columns=columns or ["No Data"])
    else:
        df = pd.DataFrame(data)
        # Reorder columns if provided
        if columns:
            existing = [c for c in columns if c in df.columns]
            if existing:
                df = df[existing]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Query Result")
    buffer.seek(0)

    return buffer.getvalue()
