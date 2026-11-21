"""Tests for the offline native/browser Studio verification orchestrator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("offline_studio", ROOT / "scripts/verify_studio_offline.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def test_profiles_have_expected_order_and_no_deployment():
    assert [name for name, _ in mod.plan("native")] == ["native_full"]
    assert [name for name, _ in mod.plan("browser")] == [
        "wasm_build", "wasm_package", "browser_playground", "browser_modules", "browser_wasm"
    ]
    assert mod.plan("all") == mod.plan("native") + mod.plan("browser")
    assert not any("netlify" in " ".join(cmd).lower() for _, cmd in mod.plan("all"))


def test_dry_run_never_executes(monkeypatch, tmp_path):
    def forbid(*_args, **_kwargs):
        raise AssertionError("Dry run must not execute external commands")
    monkeypatch.setattr(mod.subprocess, "run", forbid)
    output = tmp_path / "report.json"
    assert mod.main(["--profile", "all", "--dry-run", "--report", str(output)]) == 0
    import json
    report = json.loads(output.read_text())
    assert report["dry_run"] is True
    assert report["not_run"] == 6 and report["passed"] == 0


def test_fail_fast_reports_failure(monkeypatch, tmp_path):
    class Result:
        returncode = 7
    monkeypatch.setattr(mod.shutil, "which", lambda _name: "/usr/bin/mock")
    monkeypatch.setattr(mod.subprocess, "run", lambda *_args, **_kwargs: Result())
    output = tmp_path / "failure.json"
    assert mod.main(["--profile", "all", "--report", str(output)]) == 1
    import json
    report = json.loads(output.read_text())
    assert report["failed"] == 1
    assert len(report["checks"]) == 1
    assert report["checks"][0]["exit_code"] == 7
