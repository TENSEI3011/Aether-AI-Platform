"""
============================================================
test_phase6_viz_and_e2e.py
AI DLC Phase 6: Output Quality & End-to-End Pipeline
============================================================
Tests the final output layer and the complete AI pipeline:

  6A. Visualization Selector
      - Correct chart type chosen from data shape
      - Manual override respected
      - Axis assignment logic
      - Edge cases (empty data, single column)

  6B. Insight Generator
      - Statistical fallback produces valid structure
      - Highlights are generated for numeric data
      - Trend detection (up/down/stable)
      - Empty data handled gracefully

  6C. End-to-End Pipeline Integration
      - Complete journey: schema → LLM → validate → execute → viz → insight
      - Multiple query types through the full stack
      - DataFrame mutation safety verified after full pipeline
      - Error recovery: bad query → validation fail → graceful response

ML Concepts Covered:
  - AI Output Quality Evaluation
  - Pipeline Integration Testing
  - Graceful Degradation (fallbacks at every layer)
============================================================
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.viz_selector import select_visualization
from services.insight_generator import _statistical_insights
from services.schema_extractor import extract_schema, generate_schema_summary
from services.query_executor import execute_query
from services.query_validator import validate_query
from llm.llm_engine import LLMEngine


# ═══════════════════════════════════════════════════════════
# PHASE 6A — Visualization Selector
# ═══════════════════════════════════════════════════════════

class TestVizSelector:
    """
    Tests that the system automatically selects the best chart type.
    This is critical UX: wrong chart types confuse users.
    """

    # ── Datetime + Numeric → Line chart ───────────────────

    def test_datetime_numeric_gives_line_chart(self):
        data = [{"date": "2023-01-01", "sales": 100},
                {"date": "2023-01-02", "sales": 200},
                {"date": "2023-01-03", "sales": 150}]
        result = select_visualization(data, ["date", "sales"], row_count=3)
        assert result["chart_type"] == "line"

    def test_line_chart_has_date_on_x_axis(self):
        data = [{"date": "2023-01-01", "sales": 100},
                {"date": "2023-01-02", "sales": 200}]
        result = select_visualization(data, ["date", "sales"], row_count=2)
        assert result["x_axis"] == "date"
        assert result["y_axis"] == "sales"

    # ── Categorical + Numeric → Bar or Pie chart ──────────

    def test_many_categories_gives_bar_chart(self):
        """More than 6 unique categories → bar chart."""
        cats = [f"Cat{i}" for i in range(10)]
        data = [{"category": c, "value": i * 10} for i, c in enumerate(cats)]
        result = select_visualization(data, ["category", "value"], row_count=10)
        assert result["chart_type"] == "bar"

    def test_few_categories_gives_pie_chart(self):
        """≤ 6 unique categories + single numeric → pie chart."""
        data = [{"region": r, "sales": s} for r, s in
                [("North", 100), ("South", 200), ("East", 150),
                 ("West", 120), ("Central", 80)]]
        result = select_visualization(data, ["region", "sales"], row_count=5)
        assert result["chart_type"] == "pie"

    def test_bar_chart_categorical_on_x_axis(self):
        data = [{"dept": d, "avg_salary": s} for d, s in
                [("HR", 55000), ("Eng", 95000), ("Sales", 72000),
                 ("Finance", 85000), ("Ops", 62000),
                 ("Legal", 90000), ("Marketing", 70000)]]
        result = select_visualization(data, ["dept", "avg_salary"], row_count=7)
        assert result["x_axis"] == "dept"
        assert result["y_axis"] == "avg_salary"

    # ── Manual override ───────────────────────────────────

    def test_manual_bar_override(self):
        data = [{"date": "2023-01-01", "sales": 100}]
        result = select_visualization(data, ["date", "sales"], row_count=1, graph_type="bar")
        assert result["chart_type"] == "bar"

    def test_manual_table_override(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = select_visualization(data, ["a", "b", "c"], row_count=1, graph_type="table")
        assert result["chart_type"] == "table"

    def test_manual_pie_override(self):
        data = [{"x": 10, "y": 20}]
        result = select_visualization(data, ["x", "y"], row_count=1, graph_type="pie")
        assert result["chart_type"] == "pie"

    def test_invalid_graph_type_ignored(self):
        """Unknown override values are ignored — auto-select is used instead."""
        data = [{"a": 1, "b": "cat"}]
        result = select_visualization(data, ["a", "b"], row_count=1, graph_type="sunburst")
        # Should not crash — should fall through to auto-select
        assert result["chart_type"] in ("bar", "line", "pie", "table")

    # ── Edge cases ─────────────────────────────────────────

    def test_empty_data_gives_table(self):
        result = select_visualization([], [], row_count=0)
        assert result["chart_type"] == "table"

    def test_two_numeric_columns_gives_bar(self):
        """Two numeric columns (no categories) → bar chart."""
        data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 30}]
        result = select_visualization(data, ["x", "y"], row_count=3)
        assert result["chart_type"] == "bar"

    def test_result_has_required_keys(self):
        data = [{"region": "North", "sales": 100}]
        result = select_visualization(data, ["region", "sales"], row_count=1)
        for key in ("chart_type", "x_axis", "y_axis", "reason"):
            assert key in result, f"Missing key: {key}"

    def test_reason_is_non_empty_string(self):
        data = [{"a": 1, "b": "cat"}]
        result = select_visualization(data, ["a", "b"], row_count=1)
        assert isinstance(result["reason"], str)
        assert len(result["reason"]) > 0

    def test_auto_default_respected(self):
        """Passing graph_type='auto' must behave the same as no override."""
        data = [{"cat": c, "val": v} for c, v in
                zip(["A", "B", "C", "D", "E", "F", "G"], range(7))]
        r1 = select_visualization(data, ["cat", "val"], row_count=7)
        r2 = select_visualization(data, ["cat", "val"], row_count=7, graph_type="auto")
        assert r1["chart_type"] == r2["chart_type"]


# ═══════════════════════════════════════════════════════════
# PHASE 6B — Insight Generator (Statistical Fallback)
# ═══════════════════════════════════════════════════════════

class TestInsightGenerator:
    """
    Test the statistical insight engine that runs when Gemini is unavailable.
    Every analysis must produce at least a summary and non-empty highlights.
    """

    def test_returns_required_keys(self):
        data = [{"sales": 100}, {"sales": 200}, {"sales": 300}]
        result = _statistical_insights(data, ["sales"])
        for key in ("summary", "highlights", "row_count"):
            assert key in result, f"Missing key: {key}"

    def test_row_count_matches_data(self):
        data = [{"x": i} for i in range(20)]
        result = _statistical_insights(data, ["x"])
        assert result["row_count"] == 20

    def test_numeric_column_produces_highlights(self):
        """Numeric columns must produce at least one max/min/mean highlight."""
        data = [{"sales": v} for v in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]]
        result = _statistical_insights(data, ["sales"])
        assert len(result["highlights"]) > 0
        # At least one highlight should mention the column name
        combined = " ".join(result["highlights"])
        assert "sales" in combined

    def test_upward_trend_detected(self):
        """Consistently rising data should produce an 'upward trend' highlight."""
        data = [{"value": i * 10} for i in range(30)]
        result = _statistical_insights(data, ["value"])
        combined = " ".join(result["highlights"]).lower()
        assert "upward" in combined or "up" in combined

    def test_downward_trend_detected(self):
        """Consistently falling data should produce a 'downward trend' highlight."""
        data = [{"value": (30 - i) * 10} for i in range(30)]
        result = _statistical_insights(data, ["value"])
        combined = " ".join(result["highlights"]).lower()
        assert "downward" in combined or "down" in combined

    def test_categorical_column_shows_top_value(self):
        """Top category value should appear in highlights."""
        data = ([{"region": "North"}] * 15 +
                [{"region": "South"}] * 8 +
                [{"region": "East"}] * 5)
        result = _statistical_insights(data, ["region"])
        combined = " ".join(result["highlights"])
        assert "North" in combined

    def test_summary_mentions_row_count(self):
        data = [{"x": i} for i in range(42)]
        result = _statistical_insights(data, ["x"])
        assert "42" in result["summary"]

    def test_empty_data_returns_gracefully(self):
        """Empty data must not crash — return zero row_count."""
        from services.insight_generator import generate_insights
        result = generate_insights([], [], "show data")
        assert result["row_count"] == 0
        assert "summary" in result

    def test_multiple_numeric_columns(self):
        """Multiple numeric columns should all appear in highlights."""
        data = [{"a": i, "b": i * 2, "c": i * 3} for i in range(20)]
        result = _statistical_insights(data, ["a", "b", "c"])
        combined = " ".join(result["highlights"])
        assert "a" in combined
        assert "b" in combined


# ═══════════════════════════════════════════════════════════
# PHASE 6C — End-to-End Pipeline Integration
# ═══════════════════════════════════════════════════════════

class TestEndToEndPipeline:
    """
    Full pipeline: schema extract → LLM stub → validate → execute → viz → insights.
    These are the highest-value tests — they exercise every layer at once.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        np.random.seed(99)
        n = 80
        self.df = pd.DataFrame({
            "employee_id": range(1, n + 1),
            "age":         np.random.randint(22, 60, n),
            "salary":      np.random.randint(40_000, 150_000, n).astype(float),
            "department":  np.random.choice(["Eng", "HR", "Sales", "Finance"], n),
            "is_remote":   np.random.choice([0, 1], n),
        })
        self.schema = extract_schema(self.df)
        self.schema_summary = generate_schema_summary(self.schema)
        self.col_names = [c["name"] for c in self.schema["columns"]]

        # Force stub mode
        os.environ["GEMINI_API_KEY"] = ""
        self.engine = LLMEngine()
        self.engine.is_stub = True
        self.engine.use_gemini = False

    def _run_pipeline(self, query: str):
        """Run the full pipeline and return all outputs."""
        # Step 1: Generate code
        llm = self.engine._stub_generate(query, self.schema_summary)
        code = llm["code"]

        # Step 2: Validate
        validation = validate_query(code, self.col_names)

        # Step 3: Execute
        if validation["is_valid"]:
            exec_result = execute_query(self.df, code)
        else:
            exec_result = {"success": False, "data": [], "columns": [], "row_count": 0}

        # Step 4: Visualize
        viz = select_visualization(
            exec_result["data"],
            exec_result["columns"],
            exec_result["row_count"],
        )

        # Step 5: Insights
        from services.insight_generator import _statistical_insights
        insights = _statistical_insights(exec_result["data"], exec_result["columns"])

        return {
            "code": code, "validation": validation, "exec": exec_result,
            "viz": viz, "insights": insights,
        }

    def test_average_query_full_pipeline(self):
        result = self._run_pipeline("average salary by department")
        assert result["validation"]["is_valid"] is True, f"Validation failed: {result['validation']['errors']}"
        assert result["exec"]["success"] is True, f"Exec failed: {result['exec'].get('error')}"
        assert result["exec"]["row_count"] > 0
        assert result["viz"]["chart_type"] in ("bar", "pie", "table")

    def test_count_query_full_pipeline(self):
        result = self._run_pipeline("how many employees in each department")
        assert result["validation"]["is_valid"] is True
        assert result["exec"]["success"] is True

    def test_max_query_full_pipeline(self):
        result = self._run_pipeline("top 10 highest salary employees")
        assert result["exec"]["success"] is True
        assert result["exec"]["row_count"] <= 10

    def test_describe_query_full_pipeline(self):
        result = self._run_pipeline("describe the dataset statistics")
        assert result["validation"]["is_valid"] is True
        assert result["exec"]["success"] is True

    def test_correlation_query_full_pipeline(self):
        result = self._run_pipeline("what is the correlation between columns")
        assert result["exec"]["success"] is True

    def test_missing_values_query_full_pipeline(self):
        result = self._run_pipeline("show missing values per column")
        assert result["exec"]["success"] is True

    def test_distribution_query_full_pipeline(self):
        result = self._run_pipeline("show distribution of department")
        assert result["exec"]["success"] is True

    def test_pipeline_never_mutates_original_df(self):
        """The full pipeline must never modify the original DataFrame."""
        original_cols = list(self.df.columns)
        original_len = len(self.df)
        original_first_val = self.df["salary"].iloc[0]

        self._run_pipeline("average salary by department")
        self._run_pipeline("top 10 highest salary employees")
        self._run_pipeline("show missing values per column")

        assert list(self.df.columns) == original_cols
        assert len(self.df) == original_len
        assert self.df["salary"].iloc[0] == original_first_val

    def test_blocked_code_caught_by_validator(self):
        """Even if stub somehow generates blocked code, validator must catch it."""
        bad_code = "import os; os.system('cmd')"
        validation = validate_query(bad_code, self.col_names)
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0

    def test_pipeline_insight_structure(self):
        result = self._run_pipeline("average salary by department")
        insights = result["insights"]
        assert "summary" in insights
        assert "highlights" in insights
        assert "row_count" in insights

    def test_pipeline_viz_has_all_keys(self):
        result = self._run_pipeline("count by department")
        viz = result["viz"]
        for key in ("chart_type", "x_axis", "y_axis", "reason"):
            assert key in viz

    def test_multiple_sequential_queries_with_memory(self):
        """Run 3 queries with conversation memory — last should include context."""
        session = "e2e_session"
        queries = [
            "average salary by department",
            "how many employees per department",
            "show top 5 highest salary",
        ]
        for q in queries:
            self.engine.generate_code(q, self.schema_summary, session_id=session)

        turns = self.engine.get_memory(session)
        assert len(turns) == 3
        assert turns[0].query == queries[0]
        assert turns[2].query == queries[2]
