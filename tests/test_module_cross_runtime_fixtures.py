"""Shared G0.4 Python opt-in module conformance fixtures.

These are experimental source-runner checks, not native/KBC1 tests.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from run_kasa_modules_experimental import execute_module_source
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa.core import KasaError

CASES = json.loads((ROOT / "tests/conformance_experimental_modules.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda case: case["id"])
def test_opt_in_python_module_contract(case):
    output = io.StringIO()
    if "output" in case:
        runtime = execute_module_source(case["source"], stdout=output)
        assert output.getvalue() == case["output"]
        assert "m" not in runtime.globals.values
        assert "c" not in runtime.globals.values
    else:
        with pytest.raises(KasaError) as caught:
            execute_module_source(case["source"], stdout=output)
        assert caught.value.category == case["python_category"]
        assert case["error_contains"].lower() in str(caught.value).lower()
        if "line" in case:
            assert (caught.value.token.line, caught.value.token.column) == (case["line"], case["column"])
        assert output.getvalue() == ""
