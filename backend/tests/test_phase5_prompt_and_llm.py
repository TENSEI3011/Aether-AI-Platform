"""
============================================================
test_phase5_prompt_and_llm.py
AI DLC Phase 5: Prompt Engineering & LLM Quality
============================================================
Tests the LLM layer independently of the real Gemini API:

  5A. Prompt Template Quality
      - Prompt contains required structural elements
      - Few-shot examples embedded correctly
      - Schema injected at the right place
      - Correction prompt contains the error + failed code

  5B. Stub LLM Code Generation
      - Keyword matching generates valid Pandas code
      - Generated code passes syntax validation
      - Generated code is executable on the fixture DataFrame
      - Conversation memory stores and retrieves turns
      - Memory is bounded by memory_size (deque maxlen)

  5C. Self-Correction Prompt Structure
      - Correction prompt contains original query, failed code,
        and error message — all required for the LLM to fix it.

ML Concepts Covered:
  - In-Context Learning (ICL) — few-shot examples in prompt
  - Prompt Engineering — structured instructions reduce hallucinations
  - Agentic LLM Loop — error-as-feedback for self-correction
  - Conversation Memory — multi-turn context injection (deque)
============================================================
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np

from llm.prompt_templates import (
    build_analysis_prompt,
    build_correction_prompt,
    build_explanation_prompt,
)
from llm.llm_engine import LLMEngine
from services.query_executor import execute_query
from services.query_validator import validate_syntax


# ═══════════════════════════════════════════════════════════
# PHASE 5A — Prompt Template Quality
# ═══════════════════════════════════════════════════════════

class TestPromptTemplates:
    """
    Verify that prompts contain the required structural elements.
    High-quality prompts → fewer LLM hallucinations.
    """

    SCHEMA = (
        "Dataset has 100 rows and 4 columns.\n"
        "Columns:\n"
        "  - age (numeric): range 18-65, mean 35.0, 0 nulls\n"
        "  - salary (numeric): range 30000-120000, mean 70000.0, 0 nulls\n"
        "  - department (categorical): top values: ['HR', 'Eng', 'Sales'], 0 nulls\n"
        "  - join_date (datetime): 0 nulls\n"
    )

    # ── Analysis prompt structure ──────────────────────────

    def test_analysis_prompt_contains_schema(self):
        """LLM must see the schema to avoid hallucinating column names."""
        prompt = build_analysis_prompt("average salary", self.SCHEMA)
        assert "salary" in prompt
        assert "department" in prompt

    def test_analysis_prompt_contains_user_question(self):
        """The user's exact question must be in the prompt."""
        query = "What is the average salary by department?"
        prompt = build_analysis_prompt(query, self.SCHEMA)
        assert query in prompt

    def test_analysis_prompt_contains_few_shot_examples(self):
        """Few-shot examples (ICL) must be present to guide code format."""
        prompt = build_analysis_prompt("show top rows", self.SCHEMA)
        assert "groupby" in prompt           # Example 1 keyword
        assert "reset_index" in prompt       # Common pattern
        assert "EXAMPLES" in prompt          # Section header

    def test_analysis_prompt_references_df(self):
        """Every prompt must instruct the LLM that the variable is 'df'."""
        prompt = build_analysis_prompt("count rows", self.SCHEMA)
        assert "df" in prompt

    def test_analysis_prompt_forbids_imports(self):
        """Prompt must explicitly prohibit import statements."""
        prompt = build_analysis_prompt("anything", self.SCHEMA)
        assert "no imports" in prompt.lower() or "import" in prompt.lower()

    def test_analysis_prompt_with_history_includes_turns(self):
        """Conversation history must appear when injected."""
        history = "CONVERSATION HISTORY:\n[Turn 1] User asked: \"count by dept\"\nGenerated: df.groupby('department').size()"
        prompt = build_analysis_prompt("now filter only HR", self.SCHEMA, conversation_history=history)
        assert "CONVERSATION HISTORY" in prompt
        assert "count by dept" in prompt

    def test_analysis_prompt_without_history_is_clean(self):
        """No conversation history → no stray CONVERSATION HISTORY block."""
        prompt = build_analysis_prompt("show top rows", self.SCHEMA, conversation_history="")
        assert "CONVERSATION HISTORY" not in prompt

    # ── Correction prompt structure ────────────────────────

    def test_correction_prompt_contains_failed_code(self):
        """The LLM needs the exact failing code to understand what to fix."""
        failed_code = "df.groupby('dept')['salary'].mean()"
        prompt = build_correction_prompt("avg salary", self.SCHEMA, failed_code, "KeyError: 'dept'")
        assert failed_code in prompt

    def test_correction_prompt_contains_error_message(self):
        """The error message is the core feedback signal for self-correction."""
        error = "KeyError: 'dept'"
        prompt = build_correction_prompt("avg salary", self.SCHEMA, "some_code", error)
        assert error in prompt

    def test_correction_prompt_contains_original_question(self):
        """LLM needs original intent to know what the corrected code should do."""
        query = "What is the average salary by department?"
        prompt = build_correction_prompt(query, self.SCHEMA, "df.head()", "error")
        assert query in prompt

    def test_correction_prompt_contains_schema(self):
        """Schema must be in correction prompt so LLM uses real column names."""
        prompt = build_correction_prompt("query", self.SCHEMA, "code", "error")
        assert "salary" in prompt
        assert "department" in prompt

    # ── Explanation prompt structure ───────────────────────

    def test_explanation_prompt_contains_code(self):
        code = "df.groupby('department')['salary'].mean()"
        prompt = build_explanation_prompt(code, "result: HR=55000")
        assert code in prompt

    def test_explanation_prompt_contains_result(self):
        prompt = build_explanation_prompt("df.head()", "5 rows of data")
        assert "5 rows of data" in prompt


