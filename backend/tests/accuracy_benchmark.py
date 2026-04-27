"""
============================================================
Accuracy Benchmark — Measures pipeline accuracy per component
============================================================
Tests:
  1. Code Generation   — Does the LLM produce valid, executable code?
  2. Query Validation   — Does the validator catch bad code?
  3. Viz Selector       — Does it pick the right chart type?
  4. Insight Generator  — Does it produce meaningful insights?
  5. Anomaly Detector   — Does it flag real outliers correctly?
  6. Forecaster         — How accurate are predictions?
  7. End-to-End         — Full pipeline NL query → correct result

Run:
    cd backend
    python -m tests.accuracy_benchmark
============================================================
"""

import sys
import os
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

# ── Add project root to path ─────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.llm_engine import LLMEngine
from services.query_validator import validate_query
from services.query_executor import execute_query
from services.viz_selector import select_visualization
from services.insight_generator import generate_insights
from services.anomaly_detector import detect_anomalies
from services.forecaster import forecast
from services.schema_extractor import extract_schema, generate_schema_summary


# ═══════════════════════════════════════════════════════════
#  SAMPLE TEST DATASET
# ═══════════════════════════════════════════════════════════

def create_test_dataframe() -> pd.DataFrame:
    """Create a realistic test dataset with known properties."""
    np.random.seed(42)
    cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
              "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow"]
    n = 100

    df = pd.DataFrame({
        "City": np.random.choice(cities, n),
        "Year": np.random.choice(range(2018, 2024), n),
        "Population": np.random.randint(500000, 20000000, n),
        "AQI": np.random.normal(120, 40, n).round(1),
        "Temperature": np.random.normal(30, 5, n).round(1),
        "Rainfall_mm": np.random.exponential(800, n).round(1),
        "GDP_Billion": np.random.uniform(10, 500, n).round(2),
    })

    # Inject known issues for cleaning/anomaly tests
    df.loc[0, "AQI"] = None
    df.loc[1, "Temperature"] = None
    df.loc[2, "AQI"] = None
    df.loc[5, "AQI"] = 999.9        # Known outlier
    df.loc[10, "Temperature"] = -50  # Known outlier
    df.loc[15:16, "City"] = df.loc[15:16, "City"]  # Potential duplicates

    return df


# ═══════════════════════════════════════════════════════════
#  TEST 1: CODE GENERATION ACCURACY
# ═══════════════════════════════════════════════════════════

