#!/usr/bin/env python3
"""Collect reproducible, local-only G0.5 release evidence as JSON.

Runs full native verification, focused pytest and the two native/KBC1 module
gates. No CI integration or merge approval is implied. A skip forces the
report to 'review_required', never 'passed'.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "tests/test_g05_build_reproducibility.py",
    "tests/test_g05_compile_command.py",
    "tests/test_g05_native_mapped_runner.py",
    "tests/test_g05_source_map.py",
    "tests/test_g05_diagnostic_mapping.py",
    "tests/test_g05_namespace_collision.py",
    "tests/test_hygienic_module_linker.py",
    "tests/test_native_module_preflight.py",
    "tests/test_g05_release_evidence.py",
)
GATES = (
    ("native_full", [sys.executable, "scripts/verify_local.py", "--profile", "full",
                     "--report", "build/g05-full-native-evidence.json"], 600),
    ("g05_pytest", [sys.executable, "-m", "pytest", "-q", "-rs", *TESTS], 240),
    ("native_kbc_parity", [sys.executable, "scripts/verify_g05_native_kbc.py"], 180),
    ("kbc_independence", [sys.executable, "scripts/verify_g05_kbc_independence.py"], 180),
)


def revision() -> dict:
    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args], cwd=ROOT, text=True, capture_output=True,
                timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "tracked_changes": git("status", "--porcelain", "--untracked-files=no"),
    }


def pytest_summary(output: str) -> dict:
    """Parse the terminal summary without treating skipped tests as passes."""
    summary = {}
    for key in ("passed", "failed", "error", "errors", "skipped", "xfailed", "xpassed"):
        match = re.search(r"\b(\d+) " + key + r"\b", output)
        if match:
            summary[key] = int(match.group(1))
    # -rs reports individual short skip details; keep all lines for audit.
    summary["skip_details"] = [
        line.strip() for line in output.splitlines()
        if re.search(r"\bSKIPPED\b", line)
    ]
    return summary


def execute(label: str, argv: list[str], timeout: int) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
            check=False,
        )
        return {
            "name": label, "command": argv,
            "status": "passed" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "stdout_tail": result.stdout[-16000:],
            "stderr_tail": result.stderr[-8000:],
            "duration_seconds": round(time.monotonic() - started, 3),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "name": label, "command": argv, "status": "failed",
            "exit_code": None, "stdout_tail": "", "stderr_tail": str(exc),
            "duration_seconds": round(time.monotonic() - started, 3),
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        default=ROOT / "build" / "g05-release-evidence.json")
    args = parser.parse_args(argv)
    report = args.report.absolute()
    if report != ROOT / "build" / "g05-release-evidence.json":
        parser.error("Report path fixed to build/g05-release-evidence.json")
    before = revision()
    records = []
    for name, command, timeout in GATES:
        record = execute(name, command, timeout)
        records.append(record)
        print(f"{record['status'].upper():7} {name}", flush=True)
        if record["status"] == "failed":
            print(record["stderr_tail"] or record["stdout_tail"], file=sys.stderr)
    after = revision()
    pytest_record = next(item for item in records if item["name"] == "g05_pytest")
    summary = pytest_summary(pytest_record["stdout_tail"] + "\n" + pytest_record["stderr_tail"])
    skip_count = summary.get("skipped", 0)
    all_passed = all(item["status"] == "passed" for item in records)
    same_commit = bool(before["commit"]) and before["commit"] == after["commit"]
    branch_ok = before["branch"] == after["branch"] == "dev/g05-native-module-contract"
    clean_tracked = before["tracked_changes"] == after["tracked_changes"] == ""
    full_report = ROOT / "build" / "g05-full-native-evidence.json"
    full_profile_ok = False
    if full_report.is_file():
        try:
            full_data = json.loads(full_report.read_text(encoding="utf-8"))
            full_profile_ok = (
                full_data.get("profile") == "full"
                and full_data.get("dry_run") is False
                and full_data.get("counts", {}).get("failed") == 0
                and full_data.get("counts", {}).get("not_run") == 0
                and full_data.get("source_revision", {}).get("commit") == before["commit"]
                and full_data.get("source_revision_after", {}).get("commit") == after["commit"]
                and next(item for item in records if item["name"] == "native_full")["status"] == "passed"
            )
        except (OSError, json.JSONDecodeError):
            pass
    status = (
        "passed" if (all_passed and skip_count == 0 and "passed" in summary
                     and same_commit and branch_ok and clean_tracked and full_profile_ok)
        else "failed" if not all_passed else "review_required"
    )
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "experimental trusted-local G0.5 only",
        "status": status, "revision_before": before, "revision_after": after,
        "pytest": summary, "full_native_report": str(full_report.relative_to(ROOT)),
        "full_profile_ok": full_profile_ok, "checks": records,
        "caveat": "Pass is an evidence gate, not a security audit or merge approval.",
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"RESULT {status.upper()} | pytest: {summary} | report: {report}")
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
