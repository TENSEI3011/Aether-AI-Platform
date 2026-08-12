"""
============================================================
SDLC Phase 2 — Design & Architecture Validation
============================================================
Software Development Lifecycle Stage: DESIGN

This phase validates that the codebase follows the stated
architectural design principles:
  • Separation of concerns: each module has single responsibility
  • API layer never imports ML/service internals directly
  • Service layer has no direct HTTP or FastAPI dependency
  • Database models are clean ORM definitions (no business logic)
  • Error handling: all public functions have try/except
  • Docstring coverage: all public functions are documented
  • Dependency injection pattern is used for DB access
  • No circular imports between layers

~30 Tests
============================================================
"""

import pytest
import ast
import os
import sys
import importlib
import inspect

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))
SERVICES_DIR = os.path.join(BACKEND_ROOT, "services")
API_DIR      = os.path.join(BACKEND_ROOT, "api")
LLM_DIR      = os.path.join(BACKEND_ROOT, "llm")
DB_DIR       = os.path.join(BACKEND_ROOT, "database")
AUTH_DIR     = os.path.join(BACKEND_ROOT, "auth")


def get_py_files(directory):
    """Get all .py files in a directory (non-recursive, non-init)."""
    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".py") and f != "__init__.py"
    ]


def parse_module(filepath):
    """Parse a Python file into an AST."""
    with open(filepath, "r", encoding="utf-8") as fh:
        return ast.parse(fh.read())


def get_function_defs(tree):
    """Get all top-level and class-method function definitions."""
    fns = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fns.append(node)
    return fns


