"""Candidate arbitrary-precision integer language contract (Python reference)."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from kasa import Interpreter, parse


CASES = json.loads(
    (Path(__file__).parent / "conformance_arbitrary_integers.json").read_text(encoding="utf-8")
)["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_arbitrary_integer_reference_contract(case: dict) -> None:
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(case["source"]))
    assert output.getvalue() == case["expected_stdout"]
