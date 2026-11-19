#!/usr/bin/env python3
"""Read-only public-alpha release gate. A status report, never a publisher."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "LICENSE",
    "docs/RELEASE_NOTES_0_4.md",
    "docs/LANGUAGE_COMPATIBILITY_POLICY.md",
)
EXTERNAL = (
    "macos_intel_installer_signed_notarized",
    "macos_apple_silicon_verified",
    "windows_installer_verified",
    "linux_package_verified",
    "browser_release_on_production_verified",
    "independent_security_review_completed",
    "twi_educator_review_completed",
)

def gate(root: Path = ROOT) -> dict:
    checks: list[dict] = []
    for relative in REQUIRED:
        p = root / relative
        checks.append({"name": relative, "passed": p.is_file() and p.stat().st_size > 0,
                       "reason": "Local required release artifact"})
    # External evidence must be separately recorded and approved. An unchecked
    # JSON boolean or locally generated status file cannot certify those checks.
    for name in EXTERNAL:
        checks.append({"name": name, "passed": False,
                       "reason": "Requires independently reviewed external evidence"})
    return {"schema_version": 1, "purpose": "public-alpha-readiness",
            "source": "local read-only audit", "ready": all(item["passed"] for item in checks),
            "checks": checks, "note": "This script cannot authorize distribution or perform publishing"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "build/public-alpha-gate.json")
    args = parser.parse_args()
    report = gate()
    dest = args.report.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Public alpha release ready: {report['ready']}")
    print(f"Gates: {sum(c['passed'] for c in report['checks'])}/{len(report['checks'])} satisfied")
    for item in report["checks"]:
        print(("PASS " if item["passed"] else "BLOCK"), item["name"])
    print("Report:", dest)
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
