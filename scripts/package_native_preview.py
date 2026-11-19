#!/usr/bin/env python3
"""Build a local, unnotarized Kasa native development-preview archive.

No downloads, publishing, sudo, or changes to the user's PATH.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = """#!/bin/sh
# Resolve symlinks: a user-local ~/.local/bin/kasa link can target this launcher.
set -eu
self=$0
while [ -L "$self" ]; do
  parent=$(CDPATH= cd -- "$(dirname -- "$self")" && pwd)
  link=$(readlink "$self")
  case "$link" in /*) self="$link";; *) self="$parent/$link";; esac
done
here=$(CDPATH= cd -- "$(dirname -- "$self")" && pwd)
exec "$here/kasa-native" "$@"
"""

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package(binary: Path, output: Path, *, allow_non_macos: bool = False) -> Path:
    if platform.system() != "Darwin" and not allow_non_macos:
        raise ValueError("This preview targets macOS; use --allow-non-macos for local packaging tests")
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f"Built executable is missing or not executable: {binary}")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=False)
    commit = revision.stdout.strip() if revision.returncode == 0 else "unknown"
    version = subprocess.run([str(binary), "--version"], capture_output=True, text=True,
                             timeout=10, check=False)
    if version.returncode != 0 or not version.stdout.startswith("Kasa Native "):
        raise ValueError("Binary failed the Kasa native version check; refusing to package")
    system = platform.system().lower()
    machine = platform.machine().lower()
    name = f"kasa-0.4.0-alpha-{system}-{machine}-dev"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{name}.tar.gz"
    with tempfile.TemporaryDirectory(prefix="kasa-pack-") as temp:
        root = Path(temp) / name
        root.mkdir()
        shutil.copy2(binary, root / "kasa-native")
        (root / "kasa-native").chmod((root / "kasa-native").stat().st_mode | stat.S_IXUSR)
        (root / "kasa").write_text(LAUNCHER, encoding="utf-8")
        (root / "kasa").chmod(0o755)
        info = {
            "release": "0.4.0-alpha", "channel": "development-preview",
            "platform": system, "architecture": machine, "source_commit": commit,
            "native_version": version.stdout.strip(),
            "binary_sha256": sha256(root / "kasa-native"),
            "signature": "UNSIGNED", "notarized": False,
        }
        (root / "manifest.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        (root / "README.txt").write_text(
            "Kasa 0.4.0-alpha -- UNSIGNED local development preview.\n"
            "Built on this machine; no Apple notarization or broad compatibility claim.\n\n"
            "Run ./kasa --version or ./kasa run /path/to/program.kasa\n"
            "Optional user-local installation:\n"
            "  mkdir -p \"$HOME/.local/opt/kasa\" \"$HOME/.local/bin\"\n"
            "  cp kasa kasa-native \"$HOME/.local/opt/kasa/\"\n"
            "  ln -s \"$HOME/.local/opt/kasa/kasa\" \"$HOME/.local/bin/kasa\"\n"
            "  Add $HOME/.local/bin to your PATH if needed.\n"
            "Uninstall by removing the link and $HOME/.local/opt/kasa directory.\n",
            encoding="utf-8")
        with tarfile.open(archive, "w:gz") as bundle:
            bundle.add(root, arcname=name, recursive=True)
    digest = sha256(archive)
    (output / (archive.name + ".sha256")).write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "build/kasa-local/kasa-native")
    parser.add_argument("--output", type=Path, default=ROOT / "build/dist")
    parser.add_argument("--allow-non-macos", action="store_true", help="For packaging regression tests only")
    options = parser.parse_args()
    try:
        archive = package(options.binary.resolve(), options.output.resolve(),
                          allow_non_macos=options.allow_non_macos)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Packaging refused: {exc}", file=sys.stderr)
        return 1
    print(f"Created: {archive}")
    print(f"SHA256:  {archive}.sha256")
    print("UNSIGNED development preview; not a notarized public macOS installer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
