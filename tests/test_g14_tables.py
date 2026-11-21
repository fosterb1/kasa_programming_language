"""G1.4 source-only table helpers; shared fixtures with JS and native tests."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "stdlib/g14/tables.kasa"
CORPUS = ROOT / "tests/g14_table_cases.json"


def cases():
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["status"] == "experimental_source_only"
    assert manifest["library"] == "stdlib/g14/tables.kasa"
    items = manifest["cases"]
    assert len(items) == 10 and len({item["id"] for item in items}) == 10
    return items


@pytest.mark.parametrize("item", cases(), ids=lambda item: item["id"])
def test_reference_source_contract(item):
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(SOURCE.read_text(encoding="utf-8") + "\n" + item["source"]))
    assert output.getvalue() == item["output"]


def test_node_shared_source_contract():
    proc = subprocess.run(["node", "tests/g14_table_js.cjs"], cwd=ROOT,
                          capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    report = json.loads(proc.stdout)
    assert [item["id"] for item in report["results"]] == [item["id"] for item in cases()]
    assert all(item["pass"] for item in report["results"])


def test_g1_pinned_manifest_remains_unchanged():
    data = json.loads((ROOT / "stdlib/g1/catalog.json").read_text(encoding="utf-8"))
    assert [module["id"] for module in data["modules"]] == ["math", "collections"]
    assert all("tables" not in entry["source"] for entry in data["modules"])
