#!/usr/bin/env python3
"""Verify Kasa native and browser Studio locally, without CI or Netlify.

Prerequisites: Python dev dependencies; for browser profile: Playwright with
Chromium, Emscripten (em++), and Node. No dependency installation or deployment
is performed by this command.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def plan(profile: str) -> list[tuple[str, list[str]]]:
    python = sys.executable
    native = [("native_full", [python, "scripts/verify_local.py", "--profile", "full",
                                "--report", "build/offline-native-evidence.json"])]
    browser = [
        ("wasm_build", ["bash", "native/wasm/build.sh"]),
        ("wasm_package", [python, "playground/build_site.py", "--require-wasm"]),
        ("browser_playground", [python, "scripts/verify_browser_playground.py"]),
        ("browser_modules", [python, "scripts/verify_real_module_browser.py"]),
        ("browser_wasm", [python, "scripts/verify_real_wasm_browser.py"]),
    ]
    return (native if profile == "native" else
            browser if profile == "browser" else native + browser)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("native", "browser", "all"), default="all")
    parser.add_argument("--dry-run", action="store_true", help="show commands, execute nothing")
    parser.add_argument("--report", default="build/offline-studio-verification.json")
    args = parser.parse_args(argv)
    report = Path(args.report)
    if not report.is_absolute():
        report = ROOT / report
    checks = []
    for name, command in plan(args.profile):
        if args.dry_run:
            status, code = "not_run", None
        elif not shutil.which(command[0]):
            status, code = "failed", None
            print(f"Missing executable: {command[0]}", file=sys.stderr, flush=True)
        else:
            code = subprocess.run(command, cwd=ROOT, check=False).returncode
            status = "passed" if code == 0 else "failed"
        checks.append({"name": name, "command": command,
                       "status": status, "exit_code": code})
        print(f"{status.upper():8} {name}", flush=True)
        if status == "failed":
            break
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "dry_run": args.dry_run,
        "checks": checks,
        "passed": sum(c["status"] == "passed" for c in checks),
        "failed": sum(c["status"] == "failed" for c in checks),
        "not_run": sum(c["status"] == "not_run" for c in checks),
        "caveat": "Passing does not certify production security or deployed Netlify behavior.",
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {report}", flush=True)
    if args.dry_run:
        print("DRY RUN: no verification performed", flush=True)
        return 0
    return 0 if len(checks) == len(plan(args.profile)) and payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
