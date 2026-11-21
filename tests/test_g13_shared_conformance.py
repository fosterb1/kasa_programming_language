"""G1.3 shared corpus integrity; no native binary required for these checks."""
from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from run_kasa_modules_experimental import execute_module_source
    from link_kasa_modules_hygienic import link_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def cases():
    data = json.loads((ROOT / "tests/g13_cross_runtime_cases.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["status"] == "experimental_g1_shared_source_and_expected_output"
    rows = data["cases"]
    assert len(rows) == 12
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(("output" in row) != ("reject" in row) for row in rows)
    return rows


@pytest.mark.parametrize("item", cases(), ids=lambda x: x["id"])
def test_python_contract_and_rejection(item):
    out = io.StringIO()
    if "output" in item:
        execute_module_source(item["source"], stdout=out, generation="g1")
        assert out.getvalue() == item["output"]
        assert link_source(item["source"], generation="g1")
    else:
        with pytest.raises(Exception, match="(?i)" + item["reject"]):
            execute_module_source(item["source"], stdout=out, generation="g1")
        assert out.getvalue() == ""
        with pytest.raises(Exception, match="(?i)" + item["reject"]):
            link_source(item["source"], generation="g1")


def test_js_uses_same_fixture_ids():
    result = subprocess.run(
        ["node", str(ROOT / "tests/g13_js_fixture_runner.cjs")],
        cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stderr + result.stdout
    report = json.loads(result.stdout)
    assert report["schema_version"] == 1
    assert [entry["id"] for entry in report["results"]] == [item["id"] for item in cases()]
    assert all(entry["pass"] for entry in report["results"])
