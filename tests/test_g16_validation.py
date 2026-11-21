"""G1.6 typed record validation contracts for the independent Python adapter."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from g16_validate_record import ValidationContractError, validate_record
finally:
    sys.path.remove(str(ROOT / "scripts"))

CASES = json.loads((ROOT / "tests/g16_validation_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("item", CASES["cases"], ids=lambda item: item["id"])
def test_python_validation(item):
    assert validate_record(CASES["schema"], item["record"]) == item["expected"]


@pytest.mark.parametrize("item", CASES["invalid_schemas"], ids=lambda item: item["id"])
def test_invalid_schema_rejected(item):
    with pytest.raises(ValidationContractError, match=item["reject"]):
        validate_record(item["schema"], [])


def test_js_independent_contract():
    proc = subprocess.run(["node", "tests/g16_validation_js.cjs"], cwd=ROOT,
                          capture_output=True, text=True, timeout=30, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["passed"] is True
    assert report["cases"] == len(CASES["cases"])
    assert report["invalid_schemas"] == len(CASES["invalid_schemas"])


def test_g1_catalog_not_modified():
    manifest = json.loads((ROOT / "stdlib/g1/catalog.json").read_text(encoding="utf-8"))
    assert set(item["id"] for item in manifest["modules"]) == {"math", "collections"}
