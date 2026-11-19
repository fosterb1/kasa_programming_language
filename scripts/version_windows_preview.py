#!/usr/bin/env python3
"""Create a NEW versioned Windows developer ZIP from a verified legacy portable ZIP.

Never modifies the original ZIP, installer, staged files, PATH or registry.
No installation and no upgrade authorization; the output is still unsigned.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip"
OUTPUT = ROOT / "build/dist"
PAYLOAD = frozenset({"kasa-native.exe", "kasa.cmd", "README.txt", "manifest.json"})
IDENTITY = "org.kasalang.kasa.windows.preview.v1"
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
MAX_PAYLOAD = 100 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_version(build: int) -> str:
    if type(build) is not int or not 1 <= build <= 65535:
        raise ValueError("Build number must be an integer from 1 to 65535")
    return f"0.4.0.{build}"


def read_verified_archive(source: Path) -> tuple[dict[str, bytes], dict]:
    checksum = source.with_name(source.name + ".sha256")
    if not source.is_file() or source.is_symlink() or not checksum.is_file() or checksum.is_symlink():
        raise ValueError("Verified source ZIP and sidecar SHA-256 must be regular files")
    fields = checksum.read_text(encoding="ascii").strip().split()
    if len(fields) != 2 or fields[1] != source.name or not DIGEST.fullmatch(fields[0].lower()):
        raise ValueError("Invalid ZIP sidecar checksum")
    if sha256(source.read_bytes()) != fields[0].lower():
        raise ValueError("Source ZIP SHA-256 does not match sidecar")
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
        expected = {f"{source.stem}/{name}" for name in PAYLOAD}
        members = archive.namelist()
        if len(members) != len(expected) or set(members) != expected:
            raise ValueError("Legacy ZIP has unknown, duplicate or missing entries")
        if any(info.file_size > MAX_PAYLOAD for info in archive.infolist()):
            raise ValueError("Oversized package member")
        files = {name: archive.read(f"{source.stem}/{name}") for name in PAYLOAD}
    manifest = json.loads(files["manifest.json"])
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be an object")
    if any(manifest.get(key) != val for key, val in (
        ("release", "0.4.0-alpha"), ("platform", "Windows"), ("architecture", "x64"),
        ("channel", "development-preview"), ("signature", "UNSIGNED"),
        ("installer", False),
    )):
        raise ValueError("Unexpected legacy manifest identity or release")
    if not COMMIT.fullmatch(str(manifest.get("source_commit", ""))):
        raise ValueError("Missing verifiable 40-character source commit")
    if manifest.get("binary_sha256") != sha256(files["kasa-native.exe"]):
        raise ValueError("Legacy binary SHA-256 mismatch")
    return files, manifest


def package(source: Path, output: Path, build: int) -> Path:
    version = build_version(build)
    # Reading and verification happen before creating output files.
    files, manifest = read_verified_archive(source)
    name = f"kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev-build-{build}"
    dest = output / f"{name}.zip"
    sidecar = output / (dest.name + ".sha256")
    receipt = output / f"{name}.receipt.json"
    if any(p.exists() or p.is_symlink() for p in (dest, sidecar, receipt)):
        raise ValueError("One or more versioned output files already exist; refusing overwrite")
    manifest = dict(manifest)
    manifest["installer_build_version"] = version
    manifest["package_kind"] = "versioned-portable-developer-preview"
    manifest["upgrade_supported"] = False
    manifest["installation_receipt_status"] = "NOT_INSTALLED"
    files = dict(files)
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    files["kasa-install-identity.txt"] = (IDENTITY + "\n").encode("ascii")
    files_hashes = {key: sha256(value) for key, value in sorted(files.items())}
    output.mkdir(parents=True, exist_ok=True)
    # Only output artifacts are written. Never touch source ZIP or working stage.
    try:
        with zipfile.ZipFile(dest, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for key, payload in sorted(files.items()):
                archive.writestr(f"{name}/{key}", payload)
        with zipfile.ZipFile(dest) as archive:
            if (archive.testzip() is not None or
                    len(archive.namelist()) != len(files) or
                    set(archive.namelist()) != {f"{name}/{key}" for key in files}):
                raise ValueError("Versioned ZIP verification failed")
        archive_sha = sha256(dest.read_bytes())
        # Local BUILD receipt, not an installation receipt or cryptographic signature.
        record = {
            "schema_version": 1, "receipt_kind": "BUILD_ONLY_NOT_INSTALLED",
            "installer_build_version": version, "release": "0.4.0-alpha",
            "platform": "Windows", "architecture": "x64",
            "source_commit": manifest["source_commit"],
            "source_zip": source.name,
            "source_zip_sha256": sha256(source.read_bytes()),
            "archive_filename": dest.name, "archive_sha256": archive_sha,
            "files_sha256": files_hashes, "signed": False,
            "upgrades_allowed": False,
        }
        with receipt.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
        with sidecar.open("x", encoding="ascii") as stream:
            stream.write(f"{archive_sha}  {dest.name}\n")
    except Exception:
        # Do not remove or overwrite pre-existing outputs. Cleanup only the
        # artifacts this invocation created after preflight confirmed absence.
        for path in (sidecar, receipt, dest):
            if path.is_file():
                path.unlink()
        raise
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=int, required=True,
                        help="Explicit monotonically assigned build number, 1..65535")
    parser.add_argument("--source", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    try:
        dest = package(args.source.absolute(), args.output.absolute(), args.build)
    except (ValueError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"Versioned Windows packaging refused: {error}", file=sys.stderr)
        return 1
    print("Created new unsigned versioned developer ZIP:", dest)
    print("Build-only receipt:", dest.with_suffix(".receipt.json"))
    print("NOT installed or upgrade-enabled. The original artifacts were preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