def test_code_generation(llm: LLMEngine, schema_summary: str, df: pd.DataFrame) -> Dict:
    """
    Tests whether the LLM generates valid, executable Pandas code
    for a set of known queries.
    """
    test_queries = [
        ("Show the average AQI by city", "groupby", ["City", "AQI"]),
        ("What is the total population?", "scalar", ["Population"]),
        ("Show top 5 cities by GDP", "top_n", ["City", "GDP_Billion"]),
        ("Count rows per city", "value_counts", ["City"]),
        ("Show summary statistics", "describe", []),
        ("What is the average temperature by year?", "groupby", ["Year", "Temperature"]),
        ("Show correlation between AQI and Temperature", "corr", ["AQI", "Temperature"]),
        ("Show the maximum rainfall", "scalar", ["Rainfall_mm"]),
        ("Compare GDP across cities", "groupby", ["City", "GDP_Billion"]),
        ("Show first 10 rows", "head", []),
        ("What is the trend of AQI over years?", "trend", ["Year", "AQI"]),
        ("Show AQI distribution", "distribution", ["AQI"]),
        ("Which city has the highest AQI?", "top_n", ["City", "AQI"]),
        ("Show total rainfall by city", "groupby", ["City", "Rainfall_mm"]),
        ("How many unique cities are there?", "scalar", ["City"]),
    ]

    results = []
    column_names = list(df.columns)

    for query, expected_type, expected_cols in test_queries:
        start = time.time()
        try:
            # Generate code
            gen = llm.generate_code(query, schema_summary)
            code = gen["code"]
            gen_time = round(time.time() - start, 3)

            # Validate
            val = validate_query(code, column_names)

            # Execute
            if val["is_valid"]:
                exec_result = execute_query(df, code)
                executable = exec_result["success"]
                has_data = len(exec_result.get("data", [])) > 0

                # Check if expected columns appear in result
                result_cols = exec_result.get("columns", [])
                col_match = all(
                    any(ec.lower() in rc.lower() for rc in result_cols)
                    for ec in expected_cols
                ) if expected_cols else True
            else:
                executable = False
                has_data = False
                col_match = False

            results.append({
                "query": query,
                "valid_syntax": val["is_valid"],
                "executable": executable,
                "has_data": has_data,
                "column_match": col_match,
                "code": code[:120],
                "time_s": gen_time,
                "errors": val.get("errors", []) + ([exec_result.get("error")] if not executable and val["is_valid"] else []),
            })

        except Exception as e:
            results.append({
                "query": query,
                "valid_syntax": False,
                "executable": False,
                "has_data": False,
                "column_match": False,
                "code": "",
                "time_s": round(time.time() - start, 3),
                "errors": [str(e)],
            })

    # Calculate metrics
    total = len(results)
    syntax_pass = sum(1 for r in results if r["valid_syntax"])
    exec_pass = sum(1 for r in results if r["executable"])
    data_pass = sum(1 for r in results if r["has_data"])
    col_pass = sum(1 for r in results if r["column_match"])
    avg_time = round(sum(r["time_s"] for r in results) / total, 3)

    return {
        "test_name": "Code Generation",
        "total_queries": total,
        "accuracy": round(exec_pass / total * 100, 1),
        "syntax_accuracy": round(syntax_pass / total * 100, 1),
        "execution_accuracy": round(exec_pass / total * 100, 1),
        "data_accuracy": round(data_pass / total * 100, 1),
        "column_match_accuracy": round(col_pass / total * 100, 1),
        "avg_time_s": avg_time,
        "details": results,
    }


# ═══════════════════════════════════════════════════════════
#  TEST 2: VALIDATION ACCURACY
# ═══════════════════════════════════════════════════════════

def test_validation() -> Dict:
    """
    Tests the validator's ability to:
      - Accept safe code (no false positives)
      - Block dangerous code (no false negatives)
    """
    safe_code = [
        ("df.head(10)", True),
        ("df.groupby('City')['AQI'].mean()", True),
        ("df.describe()", True),
        ("df['AQI'].value_counts()", True),
        ("df.sort_values('AQI', ascending=False).head(5)", True),
        ("df.corr(numeric_only=True)", True),
        ("df[df['AQI'] > 100]", True),
        ("df['AQI'].mean()", True),
        ("df.nlargest(10, 'AQI')", True),
        ("df.groupby('City').agg({'AQI': 'mean', 'Temperature': 'max'})", True),
    ]

    dangerous_code = [
        ("import os; os.system('rm -rf /')", False),
        ("exec('print(1)')", False),
        ("eval('1+1')", False),
        ("__import__('os').system('ls')", False),
        ("open('/etc/passwd', 'r').read()", False),
        ("df.to_csv('/tmp/stolen.csv')", False),
        ("df.to_excel('/tmp/data.xlsx')", False),
        ("import subprocess; subprocess.run(['ls'])", False),
        ("globals()['__builtins__']", False),
        ("df.drop('City', axis=1)", False),  # .drop() is blocked
    ]

    columns = ["City", "Year", "AQI", "Temperature", "Rainfall_mm", "GDP_Billion", "Population"]
    results = []

    for code, expected_safe in safe_code + dangerous_code:
        val = validate_query(code, columns)
        actual_safe = val["is_valid"]
        correct = actual_safe == expected_safe
        results.append({
            "code": code[:80],
            "expected": "safe" if expected_safe else "blocked",
            "actual": "safe" if actual_safe else "blocked",
            "correct": correct,
            "errors": val.get("errors", []),
        })

    total = len(results)
    correct_count = sum(1 for r in results if r["correct"])
    safe_correct = sum(1 for r, (_, exp) in zip(results, safe_code + dangerous_code) if r["correct"] and exp)
    block_correct = sum(1 for r, (_, exp) in zip(results, safe_code + dangerous_code) if r["correct"] and not exp)

    return {
        "test_name": "Query Validation",
        "total_tests": total,
        "overall_accuracy": round(correct_count / total * 100, 1),
        "safe_code_accuracy": round(safe_correct / len(safe_code) * 100, 1),
        "blocked_code_accuracy": round(block_correct / len(dangerous_code) * 100, 1),
        "false_positives": sum(1 for r, (_, exp) in zip(results, safe_code + dangerous_code) if not r["correct"] and exp),
        "false_negatives": sum(1 for r, (_, exp) in zip(results, safe_code + dangerous_code) if not r["correct"] and not exp),
        "details": results,
    }


