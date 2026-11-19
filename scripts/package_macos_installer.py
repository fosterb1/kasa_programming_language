#!/usr/bin/env python3
"""Prepare an unsigned macOS Installer .pkg for Kasa's native 0.4 alpha.

Creates a payload and calls Apple's pkgbuild. Does NOT install the package.
No sudo, publishing, signing, or changes to system directories at build time.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile

from package_native_preview import LAUNCHER, ROOT

PACKAGE_ID = "org.kasalang.kasa.preview"
VERSION_PREFIX = "0.4.0"
PACKAGE_LINK = "../lib/kasa-preview/kasa"
PREINSTALL = """#!/bin/sh
# Fail safely if another program already owns /usr/local/bin/kasa.
set -eu
link="/usr/local/bin/kasa"
if [ -L "$link" ]; then
  target=$(readlink "$link")
  if [ "$target" != "../lib/kasa-preview/kasa" ]; then
    echo "Refusing to replace existing kasa symlink: $link -> $target" >&2
    exit 1
  fi
elif [ -e "$link" ]; then
  echo "Refusing to replace existing /usr/local/bin/kasa" >&2
  exit 1
fi
exit 0
"""


def checked(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=30, check=False)
    if p.returncode:
        raise ValueError(f"Command failed: {command[0]}: {(p.stderr or p.stdout)[-700:]}")
    return p


def version_from_git() -> tuple[str, str]:
    commit = checked(["git", "rev-parse", "HEAD"]).stdout.strip()
    count = checked(["git", "rev-list", "--count", "HEAD"]).stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", commit) or not count.isdecimal() or int(count) < 1:
        raise ValueError("Cannot derive a trustworthy revision and incrementing build number")
    if checked(["git", "status", "--porcelain", "--untracked-files=normal"]).stdout.strip():
        raise ValueError("Source checkout is dirty; commit or revert changes before packaging")
    # pkgbuild versions must be numeric; monotonically increasing revision count
    # makes a later commit an upgrade instead of an equal-version reinstall.
    return f"{VERSION_PREFIX}.{count}", commit


def build(binary: Path, output: Path) -> Path:
    if platform.system() != "Darwin":
        raise ValueError("Installer builds require macOS and Apple's pkgbuild")
    if platform.machine() not in ("x86_64", "arm64"):
        raise ValueError("Unsupported macOS architecture")
    if shutil.which("pkgbuild") is None:
        raise ValueError("Apple pkgbuild is missing; install Command Line Tools")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError("Native executable missing; run full verification first")
    version, commit = version_from_git()
    actual = checked([str(binary), "--version"]).stdout.strip()
    if not actual.startswith("Kasa Native 0.4.0-alpha"):
        raise ValueError("Wrong Kasa native executable/version")
    # Refuse to disguise an old compiled binary as a new source revision.
    source_files = [ROOT / "native/CMakeLists.txt", *list((ROOT / "native/src").glob("*")),
                    *list((ROOT / "native/include").rglob("*.hpp"))]
    if any(p.is_file() and p.stat().st_mtime_ns > binary.stat().st_mtime_ns for p in source_files):
        raise ValueError("Native binary is older than source files; rerun bash scripts/mac_dev.sh full")
    arch = platform.machine()
    output.mkdir(parents=True, exist_ok=True)
    dest = output / f"kasa-{version}-macos-{arch}-UNSIGNED.pkg"
    with tempfile.TemporaryDirectory(prefix="kasa-pkg-") as work:
        root = Path(work) / "payload"
        app = root / "usr/local/lib/kasa-preview"
        cmd = root / "usr/local/bin"
        app.mkdir(parents=True)
        cmd.mkdir(parents=True)
        shutil.copy2(binary, app / "kasa-native")
        (app / "kasa-native").chmod(0o755)
        (app / "kasa").write_text(LAUNCHER, encoding="utf-8")
        (app / "kasa").chmod(0o755)
        (cmd / "kasa").symlink_to(PACKAGE_LINK)
        (app / "build-info.txt").write_text(
            f"Source commit: {commit}\nInstaller build version: {version}\n"
            f"Platform: macOS {arch}\nRelease: 0.4.0-alpha\n"
            "UNSIGNED, UNNOTARIZED developer preview\n", encoding="utf-8")
        scripts = Path(work) / "scripts"
        scripts.mkdir()
        (scripts / "preinstall").write_text(PREINSTALL, encoding="utf-8")
        (scripts / "preinstall").chmod(0o755)
        checked(["pkgbuild", "--root", str(root), "--scripts", str(scripts),
                 "--identifier", PACKAGE_ID, "--version", version,
                 "--install-location", "/", str(dest)])
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    (output / (dest.name + ".sha256")).write_text(f"{digest}  {dest.name}\n", encoding="ascii")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "build/kasa-local/kasa-native")
    parser.add_argument("--output", type=Path, default=ROOT / "build/dist")
    args = parser.parse_args()
    try:
        dest = build(args.binary.resolve(), args.output.resolve())
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Installer build refused: {exc}", file=sys.stderr)
        return 1
    print(f"Created unsigned installer: {dest}")
    print(f"Checksum: {dest}.sha256")
    print("NOT installed. This system-wide pkg would need admin approval.")
    print("Inspect with pkgutil --check-signature and pkgutil --expand before installation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
