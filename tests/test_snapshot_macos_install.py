"""Phase 5E recovery backup tests: protect installed and project files."""
import os
import pytest

# These fixtures model a Unix macOS package with POSIX symlinks.
# Windows users should not need administrator privileges or Developer Mode
# to verify the portable Kasa language and native compiler.
pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="macOS POSIX-symlink installation fixture is not a Windows release test"
)


import importlib.util
from pathlib import Path
import sys
import tarfile
import json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("kasa_recovery", SCRIPTS / "snapshot_macos_install.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

def installed(tmp_path):
    base = tmp_path / "usr-local"
    lib = base / "lib/kasa-preview"
    lib.mkdir(parents=True)
    cmd = base / "bin"
    cmd.mkdir()
    (cmd / "kasa").symlink_to("../lib/kasa-preview/kasa")
    (lib / "kasa").write_text("#!/bin/sh\n")
    (lib / "kasa-native").write_bytes(b"native")
    (lib / "build-info.txt").write_text(
        "Source commit: " + "a" * 40 + "\nInstaller build version: 0.4.0.202\nRelease: 0.4.0-alpha\n"
    )
    return base

def test_snapshot_preserves_installed_and_personal_files(tmp_path):
    root = installed(tmp_path)
    project = tmp_path / "hello.kasa"
    project.write_text('ka "Akwaaba!"\n')
    outfile = tmp_path / "backups/recovery.tar.gz"
    tool.snapshot(root, "0.4.0.202", outfile)
    assert project.read_text() == 'ka "Akwaaba!"\n'
    assert (root / "lib/kasa-preview/kasa-native").read_bytes() == b"native"
    with tarfile.open(outfile, "r:gz") as archive:
        names = archive.getnames()
        assert len(names) == 5
        assert "bin/kasa" in names
        assert "recovery-manifest.json" in names
        assert "hello.kasa" not in names
        assert archive.getmember("bin/kasa").issym()
        manifest = json.load(archive.extractfile("recovery-manifest.json"))
        assert manifest["installed_version"] == "0.4.0.202"
        assert manifest["symlink_target"] == "../lib/kasa-preview/kasa"
        assert manifest["files"]["lib/kasa-preview/kasa-native"] == tool.digest(root / "lib/kasa-preview/kasa-native")

def test_snapshot_never_overwrites_existing_backup(tmp_path):
    root = installed(tmp_path)
    dest = tmp_path / "recovery.tar.gz"
    dest.write_text("keep-me")
    try:
        tool.snapshot(root, "0.4.0.202", dest)
    except ValueError as exc:
        assert "overwrite" in str(exc)
    else:
        raise AssertionError("Must not overwrite an existing snapshot")
    assert dest.read_text() == "keep-me"

def test_snapshot_refuses_modified_installation(tmp_path):
    root = installed(tmp_path)
    (root / "bin/kasa").unlink()
    (root / "bin/kasa").symlink_to("other")
    try:
        tool.snapshot(root, "0.4.0.202", tmp_path / "backup.tar.gz")
    except ValueError as exc:
        assert "ownership" in str(exc)
    else:
        raise AssertionError("Should reject invalid installation")
