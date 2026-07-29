"""
============================================================
LLM Prompt Templates — Structured prompts for code generation
============================================================
These templates provide context and instructions to the LLM
so it generates valid, safe Pandas code.
============================================================
"""


def build_analysis_prompt(natural_query: str, schema_summary: str) -> str:
    """
    Build a prompt that instructs the LLM to generate
    a single Pandas expression for the user's question.
    """
    return f"""You are a data analysis assistant. You ONLY generate valid Python Pandas code.

RULES:
1. Generate EXACTLY ONE Pandas expression (no imports, no print statements)
2. The DataFrame is called `df`
3. Use ONLY read-only operations (no drop, delete, to_csv, etc.)
4. Reference only columns that exist in the schema below
5. Return a DataFrame, Series, or scalar value

DATASET SCHEMA:
{schema_summary}

USER QUESTION: {natural_query}

Generate a single Pandas expression:
"""


def build_explanation_prompt(code: str, result_summary: str) -> str:
    """
    Build a prompt that instructs the LLM to explain
    the analysis result in plain English.
    """
    return f"""Explain the following data analysis result in simple, non-technical language.
Keep it to 2–3 sentences.

CODE: {code}
RESULT: {result_summary}

Explanation:
"""
