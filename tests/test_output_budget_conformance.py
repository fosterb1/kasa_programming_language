"""Cross-runtime output budget conformance: Python reference implementation."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, parse
from kasa.core import KasaError

CASES = json.loads((Path(__file__).parent / "conformance_output_budget.json").read_text(encoding="utf-8"))["cases"]

@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_output_budget_reference(case: dict) -> None:
    output = io.StringIO()
    runtime = Interpreter(stdout=output, stdin=io.StringIO(case["stdin"]))
    source = parse(case["source"])
    if case["expected_ok"]:
        runtime.run(source)
    else:
        with pytest.raises(KasaError) as error:
            runtime.run(source)
        assert error.value.category == case["error_category"]
    assert len(output.getvalue()) == case["expected_stdout_characters"]
