"""Shared nɔma ASCII numeric conversion conformance cases."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, KasaError, parse

CASES = json.loads((Path(__file__).parent / "conformance_numeric_conversion.json").read_text(encoding="utf-8"))["cases"]

@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_numeric_conversion_contract(case: dict) -> None:
    out = io.StringIO()
    runtime = Interpreter(stdout=out)
    if "expected_stdout" in case:
        runtime.run(parse(case["source"]))
        assert out.getvalue() == case["expected_stdout"]
    else:
        with pytest.raises(KasaError) as raised:
            runtime.run(parse(case["source"]))
        assert raised.value.category == case["error_category"]
