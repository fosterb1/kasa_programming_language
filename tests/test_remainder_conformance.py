"""Shared negative-remainder conformance cases for the Python Kasa reference."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from kasa import Interpreter, KasaError, parse

FIXTURES = json.loads(
    (Path(__file__).with_name("conformance_remainder.json")).read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda case: case["name"])
def test_remainder_success(case: dict) -> None:
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(case["source"]))
    assert output.getvalue() == case["expected_stdout"]


@pytest.mark.parametrize("case", FIXTURES["errors"], ids=lambda case: case["name"])
def test_remainder_error_category(case: dict) -> None:
    with pytest.raises(KasaError) as exc:
        Interpreter(stdout=io.StringIO()).run(parse(case["source"]))
    assert exc.value.category == case["category"]
