"""Kasa's shared language contract, independent of Python's host semantics."""
from __future__ import annotations

import io
import json
from pathlib import Path

from kasa.core import Interpreter, KasaError, parse

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


def test_all_success_cases():
    assert CASES["schema"] == "kasa-conformance-v1"
    for case in CASES["success"]:
        sink = io.StringIO()
        engine = Interpreter(stdout=sink, stdin=io.StringIO(case.get("input", "")))
        engine.run(parse(case["source"]))
        assert sink.getvalue() == case["output"], case["id"]


def test_all_failure_categories():
    for case in CASES["failures"]:
        try:
            engine = Interpreter(stdout=io.StringIO(), stdin=io.StringIO())
            engine.run(parse(case["source"]))
        except KasaError as error:
            assert error.category == case["error"], case["id"]
        else:
            raise AssertionError(f"Expected {case['error']} for {case['id']}")
