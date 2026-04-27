"""
============================================================
LLM Engine — Generates Pandas code from natural language
============================================================
Uses Google Gemini API to convert natural-language questions
into valid Pandas expressions. Falls back to keyword-based
stub if the API key is missing or the call fails.

IMPORTANT:
  - The LLM ONLY generates code strings
  - It NEVER executes code
  - All output passes through the validation layer
============================================================
"""

import re
import logging
from typing import Dict, Any, List

from google import genai

from core.config import settings
from llm.prompt_templates import build_analysis_prompt, build_contextual_prompt

logger = logging.getLogger(__name__)


class LLMEngine:
    """
    LLM integration for natural-language to Pandas code generation.
    Uses Google Gemini API with automatic fallback to a keyword stub.
    """

    def __init__(self):
        self.is_stub = True
        self.client = None

        # Try to initialise the Gemini client
        api_key = settings.GEMINI_API_KEY
        if api_key and api_key != "your-api-key-here":
            try:
                self.client = genai.Client(api_key=api_key)
                self.model_name = settings.GEMINI_MODEL
                self.is_stub = False
                logger.info("Gemini LLM engine initialised (model: %s)", self.model_name)
            except Exception as e:
                logger.warning("Failed to initialise Gemini client, using stub: %s", e)
        else:
            logger.info("No Gemini API key configured — using stub LLM engine")

    # ────────────────────────────────────────────────────────
    # Public API
    # ────────────────────────────────────────────────────────

    def generate_code(self, natural_query: str, schema_summary: str, context_string: str = None) -> Dict[str, Any]:
        """
        Convert a natural language query into Pandas code.

        Parameters:
            natural_query: User's question (e.g., "Show average sales by region")
            schema_summary: Schema context string from schema_extractor
            context_string: Optional conversation history for follow-up questions

        Returns:
            {
                "code": str,        # Generated Pandas code
                "confidence": float, # 0.0–1.0
                "explanation": str   # Human-readable explanation
            }
        """
        if self.is_stub:
            return self._stub_generate(natural_query, schema_summary)

        try:
            return self._gemini_generate(natural_query, schema_summary, context_string)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning("Gemini quota exhausted, falling back to stub (resets daily)")
            else:
                logger.error("Gemini API call failed, falling back to stub: %s", e)
            return self._stub_generate(natural_query, schema_summary)

    def generate_narration(self, query: str, result_summary: str, highlights: List[str]) -> str:
        """
        Use Gemini to produce a 2–3 sentence natural-language narrative
        about the query result. Falls back to a formatted static summary.

        Parameters:
            query:          The original natural language question
            result_summary: Brief textual summary of the data result
            highlights:     List of key insight strings from insight_generator

        Returns:
            A human-readable narrative string.
        """
        if self.is_stub or not self.client:
            return self._build_smart_narration(query, highlights, result_summary)

        try:
            highlights_text = "\n".join(f"- {h}" for h in highlights[:5]) if highlights else "None"
            prompt = (
                f"You are a data analyst assistant. Write a clear 2-3 sentence narrative "
                f"summary of this data analysis result. Be specific about numbers and trends. "
                f"Use simple language a non-technical person can understand easily. "
                f"Do NOT use bullet points - write flowing prose only.\n\n"
                f"User question: {query}\n"
                f"Result summary: {result_summary}\n"
                f"Key highlights:\n{highlights_text}\n\n"
                f"Write the narrative now:"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.info("Gemini quota exhausted for narration, using fallback")
            else:
                logger.warning("Narration generation failed: %s", e)
            return self._build_smart_narration(query, highlights, result_summary)

    def generate_suggestions(self, query: str, schema_summary: str, result_summary: str) -> List[str]:
        """
        Use Gemini to suggest 3 smart follow-up questions the user might
        want to ask next, based on the current query and result.

        Returns:
            List of 3 follow-up question strings.
        """
        if self.is_stub or not self.client:
            return self._stub_suggestions(query, schema_summary)

        try:
            prompt = (
                f"You are a data analyst assistant. Based on the user's question and result, "
                f"suggest exactly 3 concise, insightful follow-up questions they should ask next. "
                f"Return ONLY the 3 questions, one per line, no numbering, no bullet points.\n\n"
                f"Schema: {schema_summary[:400]}\n"
                f"User question: {query}\n"
                f"Result: {result_summary}\n\n"
                f"3 follow-up questions:"
            )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            raw = response.text.strip()
            lines = [ln.strip().lstrip("*-1234567890.) ") for ln in raw.split("\n") if ln.strip()]
            suggestions = [s for s in lines if len(s) > 10][:3]
            return suggestions if suggestions else self._stub_suggestions(query, schema_summary)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.info("Gemini quota exhausted for suggestions, using fallback")
            else:
                logger.warning("Suggestions generation failed: %s", e)
            return self._stub_suggestions(query, schema_summary)

    def _stub_suggestions(self, query: str, schema_summary: str) -> List[str]:
        """Keyword-based fallback suggestions when Gemini is unavailable."""
        cols = self._extract_columns_from_schema(schema_summary)
        num = cols["numeric"][0] if cols["numeric"] else "value"
        cat = cols["categorical"][0] if cols["categorical"] else "category"
        return [
            f"What is the average {num} grouped by {cat}?",
            f"Show the top 10 rows sorted by {num} descending",
            f"Are there any anomalies or outliers in the {num} column?",
        ]

    # ────────────────────────────────────────────────────────
    # Gemini (real LLM) path
    # ────────────────────────────────────────────────────────

    def _gemini_generate(self, query: str, schema: str, context_string: str = None) -> Dict[str, Any]:
        """Call Google Gemini API and parse the response."""
        if context_string:
            prompt = build_contextual_prompt(query, schema, context_string)
        else:
            prompt = build_analysis_prompt(query, schema)

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )

        raw_text = response.text.strip()
        code = self._extract_code(raw_text)

        # Build a short explanation from any text outside the code block
        explanation = self._extract_explanation(raw_text, code)

        return {
            "code": code,
            "confidence": 0.90,
            "explanation": explanation or f"Generated code for: {query}",
        }

    # ────────────────────────────────────────────────────────
    # Smart narration builder (used when Gemini is unavailable)
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _build_smart_narration(query: str, highlights: List[str], result_summary: str) -> str:
        """
        Compose a 2-3 sentence analyst-style narrative from highlights.
        Aims for the tone of a data analyst explaining results to a manager.
        """
        if not highlights:
            return (
                f"The analysis for \"{query}\" completed successfully. "
                f"{result_summary}"
            )

        # Remove emoji for clean prose
        _emojis = ["📈 ", "📉 ", "📊 ", "⬆️ ", "⬇️ ", "➡️ ", "🏆 ", "🔗 ",
                   "📌 ", "⚡ ", "**"]
        def clean(s: str) -> str:
            for em in _emojis:
                s = s.replace(em, "")
            return s.strip()

        # Sentence 1: lead finding (highest/lowest or main metric)
        lead = next(
            (h for h in highlights if any(k in h for k in ["📈", "🔗", "📊"])),
            highlights[0]
        )
        # Sentence 2: context (average or trend)
        ctx = next(
            (h for h in highlights if any(k in h for k in ["📊", "⬆️", "⬇️", "➡️", "📌"])),
            None
        )
        # Sentence 3: ranking or variation
        extra = next(
            (h for h in highlights if any(k in h for k in ["🏆", "⚡"])),
            None
        )

        parts = [clean(lead) + "."]
        if ctx and ctx != lead:
            parts.append(clean(ctx) + ".")
        if extra:
            parts.append(clean(extra) + ".")

        return " ".join(parts)

    # ────────────────────────────────────────────────────────
    # Response parsing helpers
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _extract_code(text: str) -> str:
        """
        Extract Pandas code from the LLM response.
        Handles:
          - ```python ... ``` fenced blocks
          - ``` ... ``` generic fenced blocks
          - Plain code (no fences)
        """
        # Try to find a fenced code block
        pattern = r"```(?:python)?\s*\n?(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            # Remove any leading 'result = ' wrapper the LLM might add
            code = re.sub(r"^result\s*=\s*", "", code)
            return code

        # No code fence — take the whole text, clean it up
        lines = text.strip().split("\n")
        code_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and comment-only lines
            if not stripped or stripped.startswith("#"):
                continue
            # Skip lines that look like plain-English explanations
            if stripped[0].isupper() and not stripped.startswith("df"):
                continue
            code_lines.append(stripped)

        return "\n".join(code_lines) if code_lines else text.strip()

    @staticmethod
    def _extract_explanation(raw_text: str, code: str) -> str:
        """Pull any explanatory text from outside the code block."""
        # Remove the code block from the raw text
        cleaned = re.sub(r"```(?:python)?\s*\n?.*?```", "", raw_text, flags=re.DOTALL)
        cleaned = cleaned.strip()
        # Take first 200 chars as explanation
        if cleaned:
            return cleaned[:200]
        return ""

    # ────────────────────────────────────────────────────────
    # Stub fallback (keyword matching)
    # ────────────────────────────────────────────────────────

    def _stub_generate(self, query: str, schema: str) -> Dict[str, Any]:
        """
        Fallback: uses keyword matching + schema-aware column extraction
        to produce dynamic Pandas code based on the ACTUAL dataset columns.
        """
        query_lower = query.lower().strip()

        # ── Normalize unicode chemistry notation to ASCII ────────
        # e.g. NO₂ → no2, PM₂.₅ → pm2_5, CO₂ → co2
        _uni_map = {
            '\u2080': '0', '\u2081': '1', '\u2082': '2', '\u2083': '3',
            '\u2084': '4', '\u2085': '5', '\u2086': '6', '\u2087': '7',
            '\u2088': '8', '\u2089': '9', '.': '_',
        }
        query_normalized = query_lower
        for uni, asc in _uni_map.items():
            query_normalized = query_normalized.replace(uni, asc)
        # Use normalized version for column matching, original for keyword matching
        query_for_cols = query_normalized

        # Extract actual column names from schema
        columns = self._extract_columns_from_schema(schema)
        numeric_cols = columns.get("numeric", [])
        categorical_cols = columns.get("categorical", [])
        datetime_cols = columns.get("datetime", [])

        # ── Try to find column names mentioned in the query ─────
        mentioned_numeric    = self._find_mentioned_column(query_for_cols, numeric_cols)
        mentioned_categorical = self._find_mentioned_column(query_for_cols, categorical_cols)

        # Defaults for when no column is mentioned
        default_num = numeric_cols[0] if numeric_cols else None
        default_cat = categorical_cols[0] if categorical_cols else None

        # Use mentioned or defaults
        num = mentioned_numeric or default_num
        cat = mentioned_categorical or default_cat

        # ── Groupby trigger keywords (expanded) ─────────────────
        _groupby_kws = [
            "by", "per", "each", "group",
            "wise", "-wise", "across", "compare", "versus", "vs",
            "city", "state", "region", "country", "category",
        ]
        wants_groupby = any(kw in query_lower for kw in _groupby_kws)

        # ── Keyword-based code generation ──────────────────
        if any(kw in query_lower for kw in ["compare", "versus", "vs", "rank", "ranking", "top", "bottom"]):
            # Compare / rank always implies grouped aggregation
            if cat and num:
                agg = "mean"
                if any(kw in query_lower for kw in ["sum", "total"]):
                    agg = "sum"
                elif any(kw in query_lower for kw in ["max", "maximum", "highest"]):
                    agg = "max"
                elif any(kw in query_lower for kw in ["min", "minimum", "lowest"]):
                    agg = "min"
                code = f"df.groupby('{cat}')['{num}'].{agg}().reset_index().sort_values('{num}', ascending=False)"
                explanation = f"Compares {agg} '{num}' across each '{cat}', sorted descending"
            elif num:
                code = f"df['{num}'].describe()"
                explanation = f"Summary statistics for '{num}'"
            else:
                code = "df.describe()"
                explanation = "Descriptive statistics (no specific column found)"

        elif any(kw in query_lower for kw in ["average", "mean", "avg"]):
            if wants_groupby and cat and num:
                code = f"df.groupby('{cat}')['{num}'].mean().reset_index().sort_values('{num}', ascending=False)"
                explanation = f"Calculates the average of '{num}' grouped by '{cat}'"
            elif num:
                code = f"df['{num}'].mean()"
                explanation = f"Calculates the overall average of '{num}'"
            else:
                code = "df.describe()"
                explanation = "Shows descriptive statistics (no numeric column identified)"

        elif any(kw in query_lower for kw in ["sum", "total"]):
            if wants_groupby and cat and num:
                code = f"df.groupby('{cat}')['{num}'].sum().reset_index().sort_values('{num}', ascending=False)"
                explanation = f"Calculates total '{num}' by '{cat}'"
            elif num:
                code = f"df['{num}'].sum()"
                explanation = f"Calculates the total sum of '{num}'"
            else:
                code = "df.describe()"
                explanation = "Shows descriptive statistics (no numeric column identified)"

        elif any(kw in query_lower for kw in ["count", "how many", "frequency"]):
            if wants_groupby and cat:
                code = f"df['{cat}'].value_counts().reset_index().rename(columns={{'count': 'count'}})"
                explanation = f"Counts occurrences of each '{cat}'"
            elif cat:
                code = f"df['{cat}'].value_counts().reset_index()"
                explanation = f"Counts occurrences of each '{cat}'"
            else:
                code = "df.shape[0]"
                explanation = "Counts total number of rows"

        elif any(kw in query_lower for kw in ["describe", "summary", "statistics", "stats", "overview"]):
            code = "df.describe()"
            explanation = "Shows descriptive statistics for all numeric columns"

        elif any(kw in query_lower for kw in ["correlation", "correlate", "relationship", "relate", "corr between"]):
            # Find all mentioned numeric columns (could be 2 for a specific pair)
            mentioned_cols = []
            for col in sorted(numeric_cols, key=len, reverse=True):
                col_lower = col.lower().replace("_", " ")
                # Also check normalized query for subscripted names
                if col.lower() in query_for_cols or col_lower in query_for_cols:
                    mentioned_cols.append(col)

            if len(mentioned_cols) >= 2:
                # Specific pair: show just those two columns' correlation
                col_list = str(mentioned_cols[:2])
                code = (
                    f"df[{col_list}].corr()"
                )
                explanation = f"Correlation between '{mentioned_cols[0]}' and '{mentioned_cols[1]}'"
            elif len(mentioned_cols) == 1:
                # One column mentioned: show its correlation with all others
                col = mentioned_cols[0]
                code = (
                    f"df[{str(numeric_cols)}].corr()[['{col}']].drop('{col}')"
                    f".reset_index().rename(columns={{'index': 'column', '{col}': 'correlation'}})"
                    f".sort_values('correlation', ascending=False)"
                )
                explanation = f"Correlation of '{col}' with all other numeric columns"
            else:
                # No columns mentioned — full matrix
                code = "df.corr(numeric_only=True)"
                explanation = "Shows full correlation matrix of all numeric columns"

        elif any(kw in query_lower for kw in ["trend", "over time", "year-wise", "yearly", "year wise",
                                                "monthly", "by year", "by month", "time series",
                                                "growth", "change over"]):
            # Time-series grouping — use date column if available
            if datetime_cols and num:
                date_col = datetime_cols[0]
                # Check if mentioned numeric exists
                metric = mentioned_numeric or num
                if any(kw in query_lower for kw in ["month", "monthly"]):
                    code = (
                        f"df.assign(_period=pd.to_datetime(df['{date_col}']).dt.to_period('M').astype(str))"
                        f".groupby('_period')['{metric}'].mean().reset_index()"
                        f".rename(columns={{'_period': 'month', '{metric}': '{metric}'}})"
                    )
                    explanation = f"Monthly average of '{metric}' over time"
                else:
                    code = (
                        f"df.assign(year=pd.to_datetime(df['{date_col}']).dt.year)"
                        f".groupby('year')['{metric}'].mean().reset_index()"
                    )
                    explanation = f"Year-wise average of '{metric}'"
            elif cat and num:
                metric = mentioned_numeric or num
                code = f"df.groupby('{cat}')['{metric}'].mean().reset_index()"
                explanation = f"Average '{metric}' grouped by '{cat}' (no date column found)"
            else:
                code = "df.head(10)"
                explanation = "No date or category column found for trend analysis"

        elif any(kw in query_lower for kw in [
            "cluster", "similarity", "similar", "segment", "profile",
            "group together", "pattern", "classify", "class", "heatmap",
            "pollutant profile", "compare all", "all pollutants",
        ]):
            # Clustering / multi-metric profile — show all pollutants per city
            if cat:
                code = (
                    f"df.groupby('{cat}').mean(numeric_only=True).reset_index()"
                    f".sort_values('{numeric_cols[0]}', ascending=False)"
                    if numeric_cols else
                    f"df.groupby('{cat}').mean(numeric_only=True).reset_index()"
                )
                explanation = (
                    f"Average of all pollutants per {cat} — shows the full "
                    f"pollution profile so you can spot cities with similar patterns"
                )
            else:
                code = "df.describe()"
                explanation = "Overall statistical profile of all columns"

        elif any(kw in query_lower for kw in [
            "outlier", "anomaly", "anomalies", "abnormal", "unusual",
            "extreme", "spike", "detect outlier", "detect anomaly",
            "iqr", "out of range",
        ]):
            metric = mentioned_numeric  # specific column if named, else None
            if metric and cat:
                # Per-city outlier count for a specific metric
                q = f"df['{metric}'].quantile"
                code = (
                    f"df.assign(_out=((df['{metric}']<{q}(0.25)-1.5*({q}(0.75)-{q}(0.25)))"
                    f"|(df['{metric}']>{q}(0.75)+1.5*({q}(0.75)-{q}(0.25))))).groupby('{cat}')['_out'].sum().reset_index()"
                    f".rename(columns={{'_out':'outlier_count'}}).sort_values('outlier_count',ascending=False)"
                )
                explanation = f"Cities ranked by number of outlier '{metric}' readings (IQR method)"
            elif metric:
                # Single metric outlier rows
                q = f"df['{metric}'].quantile"
                sel = f"[['{cat}','{metric}']]" if cat else f"[['{metric}']]"
                code = (
                    f"df[((df['{metric}']<{q}(0.25)-1.5*({q}(0.75)-{q}(0.25)))"
                    f"|(df['{metric}']>{q}(0.75)+1.5*({q}(0.75)-{q}(0.25))))]{sel}"
                    f".sort_values('{metric}',ascending=False)"
                )
                explanation = f"Rows where '{metric}' is a statistical outlier (beyond 1.5\u00d7IQR)"
            elif cat:
                # Multi-column IQR — flag each pollutant, sum per row, group by city
                num_cols = [c for c in numeric_cols if c != cat][:5] or numeric_cols[:5]
                flags = "+".join(
                    f"((df['{c}']<df['{c}'].quantile(0.25)-1.5*(df['{c}'].quantile(0.75)-df['{c}'].quantile(0.25)))|(df['{c}']>df['{c}'].quantile(0.75)+1.5*(df['{c}'].quantile(0.75)-df['{c}'].quantile(0.25)))).astype('int64')"
                    for c in num_cols
                )
                code = (
                    f"df.assign(_s=({flags})).groupby('{cat}')['_s'].sum().reset_index()"
                    f".rename(columns={{'_s':'outlier_readings'}}).sort_values('outlier_readings',ascending=False)"
                )
                explanation = (
                    f"Total outlier readings per {cat} across all pollutants "
                    f"(IQR method \u2014 higher bar = city with most extreme data points)"
                )
            else:
                # Per-pollutant outlier count
                nc = numeric_cols[:5] if numeric_cols else []
                pairs = ",".join(
                    f"('{c}',int(((df['{c}']<df['{c}'].quantile(0.25)-1.5*(df['{c}'].quantile(0.75)-df['{c}'].quantile(0.25)))|(df['{c}']>df['{c}'].quantile(0.75)+1.5*(df['{c}'].quantile(0.75)-df['{c}'].quantile(0.25)))).sum()))"
                    for c in nc
                )
                code = (
                    f"pd.DataFrame([{{'pollutant':k,'outlier_count':v}} for k,v in [{pairs}]])"
                    f".sort_values('outlier_count',ascending=False)"
                )
                explanation = "Count of outlier readings per pollutant (IQR method)"


        elif any(kw in query_lower for kw in [
            "identify", "high-risk", "high risk", "risk", "above", "exceed",
            "dangerous", "hazardous", "worst", "hotspot", "flag", "filter",
            "threshold", "polluted", "unhealthy", "critical",
        ]):
            # These want ranked/filtered grouped results, not raw stats
            metric = mentioned_numeric or num
            if cat and metric:
                code = (
                    f"df.groupby('{cat}')['{metric}'].mean().reset_index()"
                    f".sort_values('{metric}', ascending=False)"
                )
                explanation = f"Ranking all {cat}s by average '{metric}' (highest = most at-risk)"
            elif metric:
                code = f"df.nlargest(10, '{metric}')"
                explanation = f"Top 10 rows with highest '{metric}' values"
            else:
                code = "df.head(10)"
                explanation = "No metric identified for risk analysis"

        else:
            # Default fallback — smarter than describe()
            if mentioned_numeric and mentioned_categorical:
                code = f"df.groupby('{mentioned_categorical}')['{mentioned_numeric}'].mean().reset_index().sort_values('{mentioned_numeric}', ascending=False)"
                explanation = f"Shows average '{mentioned_numeric}' by '{mentioned_categorical}'"
            elif mentioned_categorical:
                code = f"df['{mentioned_categorical}'].value_counts().reset_index()"
                explanation = f"Shows distribution of '{mentioned_categorical}'"
            elif mentioned_numeric and cat:
                # A numeric was mentioned + dataset has a category — group instead of describe
                code = f"df.groupby('{cat}')['{mentioned_numeric}'].mean().reset_index().sort_values('{mentioned_numeric}', ascending=False)"
                explanation = f"Average '{mentioned_numeric}' grouped by '{cat}', ranked highest first"
            elif mentioned_numeric:
                code = f"df['{mentioned_numeric}'].describe()"
                explanation = f"Shows statistics for '{mentioned_numeric}'"
            else:
                code = "df.head(10)"
                explanation = "Showing a preview of the dataset (no specific query pattern matched)"

        return {
            "code": code,
            "confidence": 0.85,
            "explanation": explanation,
        }

    def _find_mentioned_column(self, query: str, column_list: List[str]) -> str:
        """
        Check if any of the column names appear in the query.
        Returns the first match, or None.
        """
        if not column_list:
            return None

        sorted_cols = sorted(column_list, key=len, reverse=True)
        for col in sorted_cols:
            col_lower = col.lower()
            col_space = col_lower.replace("_", " ")
            if col_lower in query or col_space in query:
                return col
        return None

    def _extract_columns_from_schema(self, schema: str) -> Dict[str, list]:
        """
        Parse the schema summary to extract column names by type.
        """
        columns = {"numeric": [], "categorical": [], "datetime": [], "boolean": []}

        for line in schema.split("\n"):
            line = line.strip()
            if not line.startswith("- "):
                continue

            content = line[2:]
            paren_idx = content.find("(")
            if paren_idx == -1:
                continue

            col_name = content[:paren_idx].strip()
            rest = content[paren_idx + 1:]
            close_paren = rest.find(")")
            if close_paren == -1:
                continue

            col_type = rest[:close_paren].strip().lower()

            if col_type in columns:
                columns[col_type].append(col_name)

        return columns


# ── Module-level singleton ────────────────────────────────
llm_engine = LLMEngine()
