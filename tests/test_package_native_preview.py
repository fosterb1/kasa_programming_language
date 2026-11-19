"""Offline packaging checks: no compiler, installer, network or macOS required."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tarfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts/package_native_preview.py"


def load():
    spec = importlib.util.spec_from_file_location("kasa_package_preview", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mock_native(tmp_path: Path) -> Path:
    binary = tmp_path / "kasa-native"
    binary.write_text(
        '#!/bin/sh\n'
        'if [ "$1" = "--version" ]; then\n'
        '  echo "Kasa Native 0.4.0-alpha (mock)"\n'
        'else\n'
        '  printf "run:%s\\n" "$1"\n'
        'fi\n',
        encoding="utf-8")
    binary.chmod(0o755)
    return binary


def test_archive_has_versioned_manifest_launcher_and_sha256(tmp_path, monkeypatch):
    tool = load()
    monkeypatch.setattr(tool.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(tool.platform, "machine", lambda: "x86_64")
    archive = tool.package(mock_native(tmp_path), tmp_path / "dist")
    checksum = archive.with_name(archive.name + ".sha256")
    assert checksum.read_text().startswith(tool.sha256(archive))
    with tarfile.open(archive, "r:gz") as tar:
        root = archive.name.removesuffix(".tar.gz")
        assert set(tar.getnames()) == {
            root,
            f"{root}/README.txt",
            f"{root}/kasa",
            f"{root}/kasa-native",
            f"{root}/manifest.json",
        }
        info = json.load(tar.extractfile(f"{root}/manifest.json"))
        assert info["signature"] == "UNSIGNED"
        assert info["notarized"] is False
        assert info["architecture"] == "x86_64"
        with tar.extractfile(f"{root}/kasa") as stream:
            assert b'exec "$here/kasa-native" "$@"' in stream.read()
        assert tar.getmember(f"{root}/kasa").mode & stat.S_IXUSR


def test_launcher_follows_user_local_symlink(tmp_path, monkeypatch):
    tool = load()
    monkeypatch.setattr(tool.platform, "system", lambda: "Darwin")
    archive = tool.package(mock_native(tmp_path), tmp_path / "dist")
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(tmp_path / "unpacked", filter="data")
    root = tmp_path / "unpacked" / archive.name.removesuffix(".tar.gz")
    shortcut = tmp_path / "local-bin"
    shortcut.mkdir()
    (shortcut / "kasa").symlink_to(root / "kasa")
    result = subprocess.run([str(shortcut / "kasa"), "--version"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout.startswith("Kasa Native 0.4.0-alpha")
    output = subprocess.run([str(shortcut / "kasa"), "run", "example.kasa"],
                            capture_output=True, text=True, check=False)
    assert output.returncode == 0
    assert output.stdout == "run:run\\n".replace("\\n", "\n")


def test_wrong_binary_refused(tmp_path, monkeypatch):
    tool = load()
    monkeypatch.setattr(tool.platform, "system", lambda: "Darwin")
    wrong = tmp_path / "wrong"
    wrong.write_text("#!/bin/sh\necho 'Not Kasa'\n", encoding="utf-8")
    wrong.chmod(0o755)
    try:
        tool.package(wrong, tmp_path / "out")
    except ValueError as exc:
        assert "version check" in str(exc)
    else:
        raise AssertionError("Foreign binary must be rejected")


def test_non_mac_refused_by_default(tmp_path, monkeypatch):
    tool = load()
    monkeypatch.setattr(tool.platform, "system", lambda: "Linux")
    try:
        tool.package(mock_native(tmp_path), tmp_path / "out")
    except ValueError as exc:
        assert "macOS" in str(exc)
    else:
        raise AssertionError("Non-macOS host must not be represented as macOS preview")
