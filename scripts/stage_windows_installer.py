#!/usr/bin/env python3
"""Stage a verified Windows portable ZIP for optional Inno Setup compilation.

No installs, registry edits, privilege changes, PATH changes, or setup execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip"
STAGE = ROOT / "build/windows-installer-stage"
NAME = ARCHIVE.stem
REQUIRED = ("kasa-native.exe", "kasa.cmd", "manifest.json", "README.txt")
IDENTITY = "org.kasalang.kasa.windows.preview.v1\n"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def stage(archive: Path, dest: Path) -> Path:
    if dest.exists():
        raise ValueError("Existing staging directory will not be overwritten")
    checksum = archive.with_name(archive.name + ".sha256")
    if not archive.is_file() or not checksum.is_file():
        raise ValueError("Missing Windows preview archive or checksum")
    expected = checksum.read_text(encoding="ascii").split()
    if len(expected) != 2 or expected[1] != archive.name:
        raise ValueError("Malformed checksum or mismatched archive name")
    if sha256(archive.read_bytes()).lower() != expected[0].lower():
        raise ValueError("Archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP CRC verification failed")
        entries = set(z.namelist())
        names = {f"{archive.stem}/{item}" for item in REQUIRED}
        if entries != names:
            raise ValueError("ZIP contains unexpected or missing entries")
        info = json.loads(z.read(f"{archive.stem}/manifest.json"))
        if info.get("release") != "0.4.0-alpha" or info.get("platform") != "Windows" or info.get("architecture") != "x64":
            raise ValueError("Wrong release or architecture in package manifest")
        if info.get("binary_sha256") != sha256(z.read(f"{archive.stem}/kasa-native.exe")):
            raise ValueError("Native executable digest mismatch")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="kasa-win-stage-", dir=dest.parent) as folder:
            root = Path(folder) / "stage"
            root.mkdir()
            for item in REQUIRED:
                (root / item).write_bytes(z.read(f"{archive.stem}/{item}"))
            (root / "kasa-install-identity.txt").write_text(IDENTITY, encoding="ascii")
            root.rename(dest)
    return dest

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--output", type=Path, default=STAGE)
    args = parser.parse_args()
    if platform.system() != "Windows":
        print("Installer staging is restricted to Windows", file=sys.stderr)
        return 2
    try:
        out = stage(args.archive.resolve(), args.output.resolve())
    except (ValueError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"Installer staging refused: {exc}", file=sys.stderr)
        return 1
    print("Staged verified installer payload:", out)
    print("Stage only: no installer was compiled, installed or executed.")
    print("Optional compiler: Inno Setup 6 ISCC.exe scripts\\kasa_windows_preview.iss")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
