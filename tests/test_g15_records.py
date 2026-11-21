"""G1.5 positional-record source-only fixtures; Python + Node parity."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "stdlib/g15/records.kasa"
MANIFEST = ROOT / "tests/g15_record_cases.json"


def cases():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1 and data["status"] == "g15_source_only_experimental"
    assert data["library"] == "stdlib/g15/records.kasa"
    assert len(data["cases"]) == 10
    assert len({c["id"] for c in data["cases"]}) == 10
    return data["cases"]


@pytest.mark.parametrize("item", cases(), ids=lambda item: item["id"])
def test_python_record_contract(item):
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(LIBRARY.read_text(encoding="utf-8") + "\n" + item["source"]))
    assert out.getvalue() == item["output"]


def test_js_record_contract():
    process = subprocess.run(
        ["node", "tests/g15_record_js.cjs"], cwd=ROOT,
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    report = json.loads(process.stdout)
    assert report["schema_version"] == 1
    assert [r["id"] for r in report["results"]] == [c["id"] for c in cases()]
    assert all(r["pass"] for r in report["results"])


def test_g1_catalog_unmodified():
    manifest = json.loads((ROOT / "stdlib/g1/catalog.json").read_text(encoding="utf-8"))
    assert set(m["id"] for m in manifest["modules"]) == {"math", "collections"}
    assert not any("records" in m["source"] for m in manifest["modules"])
