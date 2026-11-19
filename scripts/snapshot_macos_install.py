#!/usr/bin/env python3
"""Make a read-only Kasa preview recovery snapshot (never modifies installation).

A snapshot is NOT an automatic installer rollback. The package receipt must be
reconciled through macOS Installer; never restore a receipt by copying files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tarfile
import tempfile

from audit_macos_install import ROOT, PACKAGE_ID, EXPECTED_TARGET, audit, receipt_version
from plan_macos_uninstall import validate_removal

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for block in iter(lambda: reader.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def snapshot(root: Path, version: str, dest: Path) -> Path:
    """Check ownership and write a complete Kasa-only archive outside system paths."""
    validate_removal(root, version)
    if dest.exists():
        raise ValueError("Refusing to overwrite an existing recovery snapshot")
    dest.parent.mkdir(parents=True, exist_ok=True)
    names = ["bin/kasa", "lib/kasa-preview/kasa", "lib/kasa-preview/kasa-native",
             "lib/kasa-preview/build-info.txt"]
    info = {
        "format": "kasa-macos-preview-recovery-v1",
        "package_id": PACKAGE_ID,
        "installed_version": version,
        "symlink_target": EXPECTED_TARGET,
        "files": {name: digest(root / name) for name in names[1:]},
        "warning": "Backup only. Do not extract into /usr/local. Restore using a reviewed installer.",
    }
    # Atomic output avoids a half-written archive being mistaken for a valid one.
    with tempfile.NamedTemporaryFile(dir=dest.parent, suffix=".tmp", delete=False) as temporary:
        intermediate = Path(temporary.name)
    try:
        with tarfile.open(intermediate, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            for name in names:
                tar.add(root / name, arcname=name, recursive=False)
            data = (json.dumps(info, indent=2, sort_keys=True) + "\n").encode("utf-8")
            with tempfile.TemporaryDirectory(prefix="kasa-meta-", dir=dest.parent) as temp:
                file = Path(temp) / "recovery-manifest.json"
                file.write_bytes(data)
                tar.add(file, arcname="recovery-manifest.json")
        # Do not publish an incomplete or unexpected archive.
        with tarfile.open(intermediate, "r:gz") as check:
            if sorted(check.getnames()) != sorted(names + ["recovery-manifest.json"]):
                raise ValueError("Recovery archive contents differ from package-owned file list")
        os.replace(intermediate, dest)
    finally:
        if intermediate.exists():
            intermediate.unlink()
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Snapshot archive path outside /usr/local")
    args = parser.parse_args(argv)
    if platform.system() != "Darwin":
        print("Only real macOS installations can be snapshotted", file=sys.stderr)
        return 2
    output = (args.output if args.output is not None else
              Path(__file__).resolve().parents[1] / "build/recovery/kasa-installed-preview.tar.gz")
    output = output.expanduser().resolve()
    try:
        if output == ROOT or ROOT in output.parents:
            raise ValueError("Recovery archive must be outside /usr/local")
        version = receipt_version()
        written = snapshot(ROOT, version, output)
    except (OSError, ValueError) as error:
        print(f"Recovery snapshot refused: {error}", file=sys.stderr)
        return 1
    print("Saved a read-only recovery snapshot:", written)
    print("SHA256:", digest(written))
    print("Installed Kasa was not modified; this archive is NOT a one-command rollback.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
