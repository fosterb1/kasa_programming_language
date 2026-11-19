"""Windows lifecycle audit: preflight test is read-only, execution needs explicit VM gates."""
import importlib.util
from pathlib import Path
import json
import subprocess

SOURCE = Path(__file__).resolve().parents[1] / "scripts/verify_windows_installer_lifecycle.py"
spec = importlib.util.spec_from_file_location("kasa_windows_lifecycle", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

def test_read_only_preflight_with_matching_hash(tmp_path, monkeypatch):
    setup = tmp_path / "mock-setup.exe"
    setup.write_bytes(b"MZ" + b"kasa" * 1024)
    digest = tool.sha256(setup)
    report = tmp_path / "report.json"
    def prohibited(*args, **kwargs):
        raise AssertionError("Installer must never execute in preflight")
    monkeypatch.setattr(tool, "run_lifecycle", prohibited)
    result = tool.main(["--setup", str(setup), "--sha256", digest, "--report", str(report)])
    assert result == 0
    data = json.loads(report.read_text())
    assert data["setup"]["matches"]
    assert not data["executed"]
    assert "READ-ONLY" in data["note"]

def test_reject_checksum_mismatch(tmp_path):
    setup = tmp_path / "other.exe"
    setup.write_bytes(b"MZ-different")
    report = tmp_path / "bad.json"
    result = tool.main(["--setup", str(setup), "--sha256", "0" * 64,
                        "--report", str(report)])
    assert result == 1
    assert not json.loads(report.read_text())["executed"]

def test_reject_missing_vm_even_if_opted_in(tmp_path, monkeypatch):
    setup = tmp_path / "other.exe"
    setup.write_bytes(b"MZtest")
    report = tmp_path / "blocked.json"
    monkeypatch.setattr(tool, "detect_vm", lambda: (False, "physical office computer"))
    def prohibited(*args, **kwargs):
        raise AssertionError("Installer must not execute on physical Windows")
    monkeypatch.setattr(tool, "run_lifecycle", prohibited)
    code = tool.main(["--setup", str(setup), "--sha256", tool.sha256(setup),
                      "--report", str(report), "--execute-in-disposable-vm",
                      "--acknowledge-vm-snapshot", "DISPOSABLE-VM-SNAPSHOT-CONFIRMED"])
    assert code == 2
    assert not json.loads(report.read_text())["executed"]

def test_reject_vm_without_snapshot_acknowledgment(tmp_path, monkeypatch):
    setup = tmp_path / "other.exe"
    setup.write_bytes(b"MZtest")
    report = tmp_path / "no_ack.json"
    monkeypatch.setattr(tool, "detect_vm", lambda: (True, "Microsoft Corporation Virtual Machine"))
    monkeypatch.setattr(tool, "run_lifecycle", lambda *args: (_ for _ in ()).throw(AssertionError("not allowed")))
    code = tool.main(["--setup", str(setup), "--sha256", tool.sha256(setup),
                      "--report", str(report), "--execute-in-disposable-vm"])
    assert code == 2
    assert not json.loads(report.read_text())["executed"]

def test_detect_vm_non_windows_refuses(monkeypatch):
    monkeypatch.setattr(tool.os, "name", "posix")
    assert tool.detect_vm()[0] is False

def test_command_records_nonzero_without_inventing_pass(monkeypatch):
    def fake(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 5, "", "Setup refused")
    monkeypatch.setattr(tool.subprocess, "run", fake)
    result = tool.command(["setup.exe", "/VERYSILENT"])
    assert result["exit_code"] == 5
    assert "refused" in result["stderr_tail"]
