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
6. Do NOT use exec, eval, open, os, sys, subprocess, or any dangerous functions
7. Column names are CASE-SENSITIVE — use them exactly as shown in the schema

DATASET SCHEMA:
{schema_summary}

USER QUESTION: {natural_query}

Return ONLY the Pandas expression inside a ```python code block. No explanations outside the block.
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


def build_contextual_prompt(
    natural_query: str,
    schema_summary: str,
    context_string: str,
) -> str:
    """
    Build a prompt with conversation history context
    so the LLM can handle follow-up questions.
    """
    return f"""You are a data analysis assistant. You ONLY generate valid Python Pandas code.

RULES:
1. Generate EXACTLY ONE Pandas expression (no imports, no print statements)
2. The DataFrame is called `df`
3. Use ONLY read-only operations (no drop, delete, to_csv, etc.)
4. Reference only columns that exist in the schema below
5. Return a DataFrame, Series, or scalar value
6. Do NOT use exec, eval, open, os, sys, subprocess, or any dangerous functions
7. Column names are CASE-SENSITIVE — use them exactly as shown in the schema
8. If this is a follow-up question, modify the previous code based on the new request

DATASET SCHEMA:
{schema_summary}

{context_string}

USER QUESTION: {natural_query}

Return ONLY the Pandas expression inside a ```python code block. No explanations outside the block.
"""