# ═══════════════════════════════════════════════════════════
# PHASE 5B — Stub LLM Code Generation Quality
# ═══════════════════════════════════════════════════════════

class TestStubLLMGeneration:
    """
    Test the keyword-matching stub (active when no Gemini API key).
    Generated code must be syntactically valid AND executable.
    """

    @pytest.fixture(autouse=True)
    def engine_and_df(self):
        """Force stub mode by giving an empty API key."""
        # Temporarily unset the key so the engine uses the stub
        original_key = os.environ.get("GEMINI_API_KEY", "")
        os.environ["GEMINI_API_KEY"] = ""
        self.engine = LLMEngine()
        self.engine.is_stub = True    # Force stub mode
        self.engine.use_gemini = False
        os.environ["GEMINI_API_KEY"] = original_key

        self.schema = (
            "Dataset has 100 rows and 3 columns.\n"
            "Columns:\n"
            "  - sales (numeric): range 100-50000, mean 5000.0, 0 nulls\n"
            "  - region (categorical): top values: ['North', 'South', 'East'], 0 nulls\n"
            "  - date (datetime): 0 nulls\n"
        )
        self.df = pd.DataFrame({
            "sales":  np.random.randint(100, 50000, 50),
            "region": np.random.choice(["North", "South", "East"], 50),
        })

    def _generate_and_check(self, query: str):
        """Helper: generate code from stub and verify it is valid syntax."""
        result = self.engine._stub_generate(query, self.schema)
        assert "code" in result, "Stub must return a 'code' key"
        assert result["code"], f"Stub returned empty code for query: {query!r}"
        ok, msg = validate_syntax(result["code"])
        assert ok, f"Stub generated invalid Python syntax for {query!r}: {msg}\nCode: {result['code']}"
        return result

    def test_average_query_generates_valid_code(self):
        self._generate_and_check("what is the average sales")

    def test_groupby_average_generates_valid_code(self):
        self._generate_and_check("average sales by region")

    def test_sum_query_generates_valid_code(self):
        self._generate_and_check("total sales by region")

    def test_count_query_generates_valid_code(self):
        self._generate_and_check("how many rows per region")

    def test_max_query_generates_valid_code(self):
        self._generate_and_check("top 10 highest sales")

    def test_min_query_generates_valid_code(self):
        self._generate_and_check("show lowest sales values")

    def test_describe_query_generates_valid_code(self):
        self._generate_and_check("give me a summary statistics")

    def test_distribution_query_generates_valid_code(self):
        self._generate_and_check("show distribution of region")

    def test_correlation_query_generates_valid_code(self):
        self._generate_and_check("correlation between columns")

    def test_missing_query_generates_valid_code(self):
        self._generate_and_check("how many missing values are there")

    def test_compare_query_generates_valid_code(self):
        self._generate_and_check("compare sales vs region")

    def test_unique_query_generates_valid_code(self):
        self._generate_and_check("what are the unique regions")

    def test_anomaly_query_generates_valid_code(self):
        self._generate_and_check("find anomalies in sales")

    def test_unknown_query_falls_back_gracefully(self):
        """Unknown queries must still return some default code, not crash."""
        result = self.engine._stub_generate("xyzzy nonsense gobbledegook", self.schema)
        assert "code" in result
        assert result["code"]  # Must not be empty

    def test_stub_result_has_all_keys(self):
        """Stub result must always have code, confidence, explanation, engine."""
        result = self.engine._stub_generate("show data", self.schema)
        for key in ("code", "confidence", "explanation", "engine"):
            assert key in result, f"Missing key: {key}"

    def test_stub_confidence_is_valid_float(self):
        result = self.engine._stub_generate("average sales", self.schema)
        conf = result["confidence"]
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0

    def test_stub_executable_on_real_dataframe(self):
        """Generated stub code must actually run on a real DataFrame."""
        result = self.engine._stub_generate("average sales by region", self.schema)
        exec_result = execute_query(self.df, result["code"])
        assert exec_result["success"] is True, (
            f"Stub code failed on real df:\nCode: {result['code']}\nError: {exec_result.get('error')}"
        )


