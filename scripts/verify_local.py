#!/usr/bin/env python3
"""Run Kasa language checks without GitHub Actions.

Quick: Python and browser-JavaScript tests. Full: quick plus native C++ VM.
An optional WASM build is source/build verification, not a real browser check.
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


def run_check(label: str, command: list[str], *, env: dict[str, str],
              timeout: int = 180, dry_run: bool = False) -> dict:
    """Run one argv command; never use a shell or swallow exit failures."""
    record = {"name": label, "command": command, "status": "not_run" if dry_run else "failed",
              "exit_code": None, "duration_seconds": 0.0, "stdout_tail": "", "stderr_tail": ""}
    if dry_run:
        return record
    if not shutil.which(command[0]):
        record["stderr_tail"] = f"Executable not found: {command[0]}"
        return record
    start = time.monotonic()
    try:
        outcome = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                 text=True, errors="replace", timeout=timeout, check=False)
        record["exit_code"] = outcome.returncode
        record["stdout_tail"] = outcome.stdout[-5000:]
        record["stderr_tail"] = outcome.stderr[-5000:]
        record["status"] = "passed" if outcome.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as error:
        record["stderr_tail"] = f"Timed out after {timeout}s: {error}"
    except OSError as error:
        record["stderr_tail"] = f"Execution error: {error}"
    finally:
        record["duration_seconds"] = round(time.monotonic() - start, 3)
    return record


def plan(profile: str, wasm: bool) -> list[tuple[str, list[str], int]]:
    """Ordered test commands; returned even in --dry-run mode."""
    python = sys.executable
    node = "node"
    build = Path("build") / "kasa-local"
    exe = build / ("Release/kasa-native.exe" if os.name == "nt" else "kasa-native")
    tests = [
        ("Python pytest", [python, "-m", "pytest", "-q"], 180),
        ("Python CLI run", [python, "-m", "kasa", "run", "examples/hello.kasa"], 30),
        ("Python CLI check", [python, "-m", "kasa", "check", "examples/hello.kasa"], 30),
        ("JavaScript runtime syntax", [node, "--check", "playground/kasa-runtime.js"], 30),
        ("JavaScript worker syntax", [node, "--check", "playground/worker.js"], 30),
        ("JavaScript playground UI syntax", [node, "--check", "playground/app.js"], 30),
        ("JavaScript browser/WASM protocol tests", [node, "--test", "tests/test_kasa_browser.cjs", "tests/test_kasa_wasm.cjs"], 120),
    ]
    if profile == "full":
        tests.extend([
            ("Native CMake configure", ["cmake", "-S", "native", "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"], 120),
            ("Native C++ build", ["cmake", "--build", str(build), "--config", "Release", "--parallel", "2"], 180),
            ("Native Python conformance", [python, "native/tests/conformance.py", str(exe)], 180),
        ])
        if wasm:
            tests.extend([
                ("WASM Emscripten build", ["bash", "native/wasm/build.sh"], 300),
                ("WASM site bundle", [python, "playground/build_site.py", "--require-wasm"], 120),
            ])
    return tests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("quick", "full"), default="quick",
                        help="quick=Python+Node; full=also compile/test C++")
    parser.add_argument("--wasm", action="store_true", help="attempt Emscripten build (full profile only)")
    parser.add_argument("--dry-run", action="store_true", help="show commands without executing any tests")
    parser.add_argument("--report", default="build/kasa-local-verification.json",
                        help="write JSON report here, relative to repository root")
    args = parser.parse_args(argv)
    if args.wasm and args.profile != "full":
        parser.error("--wasm requires --profile full")
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = ROOT / report_path

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "src"), env.get("PYTHONPATH", "")]))
    checks = []
    planned_checks = plan(args.profile, args.wasm)
    for index, (name, command, timeout) in enumerate(planned_checks):
        check = run_check(name, command, env=env, timeout=timeout, dry_run=args.dry_run)
        checks.append(check)
        print(f"{check['status'].upper():8} {name}", flush=True)
        if check["status"] == "failed":
            print(check["stderr_tail"] or check["stdout_tail"], file=sys.stderr, flush=True)
            # A failure in configuration/build invalidates later dependent native jobs.
            if name in {"Native CMake configure", "Native C++ build", "WASM Emscripten build"}:
                # Do not imply dependent steps passed or simply omit them.
                for blocked_name, blocked_command, _ in planned_checks[index + 1:]:
                    checks.append({
                        "name": blocked_name, "command": blocked_command,
                        "status": "not_run", "exit_code": None,
                        "duration_seconds": 0.0, "stdout_tail": "",
                        "stderr_tail": f"Blocked after failed step: {name}",
                    })
                    print(f"NOT_RUN  {blocked_name}", flush=True)
                break

    counts = {status: sum(x["status"] == status for x in checks)
              for status in ("passed", "failed", "not_run")}
    payload = {
        "schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(), "python": sys.version.split()[0],
        "profile": args.profile, "wasm_requested": args.wasm,
        "dry_run": args.dry_run, "counts": counts, "checks": checks,
        "caveat": "A WASM build is not an end-to-end real-browser runtime test.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Report: {report_path}")
    print(f"Passed: {counts['passed']} | Failed: {counts['failed']} | Not run: {counts['not_run']}")
    if args.dry_run:
        print("DRY RUN ONLY: no tests were executed; this is NOT a pass result.")
        return 0
    return 0 if counts["failed"] == 0 and counts["not_run"] == 0 and len(checks) == len(planned_checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
