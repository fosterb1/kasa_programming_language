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


def test_lifecycle_rejects_second_install_before_uninstall(tmp_path, monkeypatch):
    """Simulation checks call order and guards; no real Setup executable runs."""
    fake_setup = tmp_path / "setup.exe"
    fake_setup.write_bytes(b"MZ-mock")
    calls = []
    def simulated_command(argv, timeout=120):
        calls.append(list(argv))
        target_arg = next((a for a in argv if a.startswith("/DIR=")), None)
        if target_arg and target_arg.endswith("occupied"):
            return {"exit_code": 2, "stdout_tail": "", "stderr_tail": "occupied"}
        if target_arg and target_arg.endswith("fresh-install"):
            dest = Path(target_arg[5:])
            if dest.exists():
                return {"exit_code": 2, "stdout_tail": "", "stderr_tail": "already installed"}
            dest.mkdir()
            for name in ("kasa-native.exe", "kasa.cmd", "manifest.json",
                         "README.txt", "kasa-install-identity.txt"):
                (dest/name).write_bytes(b"mock-file")
            return {"exit_code": 0, "stdout_tail": "", "stderr_tail": ""}
        if argv[-1] == "--version":
            return {"exit_code": 0, "stdout_tail": "Kasa Native 0.4.0-alpha", "stderr_tail": ""}
        if "run" in argv:
            return {"exit_code": 0, "stdout_tail": "Akwaaba Ghana!", "stderr_tail": ""}
        if "unins000.exe" in str(argv[0]):
            return {"exit_code": 0, "stdout_tail": "", "stderr_tail": ""}
        raise AssertionError(f"Unexpected command: {argv}")
    monkeypatch.setattr(tool, "command", simulated_command)
    report = tool.run_lifecycle(fake_setup, tmp_path / "workspace")
    names = [e["name"] for e in report["events"]]
    assert names[:3] == ["reject occupied custom destination",
                         "fresh per-user installation",
                         "reject second installation"]
    assert all(e["passed"] for e in report["events"][:3])
    assert report["passed"] is False  # Mock setup creates no real uninstaller.
    assert sum(any("/DIR=" in part and part.endswith("fresh-install") for part in cmd)
               for cmd in calls) == 2


def test_vm_failure_keeps_workspace_and_writes_report(tmp_path, monkeypatch):
    """No actual installer: simulated VM exception must leave diagnostic evidence."""
    setup = tmp_path / "mock.exe"
    setup.write_bytes(b"MZ VM mock")
    monkeypatch.setattr(tool, "detect_vm", lambda: (True, "synthetic test virtual machine"))
    monkeypatch.setattr(tool.tempfile, "mkdtemp",
                        lambda prefix: str(tmp_path / "vm-workspace"))
    # Simulate the freshly allocated VM workspace without changing the host OS.
    (tmp_path / "vm-workspace").mkdir()
    def fail_with_evidence(setup_path, base):
        base.mkdir()
        (base / "failed-setup.log").write_text("mock failure evidence")
        raise RuntimeError("simulated install failure")
    monkeypatch.setattr(tool, "run_lifecycle", fail_with_evidence)
    report = tmp_path / "vm-report.json"
    result = tool.main(["--setup", str(setup), "--sha256", tool.sha256(setup),
                        "--report", str(report), "--execute-in-disposable-vm",
                        "--acknowledge-vm-snapshot", "DISPOSABLE-VM-SNAPSHOT-CONFIRMED"])
    assert result == 1
    record = json.loads(report.read_text())
    assert record["executed"] is True
    assert record["lifecycle"]["passed"] is False
    assert "simulated install failure" in record["lifecycle"]["error"]
    assert (tmp_path / "vm-workspace/lifecycle/failed-setup.log").read_text() == "mock failure evidence"
