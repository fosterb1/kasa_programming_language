"""Phase 6F.5 read-only reconstruction audit; no app installation or execution."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for name, path in [
    ("kasa_windows_reconstruction_audit", ROOT / "scripts/audit_windows_reconstruction.py"),
    ("kasa_windows_simulation_test", ROOT / "scripts/simulate_windows_recovery.py"),
]:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()["audit_tool" if "audit" in name else "sim_tool"] = module


def prepared(tmp_path):
    source = tmp_path / "original-payload"
    source.mkdir()
    binary = b"MZ" + b"realistic-archive-payload" * 20
    (source / "kasa-native.exe").write_bytes(binary)
    (source / "kasa.cmd").write_bytes(b"@echo off\r\n")
    (source / "README.txt").write_bytes(b"read me")
    (source / "kasa-install-identity.txt").write_bytes(
        (sim_tool.snapshot_lib.IDENTITY + "\r\n").encode("ascii"))
    (source / "manifest.json").write_text(json.dumps({
        "release": "0.4.0-alpha", "platform": "Windows", "architecture": "x64",
        "binary_sha256": sim_tool.snapshot_lib.digest(binary),
        "source_commit": "a" * 40,
    }))
    snapshot = tmp_path / "backup.zip"
    sim_tool.snapshot_lib.snapshot(source, snapshot)
    workspace = tmp_path / "recon"
    result = sim_tool.simulate(snapshot, workspace)
    assert result["passed"] is True
    return source, snapshot, workspace


def test_complete_snapshot_and_reconstruction_pass(tmp_path):
    source, snapshot, workspace = prepared(tmp_path)
    before = {p.name: p.read_bytes() for p in source.iterdir()}
    record = audit_tool.audit(workspace)
    assert record["passed"] is True
    assert set(record["files_verified"]) == sim_tool.snapshot_lib.FILES
    assert record["installed_files_touched_by_audit"] is False
    assert all((source / name).read_bytes() == data for name, data in before.items())


def test_reconstructed_binary_corruption_detected(tmp_path):
    _, _, workspace = prepared(tmp_path)
    (workspace / "reconstructed-payload/kasa-native.exe").write_bytes(b"modified")
    record = audit_tool.audit(workspace)
    assert record["passed"] is False
    assert any("mismatch" in issue or "SHA-256" in issue for issue in record["issues"])


def test_reconstructed_launcher_corruption_detected(tmp_path):
    _, _, workspace = prepared(tmp_path)
    (workspace / "reconstructed-payload/kasa.cmd").write_bytes(b"bad cmd")
    record = audit_tool.audit(workspace)
    assert not record["passed"]
    assert any("disagrees" in issue for issue in record["issues"])


def test_incomplete_simulation_refused(tmp_path):
    _, archive, _ = prepared(tmp_path)
    failure_space = tmp_path / "incomplete"
    result = sim_tool.simulate(archive, failure_space, fail_after=3)
    assert result["passed"] is False
    audited = audit_tool.audit(failure_space)
    assert not audited["passed"]
    assert any("did not complete" in issue for issue in audited["issues"])


def test_report_modified_to_fake_success_is_not_sufficient(tmp_path):
    _, _, workspace = prepared(tmp_path)
    (workspace / "reconstructed-payload/kasa.cmd").write_bytes(b"tampered")
    report_path = workspace / "simulation-report.json"
    report = json.loads(report_path.read_text())
    report["passed"] = True
    report_path.write_text(json.dumps(report))
    assert audit_tool.audit(workspace)["passed"] is False


def test_missing_or_corrupt_backup_detected(tmp_path):
    _, backup, workspace = prepared(tmp_path)
    backup.with_name(backup.name + ".sha256").write_text("0" * 64 + "  " + backup.name)
    record = audit_tool.audit(workspace)
    assert not record["passed"]
    assert any("checksum" in issue for issue in record["issues"])


def test_missing_snapshot_member_refused(tmp_path):
    _, _, workspace = prepared(tmp_path)
    (workspace / "reconstructed-payload/README.txt").unlink()
    assert audit_tool.audit(workspace)["passed"] is False


def test_unrelated_project_file_remains_untouched(tmp_path):
    source, _, workspace = prepared(tmp_path)
    user_program = tmp_path / "important.kasa"
    user_program.write_text('ka "do not touch"')
    audit_tool.audit(workspace)
    assert user_program.read_text() == 'ka "do not touch"'
    assert (source / "kasa-native.exe").exists()


def test_symlink_payload_directory_refused(tmp_path):
    _, _, workspace = prepared(tmp_path)
    link = tmp_path / "symlink"
    try:
        link.symlink_to(workspace / "reconstructed-payload", target_is_directory=True)
    except OSError:
        pytest.skip("Symlink not permitted on this Windows machine")
    (workspace / "reconstructed-payload").rename(workspace / "original-payload")
    (workspace / "reconstructed-payload").symlink_to(workspace / "original-payload", target_is_directory=True)
    assert audit_tool.audit(workspace)["passed"] is False


def test_cli_refuses_workspace_outside_sandbox(tmp_path):
    result = audit_tool.main(["--workspace", str(tmp_path)])
    assert result == 2
