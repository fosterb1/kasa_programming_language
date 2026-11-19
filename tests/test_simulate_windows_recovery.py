"""Phase 6F.4 recovery simulation: only isolated files, never actual installations."""
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

SRC = Path(__file__).resolve().parents[1] / "scripts/simulate_windows_recovery.py"
spec = importlib.util.spec_from_file_location("kasa_restore_simulation", SRC)
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)

def fixture_snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    binary = b"MZ" + b"KASA" * 100
    (source / "kasa-native.exe").write_bytes(binary)
    (source / "kasa.cmd").write_bytes(b"@echo off\r\n")
    (source / "README.txt").write_bytes(b"sample")
    (source / "kasa-install-identity.txt").write_bytes((sim.snapshot_lib.IDENTITY + "\r\n").encode())
    (source / "manifest.json").write_text(json.dumps({
        "release": "0.4.0-alpha", "platform": "Windows", "architecture": "x64",
        "source_commit": "a"*40, "binary_sha256": sim.snapshot_lib.digest(binary)
    }))
    archive = tmp_path / "baseline.zip"
    sim.snapshot_lib.snapshot(source, archive)
    return source, archive

def test_success_rebuilds_all_payload_files(tmp_path):
    src, archive = fixture_snapshot(tmp_path)
    original = {f.name: f.read_bytes() for f in src.iterdir()}
    destination = tmp_path / "sim" / "new-run"
    result = sim.simulate(archive, destination)
    assert result["passed"] is True
    assert result["restore_authorized"] is False
    assert result["installed_files_touched"] is False
    assert set(result["files_written"]) == sim.snapshot_lib.FILES
    assert json.loads((destination/"simulation-report.json").read_text())["passed"]
    assert all((destination/"reconstructed-payload"/name).read_bytes() == data
               for name, data in original.items())
    assert all((src/name).read_bytes() == data for name, data in original.items())

@pytest.mark.parametrize("stop", [1, 3, 5])
def test_injected_interruption_retains_partial_evidence(tmp_path, stop):
    src, archive = fixture_snapshot(tmp_path)
    target = tmp_path / "sim" / "interrupted"
    result = sim.simulate(archive, target, fail_after=stop)
    assert result["passed"] is False
    assert len(result["files_written"]) == stop
    assert "Injected interruption" in result["error"]
    assert (target / "simulation-report.json").exists()
    assert len(list((target/"reconstructed-payload").iterdir())) == stop
    assert len(list(src.iterdir())) == 5

def test_existing_workspace_refused_preserves_user_file(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    target = tmp_path / "existing"
    target.mkdir()
    sentinel = target / "important.kasa"
    sentinel.write_text("do not touch")
    with pytest.raises(sim.SimulationError, match="already exists"):
        sim.simulate(archive, target)
    assert sentinel.read_text() == "do not touch"

def test_corrupt_snapshot_refused_before_workspace_created(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    archive.with_name(archive.name+".sha256").write_text("0"*64 + "  " + archive.name)
    target = tmp_path/"new"
    with pytest.raises(sim.snapshot_lib.SnapshotError, match="checksum"):
        sim.simulate(archive, target)
    assert not target.exists()

def test_corrupt_zip_file_refused(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    archive.write_bytes(b"corrupted")
    archive.with_name(archive.name+".sha256").write_text(
        sim.snapshot_lib.digest(archive.read_bytes()) + "  " + archive.name)
    with pytest.raises(sim.snapshot_lib.SnapshotError):
        sim.simulate(archive, tmp_path/"new")
    assert not (tmp_path/"new").exists()

def test_fails_when_snapshot_dir_is_workspace(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    with pytest.raises(sim.SimulationError, match="overlaps"):
        sim.simulate(archive, archive.parent)

def test_invalid_fault_injection_rejected_without_workspace(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    for bad in (-1, 0, 6, True):
        target = tmp_path / "fresh"
        with pytest.raises(sim.SimulationError):
            sim.simulate(archive, target, fail_after=bad)
        assert not target.exists()

def test_cli_rejects_outside_workspace(tmp_path):
    _, archive = fixture_snapshot(tmp_path)
    target = tmp_path / "unapproved"
    assert sim.main(["--snapshot", str(archive), "--workspace", str(target)]) == 2
    assert not target.exists()
