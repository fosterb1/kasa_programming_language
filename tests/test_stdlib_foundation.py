"""Portable source-level Kasa stdlib prototype cases (not an import mechanism)."""
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
CORPUS = json.loads((ROOT / "tests/conformance_stdlib_foundation.json").read_text(encoding="utf-8"))
SOURCE = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in CORPUS["libraries"])

@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda c: c["name"])
def test_stdlib_portable_python(case):
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(SOURCE + "\n" + case["source"] + "\n"))
    assert out.getvalue() == case["expected_stdout"]
