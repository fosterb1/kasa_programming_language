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
    assert output["counts"]["not_run"] == 19
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


def test_missing_executable_is_a_failure():
    runner = load_tool()
    result = runner.run_check(
        "missing", ["_kasa_very_unlikely_nonexistent_executable_"], env={"PATH": ""}
    )
    assert result["status"] == "failed"
    assert "Executable not found" in result["stderr_tail"]


def test_native_configure_failure_marks_dependent_steps_not_run(tmp_path, monkeypatch):
    runner = load_tool()
    steps = [
        ("Native CMake configure", ["dummy", "configure"], 1),
        ("Native C++ build", ["dummy", "build"], 1),
        ("Native Python conformance", ["dummy", "test"], 1),
    ]
    attempted = []

    def fake_run(name, command, *, env, timeout=180, dry_run=False):
        attempted.append(name)
        return {
            "name": name, "command": command, "status": "failed", "exit_code": 2,
            "duration_seconds": 0.1, "stdout_tail": "", "stderr_tail": "CMake failed",
        }

    monkeypatch.setattr(runner, "plan", lambda profile, wasm: steps)
    monkeypatch.setattr(runner, "run_check", fake_run)
    report = tmp_path / "failure.json"
    assert runner.main(["--profile", "full", "--report", str(report)]) == 1
    result = json.loads(report.read_text(encoding="utf-8"))
    assert attempted == ["Native CMake configure"]
    assert result["counts"] == {"passed": 0, "failed": 1, "not_run": 2}
    assert [check["status"] for check in result["checks"]] == ["failed", "not_run", "not_run"]
    assert "Blocked after failed step" in result["checks"][-1]["stderr_tail"]


def test_full_plan_executes_the_native_lexer_binary_not_an_empty_ctest_suite():
    runner = load_tool()
    lexer_checks = [command for name, command, _ in runner.plan("full", False)
                    if name == "Native lexer smoke"]
    assert len(lexer_checks) == 1
    assert Path(lexer_checks[0][0]).is_absolute()
    assert Path(lexer_checks[0][0]).name.startswith("kasa-lexer-smoke")


def test_parity_plan_runs_all_four_language_execution_paths():
    runner = load_tool()
    steps = runner.plan("parity", False)
    names = [name for name, _, _ in steps]
    assert names == [
        "Python semantic conformance",
        "JavaScript semantic and diagnostics conformance",
        "Native CMake configure",
        "Native C++ build",
        "Native mixed-number precision smoke",
        "Native decimal display smoke",
        "Native/Python decimal display differential",
        "Native/Python numeric differential",
        "Native Python conformance",
        "Native KBC1 round-trip and rejection tests",
        "Native diagnostic-category conformance",
    ]
    # Ensure the conformance.py stage is truly the native/Python harness and
    # the compiled VM path comes from the CMake build, not a stale executable.
    assert steps[7][1][1] == "native/tests/numeric_differential.py"
    assert Path(steps[7][1][-1]).name.startswith("kasa-numeric-compare-probe")
    assert steps[8][1][1] == "native/tests/conformance.py"
    assert steps[9][1][1] == "native/tests/test_bytecode.py"
    assert steps[8][1][-1] == steps[9][1][-1] == steps[10][1][-1]
    assert steps[10][1][1] == "native/tests/diagnostic_conformance.py"


def test_parity_dry_run_never_reports_executed_or_passed(tmp_path):
    report = tmp_path / "parity.json"
    result = subprocess.run(
        [sys.executable, str(TOOL), "--profile", "parity",
         "--dry-run", "--report", str(report)],
        check=False, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["profile"] == "parity"
    assert payload["counts"] == {"passed": 0, "failed": 0, "not_run": 11}
    assert len(payload["checks"]) == 11
    assert "DRY RUN ONLY" in result.stdout
    assert "source_revision" in payload
    assert set(payload["source_revision"]) == {"commit", "working_tree_clean"}


def test_parity_wasm_attempt_requires_full_profile(tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL), "--profile", "parity",
         "--wasm", "--dry-run", "--report", str(tmp_path / "bad.json")],
        check=False, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode != 0
    assert "requires --profile full" in result.stderr


def test_revision_reports_no_commit_when_git_is_unavailable(monkeypatch):
    runner = load_tool()
    monkeypatch.setattr(runner.shutil, "which", lambda name: None)
    assert runner.source_revision() == {"commit": None, "working_tree_clean": None}


def test_full_and_quick_counts_include_numeric_differential():
    runner = load_tool()
    assert len(runner.plan("quick", False)) == 7
    assert len(runner.plan("full", False)) == 19
