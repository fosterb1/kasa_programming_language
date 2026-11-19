#!/usr/bin/env python3
"""Fail-closed audit of Kasa parity JSON reports (stdlib only).

Auditing a report is NOT independent execution of the recorded Kasa tests.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

STAGES = (
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
)
SHA = re.compile(r"[0-9a-fA-F]{40}\Z")


def expected_commands() -> list[list[str]]:
    """Rebuild canonical commands from this checkout, not from the report."""
    source = Path(__file__).with_name("verify_local.py")
    spec = importlib.util.spec_from_file_location("kasa_verify_local_for_audit", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load local verification plan")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [command for _, command, _ in module.plan("parity", False)]


def command_matches(actual: object, expected: list[str]) -> bool:
    if not isinstance(actual, list) or not actual:
        return False
    if not all(isinstance(part, str) and part for part in actual):
        return False
    if actual == expected:
        return True
    # Python paths may differ between local virtual environments, but the
    # complete argument vector and script paths must remain unchanged.
    is_python = Path(actual[0]).name.lower().startswith(("python", "pypy"))
    return is_python and expected[1:] == actual[1:] and (
        expected[1:3] in (["-m", "pytest"], ["-m", "kasa"]) or
        (len(expected) > 1 and expected[1].startswith("native/tests/"))
    )


def audit(report: object, *, require_clean: bool = True, expected_commit: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["Report must be a JSON object"]
    if report.get("schema_version") != 1:
        errors.append("Expected schema_version=1")
    if report.get("profile") != "parity":
        errors.append("Expected parity profile")
    if report.get("dry_run") is not False:
        errors.append("Dry run or missing dry_run=false")
    if report.get("wasm_requested") is not False:
        errors.append("Unexpected wasm_requested for parity profile")
    revision = report.get("source_revision")
    if not isinstance(revision, dict) or not isinstance(revision.get("commit"), str) or not SHA.fullmatch(revision["commit"]):
        errors.append("Missing valid 40-character source commit SHA")
    if require_clean and (not isinstance(revision, dict) or revision.get("working_tree_clean") is not True):
        errors.append("Dirty checkout or unknown cleanliness")
    after = report.get("source_revision_after")
    if not isinstance(after, dict) or after != revision:
        errors.append("Source revision changed during verification or final revision missing")
    if expected_commit is not None and (
        not SHA.fullmatch(expected_commit)
        or not isinstance(revision, dict)
        or revision.get("commit", "").lower() != expected_commit.lower()
    ):
        errors.append("Report source commit does not match requested commit")
    checks = report.get("checks")
    if not isinstance(checks, list):
        return errors + ["Missing checks array"]
    names = [item.get("name") if isinstance(item, dict) else None for item in checks]
    if names != list(STAGES):
        errors.append(f"Expected exactly {len(STAGES)} parity stages in canonical order")
    planned = expected_commands()
    if len(planned) != len(STAGES):
        errors.append("Local parity command plan differs from audited stage count")
    for index, item in enumerate(checks):
        if not isinstance(item, dict):
            errors.append(f"Stage {index + 1} is not an object")
            continue
        if item.get("status") != "passed" or type(item.get("exit_code")) is not int or item["exit_code"] != 0:
            errors.append(f"Stage {index + 1} ({item.get('name', '?')}) was not successful")
        command = item.get("command")
        if index >= len(planned) or not command_matches(command, planned[index]):
            errors.append(f"Stage {index + 1} does not match its required parity command")
    counts = report.get("counts")
    if not isinstance(counts, dict) or any(type(counts.get(k)) is not int for k in ("passed", "failed", "not_run")):
        errors.append("Invalid status counts")
    else:
        actual = {k: sum(isinstance(c, dict) and c.get("status") == k for c in checks)
                  for k in ("passed", "failed", "not_run")}
        if counts != actual or counts != {"passed": len(STAGES), "failed": 0, "not_run": 0}:
            errors.append("Status counts inconsistent or incomplete")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JSON generated by verify_local.py --profile parity")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Developer diagnosis only, not clean-release evidence")
    parser.add_argument("--expected-commit",
                        help="Require an exact 40-character git commit (recommended for release auditing)")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: cannot read report: {exc}", file=sys.stderr)
        return 2
    problems = audit(data, require_clean=not args.allow_dirty, expected_commit=args.expected_commit)
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"PASS: report records {len(STAGES)} successful parity stages at a known source revision")
    print("CAUTION: report auditing does not independently execute or attest those tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
