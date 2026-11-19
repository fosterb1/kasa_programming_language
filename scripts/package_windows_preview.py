#!/usr/bin/env python3
"""Package a verified native Kasa Windows x64 build as an unsigned portable ZIP.

No installation, PATH edits, registry changes, downloads, or administrator rights.
This is a developer preview; it is not a signed public release or Windows installer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "0.4.0-alpha"
BIN = ROOT / "build/kasa-local/Release/kasa-native.exe"
CMD = "@echo off\r\nsetlocal\r\n\"%~dp0kasa-native.exe\" %*\r\nexit /b %errorlevel%\r\n"
GUIDE = (
    "Kasa 0.4.0-alpha — UNSIGNED Windows x64 portable developer preview\r\n"
    "Extract the entire ZIP to a folder you control. Do not run from inside ZIP.\r\n"
    "From CMD in that folder: kasa.cmd --version\r\n"
    "Run a .kasa file: kasa.cmd run C:\\path\\to\\hello.kasa\r\n"
    "You can also run kasa-native.exe directly. No Python, CMake or Node is needed\r\n"
    "for execution, though Windows may require Microsoft VC++ runtime libraries.\r\n"
    "No machine-wide installation, PATH modification, registry changes or uninstaller.\r\n"
    "Remove the extracted folder to remove this portable developer preview.\r\n"
    "UNSIGNED / untrusted for public redistribution; test on another Windows PC.\r\n"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_revision() -> str:
    try:
        proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                              capture_output=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    commit = proc.stdout.strip()
    return commit if proc.returncode == 0 and re.fullmatch(r"[a-f0-9]{40}", commit) else "unknown"


def create_package(binary: Path, output: Path, *, host: str | None = None,
                   machine: str | None = None) -> Path:
    system = host if host is not None else platform.system()
    arch = machine if machine is not None else platform.machine()
    if system != "Windows" or arch.lower() not in ("amd64", "x86_64"):
        raise ValueError("Windows x64 host required for this portable build")
    if not binary.is_file():
        raise ValueError("Native Windows executable missing; build the Release target first")
    if binary.suffix.lower() != ".exe":
        raise ValueError("Expected a native .exe, not a script or POSIX binary")
    try:
        proc = subprocess.run([str(binary), "--version"], capture_output=True,
                              text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as err:
        raise ValueError(f"Native executable could not be verified: {err}") from err
    if proc.returncode != 0 or not proc.stdout.strip().startswith("Kasa Native 0.4.0-alpha"):
        raise ValueError("Binary did not pass Kasa version check; refusing to package")
    data = binary.read_bytes()
    if len(data) < 1000:
        raise ValueError("Native executable implausibly small")
    # Detect accidentally packaging a binary from a previous source change.
    native_sources = [ROOT / "native/CMakeLists.txt",
                      *(ROOT / "native/src").glob("*.cpp"),
                      *(ROOT / "native/include").rglob("*.hpp")]
    if any(p.is_file() and p.stat().st_mtime_ns > binary.stat().st_mtime_ns for p in native_sources):
        raise ValueError("Native executable older than native source; rebuild Release before packaging")
    commit = git_revision()
    name = f"kasa-{RELEASE}-windows-x64-UNSIGNED-dev"
    output.mkdir(parents=True, exist_ok=True)
    dest = output / (name + ".zip")
    if dest.exists() or (output / (dest.name + ".sha256")).exists():
        raise ValueError("Archive or checksum already exists; refusing to overwrite developer artifacts")
    manifest = {
        "release": RELEASE,
        "platform": "Windows",
        "architecture": "x64",
        "channel": "development-preview",
        "source_commit": commit,
        "native_version": proc.stdout.strip(),
        "binary_sha256": sha256(data),
        "signature": "UNSIGNED",
        "installer": False,
        "runtime_dependencies_verified_on_clean_machine": False,
    }
    entries = {
        "kasa-native.exe": data,
        "kasa.cmd": CMD.encode("ascii"),
        "README.txt": GUIDE.encode("utf-8"),
        "manifest.json": (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    }
    partial = output / (name + ".zip.partial")
    try:
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for filename, payload in entries.items():
                z.writestr(f"{name}/{filename}", payload)
        with zipfile.ZipFile(partial) as z:
            if z.testzip() is not None or set(z.namelist()) != {
                f"{name}/{entry}" for entry in entries
            }:
                raise ValueError("Archive verification failed")
        # Do not allow an existing ZIP to be silently replaced.
        if dest.exists():
            raise ValueError("Archive appeared during packaging; refusing overwrite")
        partial.rename(dest)
        checksum = output / (dest.name + ".sha256")
        checksum.write_text(f"{sha256(dest.read_bytes())}  {dest.name}\n", encoding="ascii")
    finally:
        if partial.exists():
            partial.unlink()
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=BIN)
    parser.add_argument("--output", type=Path, default=ROOT / "build/dist")
    args = parser.parse_args()
    try:
        dest = create_package(args.binary.resolve(), args.output.resolve())
    except (ValueError, OSError) as exc:
        print(f"Windows packaging refused: {exc}", file=sys.stderr)
        return 1
    print("Created unsigned Windows portable development archive:", dest)
    print("Checksum:", str(dest) + ".sha256")
    print("NOT installed or released; no PATH, registry or machine changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
