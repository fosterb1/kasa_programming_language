"""Phase 6F.2 versioned Windows ZIP is additive and never upgrades."""
import importlib.util
import hashlib
import json
from pathlib import Path
import zipfile
import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/version_windows_preview.py"
spec = importlib.util.spec_from_file_location("version_win", PATH)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def source(tmp_path):
    src = tmp_path / "kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip"
    payload = b"MZ" + b"x" * 1000
    manifest = {
        "release": "0.4.0-alpha", "platform": "Windows", "architecture": "x64",
        "channel": "development-preview", "signature": "UNSIGNED",
        "installer": False, "source_commit": "a" * 40,
        "binary_sha256": tool.sha256(payload), "runtime_dependencies_verified_on_clean_machine": False,
    }
    items = {"manifest.json": json.dumps(manifest).encode(), "kasa-native.exe": payload,
             "kasa.cmd": b"@echo off\r\n", "README.txt": b"unsigned"}
    with zipfile.ZipFile(src, "w") as z:
        for name, data in items.items():
            z.writestr(f"{src.stem}/{name}", data)
    sidecar = src.with_name(src.name + ".sha256")
    sidecar.write_text(f"{tool.sha256(src.read_bytes())}  {src.name}\n")
    return src


def test_build_version_validation():
    assert tool.build_version(203) == "0.4.0.203"
    for bad in (-1, 0, 65536, "203", True, None):
        with pytest.raises(ValueError):
            tool.build_version(bad)


def test_versioned_zip_and_build_only_receipt(tmp_path):
    src = source(tmp_path)
    original_zip, original_sha = src.read_bytes(), (tmp_path / (src.name + ".sha256")).read_bytes()
    dest = tool.package(src, tmp_path / "dist", 203)
    receipt_path = dest.with_suffix(".receipt.json")
    report = json.loads(receipt_path.read_text())
    assert report["receipt_kind"] == "BUILD_ONLY_NOT_INSTALLED"
    assert report["installer_build_version"] == "0.4.0.203"
    assert report["upgrades_allowed"] is False and report["signed"] is False
    assert report["source_commit"] == "a" * 40
    assert report["archive_sha256"] == tool.sha256(dest.read_bytes())
    assert (tmp_path / "dist" / (dest.name + ".sha256")).read_text().startswith(report["archive_sha256"])
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == {f"{dest.stem}/{name}" for name in report["files_sha256"]}
        new_manifest = json.loads(z.read(f"{dest.stem}/manifest.json"))
        assert new_manifest["installer_build_version"] == "0.4.0.203"
        assert new_manifest["installation_receipt_status"] == "NOT_INSTALLED"
        assert new_manifest["upgrade_supported"] is False
        for name, digest in report["files_sha256"].items():
            assert tool.sha256(z.read(f"{dest.stem}/{name}")) == digest
    assert src.read_bytes() == original_zip
    assert (tmp_path / (src.name + ".sha256")).read_bytes() == original_sha


def test_repeated_build_refuses_overwrite(tmp_path):
    src = source(tmp_path)
    dest = tool.package(src, tmp_path / "dist", 1)
    before = dest.read_bytes()
    with pytest.raises(ValueError, match="overwriting|overwrite"):
        tool.package(src, tmp_path / "dist", 1)
    assert dest.read_bytes() == before


def test_bad_source_checksum_rejected_without_output(tmp_path):
    src = source(tmp_path)
    src.with_name(src.name + ".sha256").write_text("0" * 64 + "  " + src.name)
    with pytest.raises(ValueError, match="SHA-256"):
        tool.package(src, tmp_path / "dist", 5)
    assert not (tmp_path / "dist").exists()


def test_native_binary_mismatch_rejected(tmp_path):
    src = source(tmp_path)
    with zipfile.ZipFile(src, "a") as z:
        z.writestr(f"{src.stem}/kasa-native.exe", b"changed")
    src.with_name(src.name + ".sha256").write_text(tool.sha256(src.read_bytes()) + "  " + src.name)
    with pytest.raises(ValueError, match="unknown|binary SHA-256"):
        tool.package(src, tmp_path / "dist", 5)


def test_missing_or_invalid_source_commit_refused(tmp_path):
    src = source(tmp_path)
    with zipfile.ZipFile(src) as z:
        values = {key: z.read(key) for key in z.namelist()}
    key = f"{src.stem}/manifest.json"
    manifest = json.loads(values[key])
    manifest["source_commit"] = "unknown"
    values[key] = json.dumps(manifest).encode()
    with zipfile.ZipFile(src, "w") as z:
        for name, value in values.items():
            z.writestr(name, value)
    src.with_name(src.name + ".sha256").write_text(tool.sha256(src.read_bytes()) + "  " + src.name)
    with pytest.raises(ValueError, match="source commit"):
        tool.package(src, tmp_path / "dist", 5)


def test_wrong_package_platform_refused(tmp_path):
    src = source(tmp_path)
    with zipfile.ZipFile(src) as z:
        values = {key: z.read(key) for key in z.namelist()}
    key = f"{src.stem}/manifest.json"
    manifest = json.loads(values[key])
    manifest["platform"] = "Linux"
    values[key] = json.dumps(manifest).encode()
    with zipfile.ZipFile(src, "w") as z:
        for name, value in values.items():
            z.writestr(name, value)
    src.with_name(src.name + ".sha256").write_text(tool.sha256(src.read_bytes()) + "  " + src.name)
    with pytest.raises(ValueError, match="identity"):
        tool.package(src, tmp_path / "dist", 5)


def test_existing_sidecar_prevents_creation(tmp_path):
    src = source(tmp_path)
    target = tmp_path / "dist"
    target.mkdir()
    sidecar = target / "kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev-build-2.zip.sha256"
    sidecar.write_text("keep")
    with pytest.raises(ValueError, match="overwrite"):
        tool.package(src, target, 2)
    assert sidecar.read_text() == "keep"


def test_no_source_mutation_on_missing_package(tmp_path):
    with pytest.raises(ValueError, match="Verified source ZIP"):
        tool.package(tmp_path / "missing.zip", tmp_path / "out", 10)
    assert not (tmp_path / "out").exists()
