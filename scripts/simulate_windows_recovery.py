#!/usr/bin/env python3
"""Phase 6F.4: simulate Kasa payload recovery to a NEW isolated directory.

Never restore to an installed location, run executables, edit PATH/registry,
overwrite files, or delete a failed simulation. Treat snapshot as untrusted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_CLI_ROOT = (ROOT / "build" / "recovery-simulations").resolve()
SOURCE = Path(__file__).resolve().parent / "windows_recovery_snapshot.py"
spec = importlib.util.spec_from_file_location("kasa_snapshot_lib", SOURCE)
snapshot_lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot_lib)

class SimulationError(ValueError):
    pass

def simulate(archive_path: Path, workspace: Path, *, fail_after: int | None = None) -> dict:
    """The caller supplies a fresh isolated directory. Never replace its contents.

    Fault injection is a deliberate failure after N files. Partial files and
    report are retained to diagnose interrupted simulations.
    """
    if fail_after is not None and (type(fail_after) is not int or not 1 <= fail_after <= len(snapshot_lib.FILES)):
        raise SimulationError("fail_after must be 1 through 5")
    archive_path = archive_path.absolute()
    workspace = workspace.absolute()
    # Validate entire ZIP + sidecar *before* allocating destination.
    checked = snapshot_lib.verify(archive_path)
    if workspace == archive_path.parent or workspace == archive_path or (
        archive_path in workspace.parents
    ):
        raise SimulationError("Workspace overlaps snapshot archive location")
    if workspace.exists() or workspace.is_symlink():
        raise SimulationError("Simulation workspace already exists; refusing overwrite")
    workspace.parent.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(exist_ok=False)
    payload_dir = workspace / "reconstructed-payload"
    payload_dir.mkdir(exist_ok=False)
    results = {
        "mode": "SIMULATION_ONLY_NOT_INSTALLATION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": str(archive_path),
        "snapshot_sha256": checked["archive_sha256"],
        "workspace": str(workspace),
        "restore_authorized": False,
        "installed_files_touched": False,
        "passed": False,
        "files_written": [],
    }
    report_path = workspace / "simulation-report.json"
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for index, filename in enumerate(sorted(snapshot_lib.FILES), start=1):
                # ZIP entries are exact allowlisted names verified above.
                data = archive.read(snapshot_lib.PREFIX + filename)
                expected = checked["index"]["payload_sha256"][filename]
                if snapshot_lib.digest(data) != expected:
                    raise SimulationError("Snapshot changed during simulation")
                destination = payload_dir / filename
                with destination.open("xb") as target:
                    target.write(data)
                if snapshot_lib.digest(destination.read_bytes()) != expected:
                    raise SimulationError("Reconstructed file checksum mismatch: " + filename)
                results["files_written"].append(filename)
                if fail_after == index:
                    raise SimulationError("Injected interruption after file " + str(index))
        reconstructed, _ = snapshot_lib.read_owned_payload(payload_dir)
        for filename, data in reconstructed.items():
            if snapshot_lib.digest(data) != checked["index"]["payload_sha256"][filename]:
                raise SimulationError("Post-simulation file hash mismatch: " + filename)
        # Recheck the input, including the sidecar, after output is reconstructed.
        if snapshot_lib.verify(archive_path)["archive_sha256"] != checked["archive_sha256"]:
            raise SimulationError("Snapshot changed after simulation")
        results["passed"] = True
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        results["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        # Keep evidence on failure. This report isn't an installation receipt.
        report_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--inject-failure-after", type=int, default=None,
                        help="Optional 1..5; simulate interruption without deleting partial output")
    args = parser.parse_args(argv)
    workspace = args.workspace.absolute()
    try:
        # CLI is deliberately limited to the repository's isolated simulation
        # tree, not an arbitrary installed or user project directory.
        resolved = workspace.resolve()
        if ALLOWED_CLI_ROOT not in resolved.parents or resolved == ALLOWED_CLI_ROOT:
            raise SimulationError("CLI workspace must be a fresh child of build/recovery-simulations")
        result = simulate(args.snapshot, workspace, fail_after=args.inject_failure_after)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print("Recovery simulation refused:", exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
