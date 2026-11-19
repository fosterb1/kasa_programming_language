"""Phase 6F: read-only Windows upgrade planner; never treats an audit as permission to update."""
import importlib.util
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts/plan_windows_upgrade.py"
spec = importlib.util.spec_from_file_location("kasa_win_upgrade", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def package(tmp_path, name, version="0.4.0.1", binary=b"MZ-kasa", installed=False):
    root = tmp_path / name
    root.mkdir()
    (root / "kasa-native.exe").write_bytes(binary)
    (root / "kasa.cmd").write_text("@echo off")
    (root / "README.txt").write_text("test")
    (root / "kasa-install-identity.txt").write_text(tool.IDENTITY + "\n")
    (root / "manifest.json").write_text(json.dumps({
        "release": "0.4.0-alpha", "platform": "Windows", "architecture": "x64",
        "installer_build_version": version, "binary_sha256": tool.sha256(root/"kasa-native.exe"),
    }))
    if installed:
        (root / "unins000.exe").write_bytes(b"mock-uninstall")
    return root


def test_version_comparison_rejects_bad_formats():
    assert tool.parse_version("0.4.0.202") == (0, 4, 0, 202)
    for invalid in ("0.4.0", "0.4.0.-1", "0.4.0.01", "1.0.0-alpha", "", None, 1):
        assert tool.parse_version(invalid) is None


def test_current_unsigned_preview_has_no_upgrade_build_version(tmp_path):
    root = package(tmp_path, "candidate", version="0.4.0.202")
    data = json.loads((root / "manifest.json").read_text())
    del data["installer_build_version"]
    (root / "manifest.json").write_text(json.dumps(data))
    result = tool.inspect_directory(root, installed=False)
    assert not result["valid"]
    assert any("installer_build_version" in issue for issue in result["issues"])


def test_hash_mismatch_blocks(tmp_path):
    root = package(tmp_path, "candidate")
    (root / "kasa-native.exe").write_bytes(b"tampered")
    result = tool.inspect_directory(root, installed=False)
    assert not result["valid"]
    assert any("hash mismatch" in issue for issue in result["issues"])


def test_unknown_user_file_blocks_and_remains_untouched(tmp_path):
    root = package(tmp_path, "installed", installed=True)
    file = root / "user-code.kasa"
    file.write_text('ka "hello"')
    result = tool.inspect_directory(root, installed=True)
    assert not result["valid"]
    assert file.read_text() == 'ka "hello"'


def test_alien_identity_marker_blocks(tmp_path):
    root = package(tmp_path, "candidate")
    (root / "kasa-install-identity.txt").write_text("foreign product")
    assert not tool.inspect_directory(root, installed=False)["valid"]


def test_symlinked_directory_is_refused(tmp_path):
    root = package(tmp_path, "candidate")
    link = tmp_path / "link"
    try:
        link.symlink_to(root, target_is_directory=True)
    except OSError:
        return  # no Windows symlink privilege; do not elevate merely for tests
    result = tool.inspect_directory(link, installed=False)
    assert not result["valid"]


def test_strictly_newer_versions_still_blocked_without_verified_rollback(tmp_path):
    previous = tool.inspect_directory(package(tmp_path, "old", version="0.4.0.1", installed=True), installed=True)
    future = tool.inspect_directory(package(tmp_path, "new", version="0.4.0.2"), installed=False)
    assert future["valid"]
    verdict = tool.assess(previous, future)
    assert verdict["safe_to_upgrade"] is False
    assert any("rollback" in reason for reason in verdict["reasons"])


def test_non_increasing_versions_rejected(tmp_path):
    old = tool.inspect_directory(package(tmp_path, "old", version="0.4.0.3", installed=True), installed=True)
    new = tool.inspect_directory(package(tmp_path, "new", version="0.4.0.2"), installed=False)
    verdict = tool.assess(old, new)
    assert not verdict["safe_to_upgrade"]
    assert any("not a strictly newer" in reason for reason in verdict["reasons"])


def test_read_only_report_preserves_install_and_candidate(tmp_path):
    current = package(tmp_path, "installed", version="0.4.0.1", installed=True)
    candidate = package(tmp_path, "candidate", version="0.4.0.2")
    before = {str(f): f.read_bytes() for root in (current, candidate) for f in root.iterdir()}
    report = tmp_path / "upgrade.json"
    assert tool.main(["--candidate", str(candidate), "--installed-dir", str(current),
                      "--report", str(report)]) == 0
    info = json.loads(report.read_text())
    assert info["mode"] == "READ_ONLY"
    assert info["upgrade"]["safe_to_upgrade"] is False
    assert all(Path(path).read_bytes() == data for path, data in before.items())


def test_nonexistent_package_is_not_eligible(tmp_path):
    result = tool.inspect_directory(tmp_path / "not-present", installed=False)
    assert not result["valid"]