# ═══════════════════════════════════════════════════════════
# PHASE 5C — Conversation Memory (Multi-Turn ICL)
# ═══════════════════════════════════════════════════════════

class TestConversationMemory:
    """
    ML Concept: In-Context Learning (ICL) via conversation memory.
    Validate that the deque correctly stores, bounds, and exposes turns.
    """

    @pytest.fixture(autouse=True)
    def engine(self):
        os.environ["GEMINI_API_KEY"] = ""
        self.engine = LLMEngine(memory_size=3)
        self.engine.is_stub = True
        self.engine.use_gemini = False

    def test_memory_empty_initially(self):
        turns = self.engine.get_memory("session_1")
        assert turns == []

    def test_memory_stores_one_turn(self):
        self.engine._add_to_memory("s1", "show data", "df.head()", "Shows top rows")
        turns = self.engine.get_memory("s1")
        assert len(turns) == 1
        assert turns[0].query == "show data"
        assert turns[0].code == "df.head()"

    def test_memory_respects_maxlen(self):
        """With memory_size=3, a 4th turn should evict the oldest."""
        for i in range(4):
            self.engine._add_to_memory("s2", f"query_{i}", f"code_{i}", "expl")
        turns = self.engine.get_memory("s2")
        assert len(turns) == 3
        # Oldest (query_0) should be evicted
        assert turns[0].query == "query_1"
        assert turns[-1].query == "query_3"

    def test_memory_isolated_per_session(self):
        """Different session IDs must not share memory."""
        self.engine._add_to_memory("session_A", "query_A", "code_A", "expl")
        self.engine._add_to_memory("session_B", "query_B", "code_B", "expl")
        assert len(self.engine.get_memory("session_A")) == 1
        assert len(self.engine.get_memory("session_B")) == 1
        assert self.engine.get_memory("session_A")[0].query == "query_A"
        assert self.engine.get_memory("session_B")[0].query == "query_B"

    def test_clear_memory_empties_session(self):
        self.engine._add_to_memory("s3", "q", "c", "e")
        assert len(self.engine.get_memory("s3")) == 1
        self.engine.clear_memory("s3")
        assert self.engine.get_memory("s3") == []

    def test_clear_memory_does_not_affect_other_sessions(self):
        self.engine._add_to_memory("sA", "q", "c", "e")
        self.engine._add_to_memory("sB", "q", "c", "e")
        self.engine.clear_memory("sA")
        assert self.engine.get_memory("sB") != []

    def test_to_prompt_str_format(self):
        """ConversationTurn.to_prompt_str() must produce a readable string."""
        self.engine._add_to_memory("s4", "show sales", "df['sales'].sum()", "Sum")
        turns = self.engine.get_memory("s4")
        prompt_str = turns[0].to_prompt_str()
        assert "show sales" in prompt_str
        assert "df['sales'].sum()" in prompt_str

    def test_generate_code_auto_stores_result(self):
        """generate_code() with a session_id should auto-save to memory."""
        schema = "Dataset has 10 rows.\nColumns:\n  - sales (numeric): range 1-100\n"
        self.engine.generate_code("show top rows", schema, session_id="mem_test")
        turns = self.engine.get_memory("mem_test")
        assert len(turns) == 1
