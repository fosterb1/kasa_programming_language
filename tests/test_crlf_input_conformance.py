"""Shared Windows-style input normalization contract for Kasa bisa()."""
from __future__ import annotations

import io
import json
from pathlib import Path
import pytest

from kasa import Interpreter, parse

CASES = json.loads(
    (Path(__file__).parent / "conformance_crlf_input.json").read_text(encoding="utf-8")
)["cases"]

@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_crlf_input_contract(case: dict) -> None:
    out = io.StringIO()
    runtime = Interpreter(stdout=out, stdin=io.StringIO(case["stdin"]))
    runtime.run(parse(case["source"]))
    assert out.getvalue() == case["expected_stdout"]
