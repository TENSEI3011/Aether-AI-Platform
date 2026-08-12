"""
============================================================
LLM Prompt Templates — Structured prompts for code generation
============================================================
These templates provide context and instructions to the LLM
so it generates valid, safe Pandas code.

ENHANCED:
  ✅ Conversation history injection (ICL / multi-turn context)
  ✅ Semantic column hints at top of prompt
  ✅ Few-shot examples (3 worked input→output pairs)
     — LLMs are dramatically more accurate with examples,
       especially for groupby, filtering, and aggregations.
  ✅ Numeric range context in schema (from schema_extractor)
  ✅ Dedicated self-correction prompt (build_correction_prompt)
============================================================
"""


# ── 8 diverse few-shot examples covering the most common query patterns ──
# LLMs are highly sensitive to example quality and coverage.
# More patterns = fewer hallucinated column names and wrong aggregations.
_FEW_SHOT_EXAMPLES = """
EXAMPLES (reference these patterns exactly):

Example 1 — Grouped average:
  Question: "What is the average salary by department?"
  Code: df.groupby('department')['salary'].mean().reset_index()

Example 2 — Filtered rows:
  Question: "Show all employees with salary greater than 80000"
  Code: df[df['salary'] > 80000]

Example 3 — Count per category:
  Question: "How many orders are in each region?"
  Code: df.groupby('region')['order_id'].count().reset_index().rename(columns={'order_id': 'count'})

Example 4 — Top-N with sorting:
  Question: "Show the top 5 products by revenue"
  Code: df.groupby('product')['revenue'].sum().reset_index().nlargest(5, 'revenue')

Example 5 — Date-based grouping:
  Question: "What is the total sales per month?"
  Code: df.groupby(df['date'].dt.to_period('M').astype(str))['sales'].sum().reset_index()

Example 6 — Percentage / proportion:
  Question: "What percentage of orders are from each category?"
  Code: (df['category'].value_counts(normalize=True) * 100).round(2).reset_index().rename(columns={'proportion': 'percentage'})

Example 7 — Multi-column aggregation:
  Question: "Show mean, max, and count of sales by region"
  Code: df.groupby('region')['sales'].agg(['mean', 'max', 'count']).reset_index()

Example 8 — Filter out nulls and correlate:
  Question: "What is the correlation between age and income?"
  Code: df[['age', 'income']].dropna().corr()
""".strip()


def build_analysis_prompt(
    natural_query: str,
    schema_summary: str,
    conversation_history: str = "",
) -> str:
    """
    Build a prompt that instructs the LLM to generate
    a single Pandas expression for the user's question.

    Parameters:
        natural_query:        The user's current question
        schema_summary:       Schema context (with optional semantic hints)
        conversation_history: Prior Q&A turns for multi-turn ICL context
    """
    history_block = ""
    if conversation_history:
        history_block = f"\n{conversation_history}\n"

    return f"""You are a data analysis assistant. You ONLY generate valid Python Pandas code.

RULES:
1. Generate EXACTLY ONE Pandas expression (no imports, no print statements)
2. The DataFrame is called `df`
3. Use ONLY read-only operations (no drop, delete, to_csv, etc.)
4. Reference only columns that exist in the schema below
5. Return a DataFrame, Series, or scalar value
6. If the question is a follow-up (e.g. "now filter only X"), use the conversation history to understand context
7. Use the numeric ranges in the schema to generate correct filter thresholds
8. Use the top_values listed for categorical columns when filtering by category name
{history_block}
{_FEW_SHOT_EXAMPLES}

DATASET SCHEMA:
{schema_summary}

USER QUESTION: {natural_query}

Generate a single Pandas expression:
"""


def build_correction_prompt(
    natural_query: str,
    schema_summary: str,
    failed_code: str,
    error_message: str,
) -> str:
    """
    Self-correction prompt: ask the LLM to fix its own failed code.
    ML Concept: Agentic LLM loop — error as feedback signal.

    FIXED: This is now called directly (not via build_analysis_prompt)
    so Gemini actually sees the failed code + error message.
    """
    return f"""You are a data analysis assistant. Your previous Pandas code failed. Fix it.

ORIGINAL QUESTION: {natural_query}

FAILED CODE:
{failed_code}

ERROR MESSAGE:
{error_message}

DATASET SCHEMA:
{schema_summary}

RULES:
1. Generate EXACTLY ONE corrected Pandas expression
2. The DataFrame is called `df`
3. Use ONLY read-only Pandas operations
4. Reference only columns that exist in the schema
5. Address the specific error shown above

Write the CORRECTED Pandas expression:
"""


def build_explanation_prompt(code: str, result_summary: str) -> str:
    """
    Build a prompt that instructs the LLM to explain
    the analysis result in plain English.
    """
    return f"""Explain the following data analysis result in simple, non-technical language.
Keep it to 2-3 sentences.

CODE: {code}
RESULT: {result_summary}

Explanation:
"""
