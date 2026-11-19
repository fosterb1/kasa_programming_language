#!/usr/bin/env python3
"""Phase 6F.5: read-only audit of an isolated Kasa reconstruction.

Never executes binaries or installers, copies or restores files, edits PATH,
registry or existing installation. Validates saved simulation report, verified
snapshot and reconstructed payload against the originally recorded hashes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SIMULATION_ROOT = (ROOT / "build" / "recovery-simulations").resolve()
LIB = Path(__file__).resolve().parent / "windows_recovery_snapshot.py"
spec = importlib.util.spec_from_file_location("kasa_audit_snapshot", LIB)
snapshot_lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot_lib)

class AuditError(ValueError):
    pass


def audit(workspace: Path) -> dict:
    """Return an evidence-based result: passed is true only for complete payloads."""
    workspace = workspace.absolute()
    report_file = workspace / "simulation-report.json"
    payload_dir = workspace / "reconstructed-payload"
    result = {"mode": "READ_ONLY_RECONSTRUCTION_AUDIT",
              "workspace": str(workspace),
              "passed": False,
              "installed_files_touched_by_audit": False,
              "files_verified": [],
              "issues": []}
    if workspace.is_symlink() or not workspace.is_dir():
        result["issues"].append("Workspace missing or is a symlink")
        return result
    if report_file.is_symlink() or not report_file.is_file():
        result["issues"].append("Simulation report missing or is a symlink")
        return result
    if payload_dir.is_symlink() or not payload_dir.is_dir():
        result["issues"].append("Reconstruction payload missing or is a symlink")
        return result
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            raise AuditError("Simulation report is not an object")
        if report.get("mode") != "SIMULATION_ONLY_NOT_INSTALLATION":
            raise AuditError("Unexpected simulation report mode")
        if report.get("restore_authorized") is not False:
            raise AuditError("Simulation report incorrectly authorizes restoration")
        if report.get("installed_files_touched") is not False:
            raise AuditError("Simulation report does not attest untouched installations")
        if Path(str(report.get("workspace", ""))).absolute() != workspace:
            raise AuditError("Simulation report workspace mismatch")
        if report.get("passed") is not True:
            raise AuditError("Simulation did not complete successfully")
        if set(report.get("files_written", [])) != snapshot_lib.FILES or (
            len(report.get("files_written", [])) != len(snapshot_lib.FILES)
        ):
            raise AuditError("Simulation files_written inventory incomplete or duplicated")
        source_snapshot = Path(str(report["snapshot"])).absolute()
        # The report only selects an existing backup. We verify it independently.
        backup = snapshot_lib.verify(source_snapshot)
        if report.get("snapshot_sha256") != backup["archive_sha256"]:
            raise AuditError("Snapshot SHA-256 no longer agrees with simulation report")
        contents, manifest = snapshot_lib.read_owned_payload(payload_dir)
        for name in sorted(contents):
            actual = snapshot_lib.digest(contents[name])
            if actual != backup["index"]["payload_sha256"][name]:
                raise AuditError("Reconstructed payload disagrees with snapshot: " + name)
            result["files_verified"].append(name)
        if manifest.get("release") != backup["index"]["language_release"]:
            raise AuditError("Language version mismatch")
        if manifest.get("installer_build_version") != backup["index"]["installer_build_version"]:
            raise AuditError("Installer build version mismatch")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        result["issues"].append(f"{type(exc).__name__}: {exc}")
        return result
    result["passed"] = True
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    workspace = args.workspace.absolute()
    resolved = workspace.resolve()
    if SIMULATION_ROOT not in resolved.parents or resolved == SIMULATION_ROOT:
        print("Audit refused: expected an isolated workspace under build/recovery-simulations",
              file=sys.stderr)
        return 2
    result = audit(workspace)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