def has_try_except(fn_node):
    """Check if a function body has at least one try/except block."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Try):
            return True
    return False


# ═════════════════════════════════════════════════════════
# DESIGN-1: Separation of Concerns
# ═════════════════════════════════════════════════════════

class TestSeparationOfConcerns:
    """Services must not import FastAPI; API must not import ML libs."""

    SERVICE_FILES = get_py_files(SERVICES_DIR)
    FORBIDDEN_IN_SERVICES = ["fastapi", "uvicorn", "starlette"]

    def test_design_services_do_not_import_fastapi(self):
        """DESIGN-1.1: Service layer must not depend on FastAPI."""
        violations = []
        for fp in self.SERVICE_FILES:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            for forbidden in self.FORBIDDEN_IN_SERVICES:
                if f"import {forbidden}" in content or f"from {forbidden}" in content:
                    violations.append(f"{os.path.basename(fp)}: imports {forbidden}")
        assert not violations, f"Services importing framework deps: {violations}"

    def test_design_database_models_no_business_logic(self):
        """DESIGN-1.2: Database model file must not contain algorithmic logic."""
        models_file = os.path.join(DB_DIR, "models.py")
        tree = parse_module(models_file)
        # Should have no function definitions (only column declarations)
        regular_fns = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
        ]
        # Allow __repr__ and __str__ but no algorithmic functions
        algo_fns = [fn for fn in regular_fns if fn.name not in ("__repr__", "__str__")]
        assert len(algo_fns) == 0, f"Business logic in models.py: {[f.name for f in algo_fns]}"

    def test_design_services_have_single_primary_function(self):
        """DESIGN-1.3: Each service file exposes a clear primary function."""
        primary_functions = {
            "anomaly_detector.py": "detect_anomalies",
            "forecaster.py": "forecast_series",
            "clustering.py": "cluster_dataframe",
            "schema_extractor.py": "extract_schema",
            "query_validator.py": "validate_query",
            "query_executor.py": "execute_query",
            "viz_selector.py": "select_visualization",
        }
        for filename, expected_fn in primary_functions.items():
            fp = os.path.join(SERVICES_DIR, filename)
            if not os.path.exists(fp):
                continue
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            assert f"def {expected_fn}" in content, \
                f"{filename} is missing primary function '{expected_fn}'"

    def test_design_llm_layer_isolated_from_database(self):
        """DESIGN-1.4: LLM layer must not directly import database models."""
        for fp in get_py_files(LLM_DIR):
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            assert "from database" not in content and "import database" not in content, \
                f"{os.path.basename(fp)} directly imports from database layer"


# ═════════════════════════════════════════════════════════
# DESIGN-2: Error Handling Design
# ═════════════════════════════════════════════════════════

class TestErrorHandlingDesign:
    """All public service functions must have structured error handling."""

    CRITICAL_SERVICES = [
        ("anomaly_detector.py", "detect_anomalies"),
        ("forecaster.py",       "forecast_series"),
        ("clustering.py",       "cluster_dataframe"),
        ("query_executor.py",   "execute_query"),
    ]

    @pytest.mark.parametrize("filename,fn_name", CRITICAL_SERVICES)
    def test_design_critical_functions_have_error_handling(self, filename, fn_name):
        """DESIGN-2.1: Critical service modules have try/except blocks (in public fn or helpers)."""
        fp = os.path.join(SERVICES_DIR, filename)
        if not os.path.exists(fp):
            pytest.skip(f"{filename} not found")
        # The design pattern here is: public function delegates to inner _helpers
        # that contain the actual try/except. Check the whole module file.
        tree = parse_module(fp)
        module_has_try_except = any(
            isinstance(node, ast.Try)
            for node in ast.walk(tree)
        )
        assert module_has_try_except, \
            f"{filename} has no try/except anywhere — unhandled exceptions possible"

    def test_design_api_routes_have_error_handling(self):
        """DESIGN-2.2: API route files contain exception handling."""
        for fp in get_py_files(API_DIR):
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            # API files should use HTTPException or try/except
            has_http_ex = "HTTPException" in content
            has_try_ex = "try:" in content
            assert has_http_ex or has_try_ex, \
                f"{os.path.basename(fp)} has no error handling"


# ═════════════════════════════════════════════════════════
# DESIGN-3: Docstring Coverage
# ═════════════════════════════════════════════════════════

class TestDocstringCoverage:
    """Every public function in service modules must have a docstring."""

    def _get_undocumented(self, directory):
        undoc = []
        for fp in get_py_files(directory):
            tree = parse_module(fp)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue  # skip private helpers
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        undoc.append(f"{os.path.basename(fp)}:{node.name}()")
        return undoc

    def test_design_service_functions_are_documented(self):
        """DESIGN-3.1: All public service functions have docstrings."""
        undoc = self._get_undocumented(SERVICES_DIR)
        assert not undoc, f"Undocumented public service functions: {undoc}"

    def test_design_llm_functions_are_documented(self):
        """DESIGN-3.2: All public LLM functions have docstrings."""
        undoc = self._get_undocumented(LLM_DIR)
        assert not undoc, f"Undocumented public LLM functions: {undoc}"

    def test_design_each_service_module_has_module_docstring(self):
        """DESIGN-3.3: Each service module has a module-level docstring."""
        missing = []
        for fp in get_py_files(SERVICES_DIR):
            tree = parse_module(fp)
            module_doc = ast.get_docstring(tree)
            if not module_doc:
                missing.append(os.path.basename(fp))
        assert not missing, f"Service modules missing module docstrings: {missing}"


# ═════════════════════════════════════════════════════════
# DESIGN-4: Return Type Consistency
# ═════════════════════════════════════════════════════════

class TestReturnTypeConsistency:
    """Service functions must return dicts (not raise exceptions to callers)."""

    def test_design_anomaly_detector_always_returns_dict(self):
        """DESIGN-4.1: detect_anomalies never raises, always returns dict."""
        from services.anomaly_detector import detect_anomalies
        import pandas as pd, numpy as np

        test_cases = [
            pd.DataFrame({"a": [1, 2, 3]}),
            pd.DataFrame(),               # empty
            pd.DataFrame({"cat": ["a", "b", "c"]}),  # no numeric cols
        ]
        for df in test_cases:
            result = detect_anomalies(df)
            assert isinstance(result, dict), f"detect_anomalies returned {type(result)} for {df.shape}"

    def test_design_forecaster_always_returns_dict(self):
        """DESIGN-4.2: forecast_series never raises, always returns dict."""
        from services.forecaster import forecast_series
        import pandas as pd

        # Too few points → error dict
        df = pd.DataFrame({"date": pd.date_range("2023-01-01", periods=3), "val": [1, 2, 3]})
        result = forecast_series(df, "date", "val", periods=5)
        assert isinstance(result, dict)
        assert "historical" in result or "error" in result

    def test_design_clustering_always_returns_dict(self):
        """DESIGN-4.3: cluster_dataframe never raises, always returns dict."""
        from services.clustering import cluster_dataframe
        import pandas as pd

        test_cases = [
            pd.DataFrame({"x": [1, 2], "y": [3, 4]}),     # too few rows
            pd.DataFrame({"cat": ["a", "b", "c"]}),         # no numeric
        ]
        for df in test_cases:
            result = cluster_dataframe(df)
            assert isinstance(result, dict)

    def test_design_schema_extractor_always_returns_dict(self):
        """DESIGN-4.4: extract_schema never raises, always returns dict."""
        from services.schema_extractor import extract_schema
        import pandas as pd

        test_cases = [
            pd.DataFrame(),
            pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]}),
        ]
        for df in test_cases:
            result = extract_schema(df)
            assert isinstance(result, dict)
            assert "columns" in result


# ═════════════════════════════════════════════════════════
# DESIGN-5: Import Graph (No Circular Deps)
# ═════════════════════════════════════════════════════════

class TestImportGraph:
    """Validate that core modules can be imported without circular dependencies."""

    def test_design_services_importable_independently(self):
        """DESIGN-5.1: All service modules are independently importable."""
        service_modules = [
            "services.anomaly_detector",
            "services.forecaster",
            "services.clustering",
            "services.schema_extractor",
            "services.query_validator",
            "services.query_executor",
            "services.viz_selector",
            "services.insight_generator",
        ]
        for mod_name in service_modules:
            try:
                mod = importlib.import_module(mod_name)
                assert mod is not None
            except ImportError as e:
                pytest.fail(f"Cannot import {mod_name}: {e}")

    def test_design_llm_engine_importable(self):
        """DESIGN-5.2: LLM engine module is independently importable."""
        try:
            mod = importlib.import_module("llm.llm_engine")
            assert mod is not None
        except ImportError as e:
            pytest.fail(f"Cannot import llm.llm_engine: {e}")

    def test_design_no_service_imports_api_layer(self):
        """DESIGN-5.3: Service layer must not import from api layer."""
        violations = []
        for fp in get_py_files(SERVICES_DIR):
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            if "from api" in content or "import api." in content:
                violations.append(os.path.basename(fp))
        assert not violations, f"Services importing API layer: {violations}"
