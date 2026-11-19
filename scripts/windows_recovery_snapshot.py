#!/usr/bin/env python3
"""Phase 6F.3: make/verify a Kasa-owned Windows recovery snapshot, never restore.

Snapshots only the five known preview payload files, refuses links, unknown
entries and unsafe metadata. No installer execution, elevation or modifications
to the source directory. An archive is not proof of installation ownership.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = frozenset({"kasa-native.exe", "kasa.cmd", "manifest.json",
                   "README.txt", "kasa-install-identity.txt"})
IDENTITY = "org.kasalang.kasa.windows.preview.v1"
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
MAX_FILE = 64 * 1024 * 1024
MAX_ARCHIVE = 80 * 1024 * 1024
INDEX = "snapshot-index.json"
PREFIX = "kasa-payload/"


class SnapshotError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_identity_marker(data: bytes) -> bool:
    """Accept only the canonical marker plus LF or CRLF; preserve raw bytes.

    Windows text-mode writes use CRLF. An arbitrary strip() would wrongly accept
    trailing spaces or additional lines, weakening the identity check.
    """
    marker = IDENTITY.encode("ascii")
    return data in (marker + b"\n", marker + b"\r\n")


def check_manifest(data: bytes, binary: bytes) -> dict:
    try:
        meta = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise SnapshotError("Invalid package manifest JSON") from exc
    if not isinstance(meta, dict):
        raise SnapshotError("Manifest must be an object")
    for key, value in {"release": "0.4.0-alpha", "platform": "Windows",
                       "architecture": "x64"}.items():
        if meta.get(key) != value:
            raise SnapshotError(f"Manifest {key} mismatch")
    if meta.get("binary_sha256") != digest(binary):
        raise SnapshotError("Native executable SHA-256 mismatch")
    source_commit = meta.get("source_commit")
    if source_commit is not None and not COMMIT.fullmatch(str(source_commit)):
        raise SnapshotError("Invalid source commit format")
    return meta


def read_owned_payload(source: Path) -> tuple[dict[str, bytes], dict]:
    if source.is_symlink() or not source.is_dir():
        raise SnapshotError("Source must be a real existing directory")
    try:
        entries = list(source.iterdir())
        if {p.name for p in entries} != FILES:
            raise SnapshotError("Unexpected or missing source entries: stop, preserve all user files")
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                raise SnapshotError(f"Unsafe source entry: {entry.name}")
            if entry.stat().st_size > MAX_FILE:
                raise SnapshotError(f"Oversized source entry: {entry.name}")
        contents = {name: (source / name).read_bytes() for name in FILES}
    except OSError as exc:
        raise SnapshotError("Source unreadable; no backup created") from exc
    if sum(map(len, contents.values())) > MAX_ARCHIVE:
        raise SnapshotError("Source payload exceeds snapshot size limit")
    if not valid_identity_marker(contents["kasa-install-identity.txt"]):
        raise SnapshotError("Identity marker mismatch")
    manifest = check_manifest(contents["manifest.json"], contents["kasa-native.exe"])
    return contents, manifest


def snapshot(source: Path, output: Path) -> dict:
    # Unlike an installation receipt, the snapshot records only a candidate
    # payload and is *never* authorized for automatic restoration.
    contents, manifest = read_owned_payload(source)
    output = output.absolute()
    if output.suffix.lower() != ".zip":
        raise SnapshotError("Snapshot output must end in .zip")
    checksum = output.with_name(output.name + ".sha256")
    if any(p.exists() or p.is_symlink() for p in (output, checksum)):
        raise SnapshotError("Snapshot archive or checksum already exists; refusing overwrite")
    if source.resolve() == output.parent.resolve():
        raise SnapshotError("Snapshot must be stored outside the source directory")
    hashes = {name: digest(contents[name]) for name in sorted(contents)}
    index = {
        "schema_version": 1, "kind": "KASA_WINDOWS_PAYLOAD_SNAPSHOT_NO_RESTORE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_directory": str(source.absolute()),
        "source_commit": manifest.get("source_commit"),
        "language_release": "0.4.0-alpha",
        "installer_build_version": manifest.get("installer_build_version"),
        "payload_sha256": hashes, "restore_authorized": False,
        "installation_ownership_verified": False, "signed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # 'x' refuses overwrite even when another process creates an archive.
    created = False
    try:
        with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
            created = True
            archive.writestr(INDEX, json.dumps(index, indent=2, sort_keys=True) + "\n")
            for name in sorted(contents):
                archive.writestr(PREFIX + name, contents[name])
        verified = verify(output, require_sidecar=False)
        if verified["index"]["payload_sha256"] != hashes:
            raise SnapshotError("Post-write archive verification failed")
        with checksum.open("x", encoding="ascii") as stream:
            stream.write(f"{verified['archive_sha256']}  {output.name}\n")
    except Exception:
        if created and output.is_file():
            output.unlink()
        # Never delete an unrelated preexisting checksum.
        raise
    return {"archive": str(output), "checksum": str(checksum), **verified}


def verify(archive_path: Path, *, require_sidecar: bool = True) -> dict:
    path = archive_path.absolute()
    if path.is_symlink() or not path.is_file():
        raise SnapshotError("Snapshot archive missing or unsafe")
    if path.stat().st_size > MAX_ARCHIVE:
        raise SnapshotError("Snapshot archive exceeds size limit")
    archive_hash = digest(path.read_bytes())
    if require_sidecar:
        sidecar = path.with_name(path.name + ".sha256")
        if sidecar.is_symlink() or not sidecar.is_file():
            raise SnapshotError("Missing/unsafe snapshot checksum")
        fields = sidecar.read_text(encoding="ascii").strip().split()
        if len(fields) != 2 or fields[1] != path.name or fields[0].lower() != archive_hash:
            raise SnapshotError("Snapshot checksum mismatch")
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            expected = {INDEX} | {PREFIX + name for name in FILES}
            if len(names) != len(expected) or set(names) != expected:
                raise SnapshotError("Unexpected, duplicate or missing snapshot member")
            if any(info.file_size > MAX_FILE for info in archive.infolist()):
                raise SnapshotError("Oversized snapshot member")
            if archive.testzip() is not None:
                raise SnapshotError("ZIP CRC mismatch")
            index = json.loads(archive.read(INDEX))
            if not isinstance(index, dict) or index.get("schema_version") != 1 or (
                index.get("kind") != "KASA_WINDOWS_PAYLOAD_SNAPSHOT_NO_RESTORE"
            ) or index.get("restore_authorized") is not False or (
                index.get("installation_ownership_verified") is not False
            ) or index.get("signed") is not False:
                raise SnapshotError("Invalid snapshot index or unsafe authorization markers")
            hashes = index.get("payload_sha256")
            if not isinstance(hashes, dict) or set(hashes) != FILES:
                raise SnapshotError("Invalid snapshot file inventory")
            payload = {}
            for name in FILES:
                recorded = hashes[name]
                if not isinstance(recorded, str) or not SHA.fullmatch(recorded):
                    raise SnapshotError("Invalid recorded file digest")
                payload[name] = archive.read(PREFIX + name)
                if digest(payload[name]) != recorded:
                    raise SnapshotError(f"Snapshot payload tampered: {name}")
            if not valid_identity_marker(payload["kasa-install-identity.txt"]):
                raise SnapshotError("Snapshot identity marker mismatch")
            check_manifest(payload["manifest.json"], payload["kasa-native.exe"])
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, OSError) as exc:
        raise SnapshotError("Corrupt or unreadable snapshot archive") from exc
    return {"verified": True, "archive_sha256": archive_hash, "index": index,
            "note": "READ ONLY verification: no restore or upgrade performed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--create-from", type=Path, metavar="PAYLOAD_DIRECTORY")
    mode.add_argument("--verify", type=Path, metavar="SNAPSHOT_ZIP")
    parser.add_argument("--output", type=Path, help="New ZIP path when creating a snapshot")
    args = parser.parse_args(argv)
    try:
        if args.create_from is not None:
            if args.output is None:
                parser.error("--create-from requires --output")
            result = snapshot(args.create_from, args.output)
        else:
            if args.output is not None:
                parser.error("--verify does not accept --output")
            result = verify(args.verify)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (SnapshotError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Windows recovery snapshot refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