# ═══════════════════════════════════════════════════════════
#  TEST 3: VISUALIZATION SELECTOR ACCURACY
# ═══════════════════════════════════════════════════════════

def test_viz_selector() -> Dict:
    """Tests if the viz selector picks the correct chart type."""
    test_cases = [
        # (data, columns, row_count, expected_chart)
        (
            [{"City": "A", "AQI": 10}, {"City": "B", "AQI": 20}, {"City": "C", "AQI": 30}],
            ["City", "AQI"], 3, "pie",  # ≤6 categories + 1 numeric = pie
        ),
        (
            [{"City": c, "AQI": v} for c, v in zip(list("ABCDEFGHIJ"), range(10))],
            ["City", "AQI"], 10, "bar",  # >6 categories = bar
        ),
        (
            [{"x": i, "y": i * 2} for i in range(20)],
            ["x", "y"], 20, "scatter",  # 2 numeric, many rows = scatter
        ),
        (
            [{"AQI": v} for v in range(20)],
            ["AQI"], 20, "histogram",  # single numeric, many rows
        ),
        (
            [{"value": 42}],
            ["value"], 1, "table",  # single value
        ),
        (
            # Square numeric matrix → heatmap
            [{"A": 1, "B": 0.8, "C": 0.3}, {"A": 0.8, "B": 1, "C": 0.5}, {"A": 0.3, "B": 0.5, "C": 1}],
            ["A", "B", "C"], 3, "heatmap",
        ),
    ]

    results = []
    for data, columns, row_count, expected in test_cases:
        viz = select_visualization(data, columns, row_count)
        actual = viz["chart_type"]
        results.append({
            "columns": columns,
            "row_count": row_count,
            "expected": expected,
            "actual": actual,
            "correct": actual == expected,
            "reason": viz["reason"],
        })

    total = len(results)
    correct = sum(1 for r in results if r["correct"])

    return {
        "test_name": "Visualization Selector",
        "total_tests": total,
        "accuracy": round(correct / total * 100, 1),
        "details": results,
    }


# ═══════════════════════════════════════════════════════════
#  TEST 4: INSIGHT GENERATOR ACCURACY
# ═══════════════════════════════════════════════════════════

def test_insight_generator(df: pd.DataFrame) -> Dict:
    """Tests whether insights contain expected information."""
    # Generate grouped data with known properties
    grouped = df.groupby("City")["AQI"].mean().reset_index().sort_values("AQI", ascending=False)
    data = json.loads(grouped.to_json(orient="records"))
    columns = list(grouped.columns)

    insights = generate_insights(data, columns)

    checks = {
        "has_summary": bool(insights.get("summary")),
        "has_highlights": len(insights.get("highlights", [])) > 0,
        "mentions_highest": any("highest" in h.lower() or "📈" in h for h in insights.get("highlights", [])),
        "mentions_average": any("average" in h.lower() or "📊" in h for h in insights.get("highlights", [])),
        "correct_row_count": insights.get("row_count") == len(data),
        "has_top3": any("top 3" in h.lower() or "🏆" in h for h in insights.get("highlights", [])),
    }

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    return {
        "test_name": "Insight Generator",
        "total_checks": total,
        "accuracy": round(passed / total * 100, 1),
        "checks": checks,
        "summary": insights.get("summary", ""),
        "num_highlights": len(insights.get("highlights", [])),
    }


