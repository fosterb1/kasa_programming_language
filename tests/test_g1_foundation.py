"""Portable G1 source-only conformance; no catalog/module mutation."""
from __future__ import annotations
import io
import json
from pathlib import Path

import pytest
from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "tests/conformance_g1_foundation.json").read_text(encoding="utf-8"))
assert FIXTURES["schema_version"] == 1
SOURCE = "\n".join((ROOT / p).read_text(encoding="utf-8") for p in FIXTURES["libraries"])


@pytest.mark.parametrize("case", FIXTURES["cases"], ids=lambda c: c["name"])
def test_g1_python_source_parity(case):
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(SOURCE + "\n" + case["source"] + "\n"))
    assert output.getvalue() == case["expected_stdout"]


def test_g1_fixtures_do_not_change_catalog():
    catalog = json.loads((ROOT / "stdlib/catalog.json").read_text(encoding="utf-8"))
    assert all(entry["source"].startswith("stdlib/experimental/") for entry in catalog["modules"])
    assert all(p.startswith("stdlib/g1/") for p in FIXTURES["libraries"])
