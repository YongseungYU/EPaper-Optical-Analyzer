"""Export utilities for generating Excel files."""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd


def export_to_excel(
    df: pd.DataFrame,
    sheet_name: str = "Results",
    filename: Optional[str] = None,
) -> bytes:
    """Export a DataFrame to an Excel file and return bytes.

    Parameters
    ----------
    df : pd.DataFrame
        Data to export.
    sheet_name : str
        Name of the Excel worksheet.
    filename : str, optional
        Not used for bytes output; kept for API consistency.

    Returns
    -------
    bytes
        Excel file content as bytes (for Streamlit download).
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()