# ═══════════════════════════════════════════════════════════
#  TEST 5: ANOMALY DETECTOR ACCURACY
# ═══════════════════════════════════════════════════════════

def test_anomaly_detector(df: pd.DataFrame) -> Dict:
    """Tests if anomaly detector finds the injected outliers."""
    data = json.loads(df.to_json(orient="records"))
    columns = list(df.columns)

    result = detect_anomalies(data, columns)

    # We injected outliers at:
    #   AQI=999.9 (row 5), Temperature=-50 (row 10)
    aqi_anomalies = result["anomaly_indices"].get("AQI", [])
    temp_anomalies = result["anomaly_indices"].get("Temperature", [])

    checks = {
        "detects_AQI_outlier_row5": 5 in aqi_anomalies,
        "detects_Temp_outlier_row10": 10 in temp_anomalies,
        "has_anomaly_insights": len(result.get("insights", [])) > 0,
        "total_anomalies_reasonable": 1 <= result["anomaly_count"] <= 30,
        "no_false_negative_AQI": len(aqi_anomalies) >= 1,
        "no_false_negative_Temp": len(temp_anomalies) >= 1,
    }

    passed = sum(1 for v in checks.values() if v)

    return {
        "test_name": "Anomaly Detector",
        "total_checks": len(checks),
        "accuracy": round(passed / len(checks) * 100, 1),
        "checks": checks,
        "total_anomalies_found": result["anomaly_count"],
        "aqi_anomaly_indices": aqi_anomalies,
        "temp_anomaly_indices": temp_anomalies,
    }


# ═══════════════════════════════════════════════════════════
#  TEST 6: FORECASTER ACCURACY
# ═══════════════════════════════════════════════════════════

def test_forecaster() -> Dict:
    """Tests forecast accuracy against known linear and noisy data."""
    # Known linear data: y = 2x + 10
    linear_data = [{"x": i, "y": 2 * i + 10} for i in range(1, 11)]
    linear_result = forecast(linear_data, "x", "y", periods=3, method="linear")

    # Expected: y(11)=32, y(12)=34, y(13)=36
    linear_checks = {
        "linear_success": "error" not in linear_result,
        "linear_trend_rising": linear_result.get("trend") == "rising",
        "linear_r2_high": linear_result.get("confidence", 0) >= 0.95,
        "linear_forecast_close": abs(linear_result.get("forecast", [{}])[0].get("y", 0) - 32) < 2,
    }

    # Noisy data (should still forecast reasonably)
    np.random.seed(42)
    noisy_data = [{"x": i, "y": round(3 * i + 5 + np.random.normal(0, 2), 2)} for i in range(1, 16)]
    noisy_result = forecast(noisy_data, "x", "y", periods=3, method="linear")

    noisy_checks = {
        "noisy_success": "error" not in noisy_result,
        "noisy_trend_rising": noisy_result.get("trend") == "rising",
        "noisy_r2_reasonable": noisy_result.get("confidence", 0) >= 0.7,
    }

    # Moving average test
    ma_result = forecast(linear_data, "x", "y", periods=3, method="moving_average")
    ma_checks = {
        "ma_success": "error" not in ma_result,
        "ma_has_forecast": len(ma_result.get("forecast", [])) == 3,
    }

    all_checks = {**linear_checks, **noisy_checks, **ma_checks}
    passed = sum(1 for v in all_checks.values() if v)

    return {
        "test_name": "Forecaster",
        "total_checks": len(all_checks),
        "accuracy": round(passed / len(all_checks) * 100, 1),
        "checks": all_checks,
        "linear_r2": linear_result.get("confidence"),
        "noisy_r2": noisy_result.get("confidence"),
    }


