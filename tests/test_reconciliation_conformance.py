"""Amount-only reconciliation lesson: shared four-entry edge-case fixtures."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "examples/bank_reconciliation_matching.kasa").read_text(encoding="utf-8")
CASES = json.loads((ROOT / "tests/conformance_reconciliation.json").read_text(encoding="utf-8"))["cases"]


def source_for(case: dict) -> str:
    source = TEMPLATE
    for label in ("bank", "ledger"):
        original = "ma " + label + " = " + ("[5000, 7000, 5000, 12000]" if label == "bank" else "[5000, 5000, 9000, 7000]")
        new = "ma " + label + " = [" + ", ".join(map(str, case[label])) + "]"
        assert source.count(original) == 1, "Keep example template aligned with fixture builder"
        source = source.replace(original, new)
    return source


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_reconciliation_cases(case: dict) -> None:
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(source_for(case)))
    assert output.getvalue() == case["expected_stdout"]
