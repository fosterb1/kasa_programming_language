#!/usr/bin/env python3
"""Local macOS Kasa release-gate runner (no GitHub Actions required).

Runs both default Kasa and the opt-in KBC2 native VM on real macOS hosts.
--dry-run prints the command plan on any OS and never certifies the platform.
Results are reproducible, per-stage, and tied to an unchanged clean Git SHA.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BIGINT = ROOT / "build" / "kasa-macos-bigint"
PARITY = ROOT / "build" / "macos-parity.json"
FULL = ROOT / "build" / "macos-full.json"
CHECKS = (
    ("Default runtime parity", [sys.executable, "scripts/verify_local.py",
                                "--profile", "parity", "--report", str(PARITY)], 600),
    ("Default parity report audit", [sys.executable, "scripts/audit_parity_report.py",
                                     str(PARITY), "--expected-commit", "COMMIT"], 60),
    ("Default full verification", [sys.executable, "scripts/verify_local.py",
                                   "--profile", "full", "--report", str(FULL)], 900),
    ("Experimental KBC2 CMake configure",
     ["cmake", "-S", "native", "-B", str(BIGINT), "-DCMAKE_BUILD_TYPE=Release",
      "-DKASA_ENABLE_BIGINT_VM=ON"], 180),
    ("Experimental KBC2 native build",
     ["cmake", "--build", str(BIGINT), "--config", "Release",
      "--target", "kasa-native", "--parallel", "2"], 600),
    ("Experimental KBC2 integration, golden and loader robustness",
     ["ctest", "--test-dir", str(BIGINT), "-C", "Release",
      "-R", "kasa_(bigint_vm_rfc0008_source_and_kbc1|kbc2_cross_platform_golden|kbc2_loader_robustness)",
      "--output-on-failure"], 600),
)


def git_snapshot() -> dict[str, object]:
    if not shutil.which("git"):
        return {"commit": None, "clean": None}
    try:
        sha = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10, check=False)
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal"],
                                cwd=ROOT, capture_output=True, text=True,
                                timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return {"commit": None, "clean": None}
    return {"commit": sha.stdout.strip() if sha.returncode == 0 else None,
            "clean": status.stdout == "" if status.returncode == 0 else None}


def execute(label: str, argv: list[str], timeout: int) -> dict[str, object]:
    start = time.monotonic()
    record: dict[str, object] = {"name": label, "command": argv,
                                 "status": "failed", "exit_code": None}
    try:
        result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                                errors="replace", check=False, timeout=timeout)
        record["exit_code"] = result.returncode
        record["stdout_tail"] = result.stdout[-2500:]
        record["stderr_tail"] = result.stderr[-2500:]
        record["status"] = "passed" if result.returncode == 0 else "failed"
    except (OSError, subprocess.TimeoutExpired) as error:
        record["stderr_tail"] = str(error)
    record["duration_seconds"] = round(time.monotonic()-start, 3)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Show stage commands without executing or certifying anything")
    parser.add_argument("--report", type=Path, default=Path("build/macos-release-gate.json"))
    args = parser.parse_args()
    system = platform.system()
    arch = platform.machine()
    before = git_snapshot()
    commit = before.get("commit")
    plan = [(name, [commit if part == "COMMIT" else part for part in argv], timeout)
            for name, argv, timeout in CHECKS]
    if args.dry_run:
        print(f"DRY RUN ONLY; detected OS={system}, architecture={arch}")
        for name, argv, _ in plan:
            print(f"NOT RUN: {name}: {json.dumps(argv, ensure_ascii=False)}")
        return 0
    if system != "Darwin":
        print("FAIL: Native macOS certification must run on an actual macOS machine; "
              "use --dry-run elsewhere.", file=sys.stderr)
        return 2
    if arch not in ("arm64", "x86_64"):
        print(f"FAIL: Unsupported/unknown macOS architecture: {arch}", file=sys.stderr)
        return 2
    if before.get("clean") is not True or not isinstance(commit, str) or len(commit) != 40:
        print("FAIL: macOS release gate requires clean Git checkout with known SHA",
              file=sys.stderr)
        return 2
    if not all(shutil.which(tool) for tool in ("cmake", "node", "ctest", "git")):
        print("FAIL: Missing prerequisite: cmake, ctest, node or git", file=sys.stderr)
        return 2
    checks = []
    for name, argv, timeout in plan:
        check = execute(name, argv, timeout)
        checks.append(check)
        print(f"{str(check['status']).upper()} {name}", flush=True)
        if check["status"] != "passed":
            print(check.get("stderr_tail") or check.get("stdout_tail"), file=sys.stderr)
            break
    after = git_snapshot()
    all_pass = (len(checks) == len(plan) and
                all(check["status"] == "passed" for check in checks) and
                after == before and before["clean"] is True)
    report = {"schema_version": 1, "kind": "macos-release-gate",
              "created_utc": datetime.now(timezone.utc).isoformat(),
              "platform": {"os": system, "architecture": arch,
                           "python": platform.python_version()},
              "git_before": before, "git_after": after,
              "tests": checks, "expected_stages": len(plan),
              "passed": sum(check["status"] == "passed" for check in checks),
              "result": "passed" if all_pass else "failed",
              "notes": "Local verification is not independent attestation, signing, sandboxing, or distribution approval."}
    output = args.report if args.report.is_absolute() else ROOT / args.report
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"REPORT {output}")
    print(f"FINAL {report['result'].upper()}: {report['passed']}/{len(plan)} checks "
          f"on macOS {arch} at {commit}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
