"""Phase 5C: read-only macOS installation and upgrade regression checks."""
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
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit_macos_install.py"
SPEC = importlib.util.spec_from_file_location("kasa_install_audit", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def installed_layout(tmp_path, *, version="0.4.0.194"):
    directory = tmp_path / "lib/kasa-preview"
    directory.mkdir(parents=True)
    command = tmp_path / "bin"
    command.mkdir()
    (directory / "kasa-native").write_text("native binary")
    (directory / "kasa").write_text("launcher")
    (directory / "build-info.txt").write_text(
        "Source commit: " + "a" * 40 + "\n"
        "Installer build version: " + version + "\n"
        "Release: 0.4.0-alpha\n")
    (command / "kasa").symlink_to(module.EXPECTED_TARGET)
    return tmp_path


def test_expected_install_layout_is_accepted(tmp_path):
    root = installed_layout(tmp_path)
    report = module.audit(root, "0.4.0.194")
    assert report["valid"]
    assert not report["issues"]
    assert report["installed_source_commit"] == "a" * 40


def test_other_command_owner_is_rejected(tmp_path):
    root = installed_layout(tmp_path)
    (root / "bin/kasa").unlink()
    (root / "bin/kasa").symlink_to("../../other-application")
    report = module.audit(root, "0.4.0.194")
    assert not report["valid"]
    assert any("unexpected target" in item for item in report["issues"])


def test_replaced_directory_symlink_is_rejected(tmp_path):
    root = installed_layout(tmp_path)
    (root / "lib/kasa-preview/build-info.txt").unlink()
    (root / "lib/kasa-preview/kasa").unlink()
    (root / "lib/kasa-preview/kasa-native").unlink()
    (root / "lib/kasa-preview").rmdir()
    outside = root / "other"
    outside.mkdir()
    (root / "lib/kasa-preview").symlink_to(outside)
    report = module.audit(root, "0.4.0.194")
    assert not report["valid"]
    assert any("replaced with symlink" in issue for issue in report["issues"])


def test_receipt_and_metadata_disagreement_is_rejected(tmp_path):
    root = installed_layout(tmp_path)
    report = module.audit(root, "0.4.0.195")
    assert not report["valid"]
    assert any("disagree" in issue for issue in report["issues"])


def test_newer_build_accepted_but_equal_downgrade_major_version_refused():
    assert module.assess_upgrade("0.4.0.194", "0.4.0.195")[0]
    for candidate in ["0.4.0.194", "0.4.0.193", "0.4.1.195", "invalid"]:
        assert not module.assess_upgrade("0.4.0.194", candidate)[0]


def test_pkgutil_receipt_parser():
    def runner(cmd, **kwargs):
        assert cmd == ["pkgutil", "--pkg-info", module.PACKAGE_ID]
        return subprocess.CompletedProcess(cmd, 0,
            "package-id: org.kasalang.kasa.preview\nversion: 0.4.0.194\n", "")
    assert module.receipt_version(runner=runner) == "0.4.0.194"


def test_missing_receipt_is_rejected():
    def runner(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "missing")
    try:
        module.receipt_version(runner=runner)
    except ValueError as exc:
        assert "receipt" in str(exc)
    else:
        raise AssertionError("Missing receipt should not pass")
