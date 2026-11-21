"""G1.1 experimental library contract, executed in Python reference runtime.

This suite is a baseline for *future* JS/native differential tests; it does
not itself claim that those runtimes support G1 imports or module bundles.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "tests/g1_contract_fixtures.json").read_text(encoding="utf-8"))


def test_contract_schema_and_declared_exports():
    assert CONTRACT["schema_version"] == 1
    assert CONTRACT["status"] == "experimental_source_only"
    modules = CONTRACT["modules"]
    assert [m["id"] for m in modules] == ["math", "collections"]
    all_names = []
    for module in modules:
        src = ROOT / module["source"]
        assert src.is_file()
        tree = parse(src.read_text(encoding="utf-8"), filename=module["source"])
        assert all(node.kind == "function" for node in tree)
        declared = [node.value[0] for node in tree]
        assert len(declared) == len(set(declared))
        assert declared == module["exports"]
        all_names.extend(declared)
    assert len(all_names) == len(set(all_names))


def test_contract_does_not_change_g0_catalog():
    catalog = json.loads((ROOT / "stdlib/catalog.json").read_text(encoding="utf-8"))
    paths = {entry["source"] for entry in catalog["modules"]}
    assert not paths.intersection(m["source"] for m in CONTRACT["modules"])
    public_g0 = {name for entry in catalog["modules"] for name in entry["exports"]}
    public_g1 = {name for m in CONTRACT["modules"] for name in m["exports"]}
    assert public_g1.isdisjoint(public_g0)


def test_case_ids_and_expected_output_are_unambiguous():
    cases = CONTRACT["cases"]
    assert len(cases) >= 18
    ids = [case["id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert set(case) == {"id", "source", "output"}
        assert case["source"].endswith("\n")
        assert case["output"].endswith("\n")


@pytest.mark.parametrize("case", CONTRACT["cases"], ids=lambda item: item["id"])
def test_reference_g1_contract_case(case):
    module_sources = [
        (ROOT / m["source"]).read_text(encoding="utf-8")
        for m in CONTRACT["modules"]
    ]
    source = "\n".join(module_sources + [case["source"]])
    sink = io.StringIO()
    Interpreter(stdout=sink).run(parse(source))
    assert sink.getvalue() == case["output"]
