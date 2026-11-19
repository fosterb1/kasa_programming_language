#!/usr/bin/env python3
"""Conservative macOS Kasa 0.4-preview uninstaller: plan only by default.

--execute is root-only, opt-in, limited to exact package-owned paths.
This is an alpha development tool, not a general-purpose package manager.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys

from audit_macos_install import PACKAGE_ID, ROOT, audit, receipt_version

OWNED = (
    "bin/kasa",
    "lib/kasa-preview/kasa",
    "lib/kasa-preview/kasa-native",
    "lib/kasa-preview/build-info.txt",
)
DIRECTORY = "lib/kasa-preview"
CONFIRM = "remove-kasa-preview-only"


def validate_removal(root: Path, installed_version: str) -> list[Path]:
    report = audit(root, installed_version)
    if not report["valid"]:
        raise ValueError("Installation ownership audit failed: " + "; ".join(report["issues"]))
    directory = root / DIRECTORY
    if {p.name for p in directory.iterdir()} != {
        "kasa", "kasa-native", "build-info.txt"
    }:
        raise ValueError("Unexpected files in Kasa installation; refusing to remove directory")
    if (root / "bin").is_symlink() or (root / "lib").is_symlink():
        raise ValueError("Parent installation directories are symlinks; refusing to proceed")
    return [root / item for item in OWNED]


def remove(root: Path, version: str, *, execute: bool) -> None:
    paths = validate_removal(root, version)
    if not execute:
        print("READ-ONLY REMOVAL PLAN (no files or receipts changed)")
        for path in paths:
            print("Would remove:", path)
        print("Would remove empty directory:", root / DIRECTORY)
        print("Would forget package receipt:", PACKAGE_ID)
        print("Your .kasa files outside /usr/local/lib/kasa-preview are not touched.")
        return
    raise ValueError("Actual removal is intentionally disabled until transactional uninstall is tested")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="Reserved; disabled until atomic removal is reviewed and tested")
    parser.add_argument("--confirm", default="", help="Required only with --execute")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin":
        print("macOS only", file=sys.stderr)
        return 2
    if args.execute:
        print("Safe removal is not yet released; --execute intentionally disabled.", file=sys.stderr)
        return 2
    try:
        remove(ROOT, receipt_version(), execute=False)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Refusing to create uninstall plan: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
