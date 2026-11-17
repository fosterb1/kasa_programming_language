"""Shared one-based Unicode code-point source position checks.

The errors are intentional syntax errors. These tests verify positions, not
the quality of translated error messages or human language approval.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from kasa import KasaError, parse

FIXTURES = json.loads(
    (Path(__file__).with_name("conformance_source_locations.json")).read_text(encoding="utf-8")
)

@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda case: case["name"])
def test_python_source_coordinates(case: dict) -> None:
    with pytest.raises(KasaError) as exc:
        parse(case["source"])
    error = exc.value
    assert error.category == case["category"]
    assert (error.token.line, error.token.column) == (case["line"], case["column"])
