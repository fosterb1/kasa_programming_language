#!/usr/bin/env python3
"""Read-only audit of installed macOS Kasa preview before upgrades/removal.

This tool never modifies files, receipts, packages, or source projects.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

PACKAGE_ID = "org.kasalang.kasa.preview"
EXPECTED_TARGET = "../lib/kasa-preview/kasa"
ROOT = Path("/usr/local")
FILES = ("lib/kasa-preview/kasa-native", "lib/kasa-preview/kasa", "lib/kasa-preview/build-info.txt")
VERSION_RE = re.compile(r"0\.4\.0\.(\d+)\Z")


def receipt_version(*, runner=subprocess.run) -> str:
    proc = runner(["pkgutil", "--pkg-info", PACKAGE_ID], capture_output=True,
                  text=True, timeout=10, check=False)
    if proc.returncode:
        raise ValueError("Kasa preview package receipt not found")
    lines = [line.split(":", 1)[1].strip() for line in proc.stdout.splitlines()
             if line.startswith("version:")]
    if len(lines) != 1 or not VERSION_RE.fullmatch(lines[0]):
        raise ValueError("Unexpected Kasa preview receipt version")
    return lines[0]


def audit(root: Path, installed_version: str) -> dict:
    """Inspect paths without resolving symlinks or running installed executables."""
    issues: list[str] = []
    link = root / "bin/kasa"
    if not link.is_symlink():
        issues.append("Expected /usr/local/bin/kasa symlink is absent")
    elif os.readlink(link) != EXPECTED_TARGET:
        issues.append("Kasa command symlink points to an unexpected target")
    base = root / "lib/kasa-preview"
    if base.is_symlink() or not base.is_dir():
        issues.append("Kasa installation directory missing or replaced with symlink")
    for relative in FILES:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            issues.append(f"Missing or unexpected Kasa file: {relative}")
    info = base / "build-info.txt"
    installed = {}
    if info.is_file() and not info.is_symlink():
        for line in info.read_text(encoding="utf-8").splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                installed[key] = value
        if installed.get("Installer build version") != installed_version:
            issues.append("Installer build-info and package receipt versions disagree")
        if installed.get("Release") != "0.4.0-alpha":
            issues.append("Unexpected Kasa release label")
        if installed.get("Source commit") is None:
            issues.append("Missing source revision in build info")
    else:
        issues.append("Cannot inspect Kasa package build-info safely")
    return {"package_id": PACKAGE_ID, "installed_version": installed_version,
            "installed_source_commit": installed.get("Source commit"),
            "root": str(root), "valid": not issues, "issues": issues}


def assess_upgrade(installed: str, candidate: str) -> tuple[bool, str]:
    current = VERSION_RE.fullmatch(installed)
    proposed = VERSION_RE.fullmatch(candidate)
    if not current or not proposed:
        return False, "Only 0.4.0.N preview installer versions are supported"
    if int(proposed.group(1)) <= int(current.group(1)):
        return False, "Candidate version is not newer than the installed version"
    return True, "Candidate is a newer installer build; compatibility still requires testing"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-version", help="Optional candidate installer version, e.g. 0.4.0.200")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin":
        print("This audit requires a real macOS installation", file=sys.stderr)
        return 2
    try:
        installed = receipt_version()
        result = audit(ROOT, installed)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Install audit failed: {exc}", file=sys.stderr)
        return 1
    if args.candidate_version:
        allowed, message = assess_upgrade(installed, args.candidate_version)
        result["upgrade_candidate"] = args.candidate_version
        result["upgrade_permitted"] = allowed and result["valid"]
        result["upgrade_reason"] = message
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] and result.get("upgrade_permitted", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
