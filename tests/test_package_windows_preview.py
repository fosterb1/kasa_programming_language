"""Phase 6C unsigned Windows portable archive — offline, no admin privileges."""
import importlib.util
import json
from pathlib import Path
import subprocess
import zipfile

SOURCE = Path(__file__).resolve().parents[1] / "scripts/package_windows_preview.py"
spec = importlib.util.spec_from_file_location("kasa_windows_package", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fake_binary(tmp_path):
    """Synthetic executable; subprocess validation is mocked on Windows and POSIX."""
    exe = tmp_path / "kasa-native.exe"
    exe.write_bytes(b"MZ" + b"x" * 2000)
    return exe


def mock_version(monkeypatch, *, output="Kasa Native 0.4.0-alpha (mock)\n"):
    def run(argv, **kwargs):
        assert argv[-1] == "--version"
        return subprocess.CompletedProcess(argv, 0, output, "")
    monkeypatch.setattr(tool.subprocess, "run", run)
    monkeypatch.setattr(tool, "git_revision", lambda: "a" * 40)


def test_zip_has_expected_files_manifest_and_checksum(tmp_path, monkeypatch):
    mock_version(monkeypatch)
    dest = tool.create_package(fake_binary(tmp_path), tmp_path / "dist",
                               host="Windows", machine="AMD64")
    assert dest.exists()
    checksum = dest.with_name(dest.name + ".sha256")
    assert checksum.read_text().startswith(tool.sha256(dest.read_bytes()))
    root = dest.stem
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {
            f"{root}/kasa.cmd", f"{root}/kasa-native.exe",
            f"{root}/README.txt", f"{root}/manifest.json",
        }
        manifest = json.loads(z.read(f"{root}/manifest.json"))
        assert manifest["signature"] == "UNSIGNED"
        assert manifest["platform"] == "Windows"
        assert manifest["installer"] is False
        assert manifest["runtime_dependencies_verified_on_clean_machine"] is False
        assert manifest["binary_sha256"] == tool.sha256(z.read(f"{root}/kasa-native.exe"))
        assert b'%~dp0kasa-native.exe' in z.read(f"{root}/kasa.cmd")


def test_reject_non_windows_host(tmp_path):
    try:
        tool.create_package(fake_binary(tmp_path), tmp_path / "dist",
                            host="Linux", machine="x86_64")
    except ValueError as exc:
        assert "Windows x64" in str(exc)
    else:
        raise AssertionError("Must not label Linux build as Windows")


def test_reject_wrong_cpu_arch(tmp_path):
    try:
        tool.create_package(fake_binary(tmp_path), tmp_path / "dist",
                            host="Windows", machine="ARM64")
    except ValueError as exc:
        assert "Windows x64" in str(exc)
    else:
        raise AssertionError("Must refuse untested Windows ARM architecture")


def test_reject_wrong_executable_version(tmp_path, monkeypatch):
    exe = fake_binary(tmp_path)
    mock_version(monkeypatch, output="Not Kasa\n")
    try:
        tool.create_package(exe, tmp_path / "dist", host="Windows", machine="AMD64")
    except ValueError as exc:
        assert "version check" in str(exc)
    else:
        raise AssertionError("Foreign binary must not be packaged")


def test_reject_existing_archive_without_overwrite(tmp_path, monkeypatch):
    mock_version(monkeypatch)
    exe = fake_binary(tmp_path)
    dest = tool.create_package(exe, tmp_path / "dist", host="Windows", machine="AMD64")
    previous = dest.read_bytes()
    try:
        tool.create_package(exe, tmp_path / "dist", host="Windows", machine="AMD64")
    except ValueError as exc:
        assert "overwrite" in str(exc)
    else:
        raise AssertionError("Must not overwrite original artifact")
    assert dest.read_bytes() == previous
