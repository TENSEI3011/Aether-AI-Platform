"""
============================================================
Utility Helpers — Shared utility functions
============================================================
"""

import os
from datetime import datetime


def ensure_directory(path: str) -> str:
    """Create a directory if it doesn't exist. Returns the path."""
    os.makedirs(path, exist_ok=True)
    return path


def generate_filename(original: str, prefix: str = "") -> str:
    """
    Generate a unique filename using timestamp.
    Preserves original extension.
    """
    name, ext = os.path.splitext(original)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}{timestamp}_{name}{ext}"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, adding ellipsis if trimmed."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
