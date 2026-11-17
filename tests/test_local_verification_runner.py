"""Unit tests for the independent, no-Actions Kasa verification command."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "verify_local.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("kasa_verify_local", TOOL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runner_dry_run_never_claims_tests_passed(tmp_path):
    report = tmp_path / "verify.json"
    result = subprocess.run(
        [sys.executable, str(TOOL), "--profile", "full", "--dry-run", "--report", str(report)],
        check=False, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(report.read_text(encoding="utf-8"))
    assert output["dry_run"] is True
    assert output["counts"]["passed"] == 0
    assert output["counts"]["not_run"] == 8
    assert "NOT a pass" in result.stdout


def test_runner_uses_exit_codes_not_empty_output():
    runner = load_tool()
    env = {"PATH": __import__("os").environ.get("PATH", "")}
    successful = runner.run_check(
        "blank success", [sys.executable, "-c", "pass"], env=env
    )
    failing = runner.run_check(
        "explicit fail", [sys.executable, "-c", "raise SystemExit(4)"], env=env
    )
    assert successful["status"] == "passed"
    assert failing["status"] == "failed" and failing["exit_code"] == 4


def test_wasm_requires_full_profile(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL), "--wasm", "--dry-run", "--report", str(tmp_path / "x.json")],
        check=False, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "requires --profile full" in result.stderr
