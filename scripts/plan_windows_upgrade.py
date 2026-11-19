#!/usr/bin/env python3
"""Phase 6F: READ-ONLY Windows upgrade eligibility and recovery planning.

This tool NEVER installs, removes, overwrites, renames or executes program files.
It does not grant a right to upgrade: the v2 Inno Setup installer blocks all
existing destination folders, regardless of the result of this planner.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "build/windows-installer-stage"
DEFAULT_REPORT = ROOT / "build/windows-upgrade-plan.json"
IDENTITY = "org.kasalang.kasa.windows.preview.v1"
KNOWN_PAYLOAD = frozenset({
    "kasa-native.exe", "kasa.cmd", "README.txt",
    "manifest.json", "kasa-install-identity.txt",
})
# An Inno Setup installation adds these files, but this planner cannot
# independently establish their ownership or trustworthiness.
INNO_UNINSTALLER = frozenset({"unins000.exe", "unins000.dat", "unins000.msg"})
VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_version(value: object) -> tuple[int, int, int, int] | None:
    if not isinstance(value, str) or not VERSION_PATTERN.fullmatch(value):
        return None
    return tuple(int(part) for part in value.split("."))


def inspect_directory(directory: Path, *, installed: bool) -> dict:
    result = {"path": str(directory), "exists": directory.is_dir(),
              "valid": False, "issues": [], "manifest": None, "inventory": []}
    if directory.is_symlink():
        result["issues"].append("Directory is a symlink/reparse-like path; no ownership established")
        return result
    if not directory.is_dir():
        result["issues"].append("Package directory is missing")
        return result
    try:
        entries = list(directory.iterdir())
        result["inventory"] = sorted(item.name for item in entries)
        allowed = KNOWN_PAYLOAD | (INNO_UNINSTALLER if installed else frozenset())
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                result["issues"].append(f"Unrecognized link or directory: {entry.name}")
            elif entry.name not in allowed:
                result["issues"].append(f"Unknown file (must preserve): {entry.name}")
        for name in KNOWN_PAYLOAD:
            if name not in result["inventory"]:
                result["issues"].append(f"Missing expected file: {name}")
        identity = directory / "kasa-install-identity.txt"
        if identity.is_file() and not identity.is_symlink():
            if identity.read_text(encoding="ascii").strip() != IDENTITY:
                result["issues"].append("Installation identity marker mismatch")
        manifest_path = directory / "manifest.json"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            result["issues"].append("Missing or unsafe manifest")
            return result
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result["manifest"] = manifest
        if not isinstance(manifest, dict):
            result["issues"].append("Manifest must be an object")
            return result
        if (manifest.get("release") != "0.4.0-alpha" or
                manifest.get("platform") != "Windows" or
                manifest.get("architecture") != "x64"):
            result["issues"].append("Release/platform/architecture mismatch")
        native = directory / "kasa-native.exe"
        expected = manifest.get("binary_sha256")
        if not isinstance(expected, str) or not SHA_PATTERN.fullmatch(expected):
            result["issues"].append("Manifest binary_sha256 is missing or invalid")
        elif native.is_file() and not native.is_symlink():
            if sha256(native) != expected:
                result["issues"].append("Native executable hash mismatch")
        else:
            result["issues"].append("Native executable missing or unsafe")
        if parse_version(manifest.get("installer_build_version")) is None:
            result["issues"].append("No reviewed installer_build_version (0.4.0.N)")
        if installed:
            result["issues"].append(
                "Installed ownership/uninstall receipt not cryptographically attested")
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        result["issues"].append(f"Cannot safely inspect package: {type(exc).__name__}: {exc}")
    result["valid"] = not result["issues"]
    return result


def assess(installed: dict | None, candidate: dict) -> dict:
    reasons = []
    if not candidate["valid"]:
        reasons.append("Candidate package metadata/integrity not eligible")
    if installed is None:
        reasons.append("No installed version specified; cannot compare revisions")
    elif not installed["valid"]:
        reasons.append("Installed package ownership or integrity not established")
    if installed is not None and installed["manifest"] and candidate["manifest"]:
        current = parse_version(installed["manifest"].get("installer_build_version"))
        target = parse_version(candidate["manifest"].get("installer_build_version"))
        if current is None or target is None:
            reasons.append("Missing or invalid monotonic installer build version")
        elif current[:3] != target[:3] or target <= current:
            reasons.append("Candidate is not a strictly newer compatible installer build")
    # Deliberately hard-coded: no production installer-upgrade or rollback
    # procedure has been verified on Windows.
    reasons.append("Actual upgrade, recovery snapshot and rollback are NOT implemented or VM-verified")
    return {"safe_to_upgrade": False, "reasons": reasons,
            "policy": "BLOCKED: guarded-v2 installer forbids any existing destination"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--installed-dir", type=Path,
                        help="Optional exact installed Kasa directory; inspected without mutation")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    candidate = inspect_directory(args.candidate.absolute(), installed=False)
    current = (inspect_directory(args.installed_dir.absolute(), installed=True)
               if args.installed_dir is not None else None)
    assessment = assess(current, candidate)
    payload = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
               "mode": "READ_ONLY", "candidate": candidate, "installed": current,
               "upgrade": assessment,
               "does_not_do": ["execute an installer", "remove or replace files",
                               "edit registry or PATH", "create recovery backups"]}
    report = args.report.absolute()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("READ-ONLY Windows upgrade eligibility report:", report)
    print("Candidate eligible:", candidate["valid"])
    print("Safe to upgrade:", assessment["safe_to_upgrade"])
    for reason in assessment["reasons"]:
        print("BLOCKED:", reason)
    # Not-ready is intentional; exit 0 so this read-only inspection can be
    # scripted without treating an unimplemented upgrade as a successful run.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