# ═══════════════════════════════════════════════════════════
#  TEST 7: END-TO-END PIPELINE
# ═══════════════════════════════════════════════════════════

def test_end_to_end(llm: LLMEngine, schema_summary: str, df: pd.DataFrame) -> Dict:
    """
    Tests the complete pipeline: NL query → code gen → validate →
    execute → viz → insights → result correctness.
    """
    column_names = list(df.columns)

    test_cases = [
        {
            "query": "Show average AQI by city",
            "check_fn": lambda r: (
                r["exec"]["success"]
                and "City" in r["exec"]["columns"]
                and len(r["exec"]["data"]) > 0
                and r["viz"]["chart_type"] in ("bar", "pie")
            ),
        },
        {
            "query": "What is the total population?",
            "check_fn": lambda r: (
                r["exec"]["success"]
                and len(r["exec"]["data"]) >= 1
            ),
        },
        {
            "query": "Show correlation between AQI and Temperature",
            "check_fn": lambda r: (
                r["exec"]["success"]
                and len(r["exec"]["data"]) > 0
            ),
        },
        {
            "query": "Count rows per city",
            "check_fn": lambda r: (
                r["exec"]["success"]
                and len(r["exec"]["data"]) > 0
            ),
        },
        {
            "query": "Show descriptive statistics",
            "check_fn": lambda r: (
                r["exec"]["success"]
                and len(r["exec"]["data"]) > 0
            ),
        },
    ]

    results = []
    for tc in test_cases:
        try:
            gen = llm.generate_code(tc["query"], schema_summary)
            val = validate_query(gen["code"], column_names)

            if not val["is_valid"]:
                results.append({"query": tc["query"], "passed": False, "stage": "validation", "error": val["errors"]})
                continue

            exec_result = execute_query(df, gen["code"])
            viz = select_visualization(
                exec_result.get("data", []),
                exec_result.get("columns", []),
                exec_result.get("row_count", 0),
            )
            insights = generate_insights(
                exec_result.get("data", []),
                exec_result.get("columns", []),
            )

            pipeline_result = {"exec": exec_result, "viz": viz, "insights": insights}
            passed = tc["check_fn"](pipeline_result)
            results.append({"query": tc["query"], "passed": passed, "stage": "complete", "chart": viz["chart_type"]})

        except Exception as e:
            results.append({"query": tc["query"], "passed": False, "stage": "error", "error": str(e)})

    total = len(results)
    passed = sum(1 for r in results if r["passed"])

    return {
        "test_name": "End-to-End Pipeline",
        "total_tests": total,
        "accuracy": round(passed / total * 100, 1),
        "details": results,
    }


# ═══════════════════════════════════════════════════════════
#  MAIN RUNNER
# ═══════════════════════════════════════════════════════════

def print_header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(result: Dict):
    name = result["test_name"]
    if "accuracy" in result:
        acc = result["accuracy"]
        status = "PASS" if acc >= 80 else "WARN" if acc >= 60 else "FAIL"
        print(f"\n  [{status}] {name}: {acc}%")
    elif "overall_accuracy" in result:
        acc = result["overall_accuracy"]
        status = "PASS" if acc >= 80 else "WARN" if acc >= 60 else "FAIL"
        print(f"\n  [{status}] {name}: {acc}%")

    # Print sub-metrics
    skip_keys = {"test_name", "details", "checks", "accuracy", "overall_accuracy"}
    for k, v in result.items():
        if k in skip_keys:
            continue
        if isinstance(v, dict):
            print(f"    {k}:")
            for sk, sv in v.items():
                status = "[Y]" if sv is True else "[N]" if sv is False else "   "
                print(f"      {status} {sk}: {sv}")
        elif isinstance(v, list) and len(v) <= 5:
            print(f"    {k}: {v}")
        else:
            print(f"    {k}: {v}")


