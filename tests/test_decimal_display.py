"""The Python Kasa reference defines the expected decimal output contract."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/conformance_decimal_display.json").read_text(encoding="utf-8"))["cases"]

@pytest.mark.parametrize("fixture", CASES, ids=lambda case: case["name"])
def test_decimal_display_python_reference(fixture: dict) -> None:
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(fixture["source"]))
    assert out.getvalue() == fixture["expected_stdout"]
