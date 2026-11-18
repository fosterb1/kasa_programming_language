"""Shared signed int64 minimum source program contract."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, parse

CASES = json.loads((Path(__file__).parent / "conformance_int64_boundary.json").read_text(encoding="utf-8"))["cases"]

@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_signed_int64_minimum(case: dict) -> None:
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(case["source"]))
    assert out.getvalue() == case["expected_stdout"]