def main():
    print_header("ACCURACY BENCHMARK - Generative AI Analysis Platform")
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Setup
    print("\n  Creating test dataset...")
    df = create_test_dataframe()
    schema = extract_schema(df)
    schema_summary = generate_schema_summary(schema)
    llm = LLMEngine()

    mode = "Gemini API" if not llm.is_stub else "Stub (keyword-based)"
    print(f"  LLM Mode: {mode}")
    print(f"  Dataset: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"  Columns: {', '.join(df.columns)}")

    # Run all tests
    all_results = []

    print_header("TEST 1: Code Generation")
    r1 = test_code_generation(llm, schema_summary, df)
    print_result(r1)
    # Show per-query detail
    for d in r1["details"]:
        status = "[Y]" if d["executable"] and d["has_data"] else "[N]"
        print(f"    {status} \"{d['query'][:50]}\" -> {'OK' if d['executable'] else 'FAIL'} ({d['time_s']}s)")
        if d["errors"]:
            for e in d["errors"][:1]:
                print(f"      -- {str(e)[:100]}")
    all_results.append(r1)

    print_header("TEST 2: Query Validation")
    r2 = test_validation()
    print_result(r2)
    for d in r2["details"]:
        status = "[Y]" if d["correct"] else "[N]"
        print(f"    {status} {d['code'][:60]:<62} expected={d['expected']:<7} actual={d['actual']}")
    all_results.append(r2)

    print_header("TEST 3: Visualization Selector")
    r3 = test_viz_selector()
    print_result(r3)
    for d in r3["details"]:
        status = "[Y]" if d["correct"] else "[N]"
        print(f"    {status} {str(d['columns']):<30} expected={d['expected']:<10} actual={d['actual']:<10} ({d['reason'][:40]})")
    all_results.append(r3)

    print_header("TEST 4: Insight Generator")
    r4 = test_insight_generator(df)
    print_result(r4)
    all_results.append(r4)

    print_header("TEST 5: Anomaly Detector")
    r5 = test_anomaly_detector(df)
    print_result(r5)
    all_results.append(r5)

    print_header("TEST 6: Forecaster")
    r6 = test_forecaster()
    print_result(r6)
    all_results.append(r6)

    print_header("TEST 7: End-to-End Pipeline")
    r7 = test_end_to_end(llm, schema_summary, df)
    print_result(r7)
    for d in r7["details"]:
        status = "[Y]" if d["passed"] else "[N]"
        extra = f" -> {d.get('chart', d.get('error', ''))}"
        print(f"    {status} \"{d['query'][:50]}\"{extra}")
    all_results.append(r7)

    # ── Final Summary ────────────────────────────────────────
    print_header("FINAL ACCURACY SUMMARY")
    print(f"  {'Component':<25} {'Accuracy':>10}  {'Status':>6}")
    print(f"  {'-' * 45}")

    accuracies = []
    for r in all_results:
        acc = r.get("accuracy") or r.get("overall_accuracy") or 0
        accuracies.append(acc)
        status = "PASS" if acc >= 80 else "WARN" if acc >= 60 else "FAIL"
        print(f"  {r['test_name']:<25} {acc:>9.1f}%  [{status}]")

    overall = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0
    print(f"  {'-' * 45}")
    status = "PASS" if overall >= 80 else "WARN" if overall >= 60 else "FAIL"
    print(f"  {'OVERALL AVERAGE':<25} {overall:>9.1f}%  [{status}]")
    print(f"\n  LLM Mode: {mode}")
    print(f"  Total tests run: {sum(r.get('total_tests', r.get('total_queries', r.get('total_checks', 0))) for r in all_results)}")
    print(f"{'=' * 60}\n")

    # Save results to JSON
    output_path = os.path.join(os.path.dirname(__file__), "accuracy_results.json")
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "llm_mode": mode,
        "dataset_shape": list(df.shape),
        "overall_accuracy": overall,
        "components": {r["test_name"]: r.get("accuracy") or r.get("overall_accuracy") for r in all_results},
    }
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to: {output_path}")


if __name__ == "__main__":
    main()
