"""Recovery snapshot tests use synthetic files; never launch or restore an installer."""
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

FILE = Path(__file__).resolve().parents[1] / "scripts/windows_recovery_snapshot.py"
spec = importlib.util.spec_from_file_location("kasa_snapshot", FILE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def payload(tmp_path):
    folder = tmp_path / "source"
    folder.mkdir()
    binary = b"MZ" + b"Kasa" * 100
    (folder / "kasa-native.exe").write_bytes(binary)
    (folder / "kasa.cmd").write_bytes(b"@echo off\r\n")
    (folder / "README.txt").write_bytes(b"developer-only")
    (folder / "kasa-install-identity.txt").write_text(tool.IDENTITY + "\n")
    (folder / "manifest.json").write_text(json.dumps({
        "release": "0.4.0-alpha", "platform": "Windows",
        "architecture": "x64", "source_commit": "a" * 40,
        "binary_sha256": tool.digest(binary),
        "installer_build_version": "0.4.0.203",
    }))
    return folder


def test_create_and_verify_round_trip_without_source_mutation(tmp_path):
    src = payload(tmp_path)
    before = {p.name: p.read_bytes() for p in src.iterdir()}
    output = tmp_path / "snapshots" / "test.zip"
    created = tool.snapshot(src, output)
    assert created["verified"]
    assert not created["index"]["restore_authorized"]
    assert not created["index"]["installation_ownership_verified"]
    assert not created["index"]["signed"]
    assert created["index"]["installer_build_version"] == "0.4.0.203"
    assert tool.verify(output)["archive_sha256"] == created["archive_sha256"]
    assert output.with_name(output.name + ".sha256").exists()
    assert {p.name: p.read_bytes() for p in src.iterdir()} == before


def test_refuse_overwrite_existing_snapshot(tmp_path):
    src = payload(tmp_path)
    out = tmp_path / "same.zip"
    tool.snapshot(src, out)
    first = out.read_bytes()
    with pytest.raises(tool.SnapshotError, match="overwrite"):
        tool.snapshot(src, out)
    assert out.read_bytes() == first


def test_refuse_unknown_user_file_and_preserve(tmp_path):
    src = payload(tmp_path)
    foreign = src / "important.kasa"
    foreign.write_text("protect this!")
    with pytest.raises(tool.SnapshotError, match="Unexpected"):
        tool.snapshot(src, tmp_path / "snapshot.zip")
    assert foreign.read_text() == "protect this!"
    assert not (tmp_path / "snapshot.zip").exists()


def test_refuse_modified_binary_digest(tmp_path):
    src = payload(tmp_path)
    (src / "kasa-native.exe").write_bytes(b"changed")
    with pytest.raises(tool.SnapshotError, match="SHA-256"):
        tool.snapshot(src, tmp_path / "bad.zip")


def test_refuse_wrong_identity_marker(tmp_path):
    src = payload(tmp_path)
    (src / "kasa-install-identity.txt").write_text("alien\n")
    with pytest.raises(tool.SnapshotError, match="marker"):
        tool.snapshot(src, tmp_path / "bad.zip")


def test_refuse_source_symlink(tmp_path):
    src = payload(tmp_path)
    link = tmp_path / "alias"
    try:
        link.symlink_to(src, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation unavailable on this Windows configuration")
    with pytest.raises(tool.SnapshotError, match="real existing"):
        tool.snapshot(link, tmp_path / "bad.zip")


def test_refuse_corrupt_checksum(tmp_path):
    src = payload(tmp_path)
    out = tmp_path / "good.zip"
    tool.snapshot(src, out)
    out.with_name(out.name + ".sha256").write_text("0" * 64 + "  " + out.name)
    with pytest.raises(tool.SnapshotError, match="checksum mismatch"):
        tool.verify(out)


def test_refuse_modified_archive_payload_even_if_checksum_recomputed(tmp_path):
    src = payload(tmp_path)
    out = tmp_path / "good.zip"
    tool.snapshot(src, out)
    with zipfile.ZipFile(out) as z:
        files = {n: z.read(n) for n in z.namelist()}
    files["kasa-payload/kasa.cmd"] = b"malicious replacement"
    with zipfile.ZipFile(out, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    out.with_name(out.name + ".sha256").write_text(tool.digest(out.read_bytes()) + "  " + out.name)
    with pytest.raises(tool.SnapshotError, match="tampered"):
        tool.verify(out)


def test_refuse_duplicate_zip_members(tmp_path):
    src = payload(tmp_path)
    out = tmp_path / "good.zip"
    tool.snapshot(src, out)
    with zipfile.ZipFile(out, "a") as z:
        z.writestr("kasa-payload/kasa.cmd", b"duplicate")
    out.with_name(out.name + ".sha256").write_text(tool.digest(out.read_bytes()) + "  " + out.name)
    with pytest.raises(tool.SnapshotError, match="duplicate"):
        tool.verify(out)


def test_refuse_destination_inside_source(tmp_path):
    src = payload(tmp_path)
    with pytest.raises(tool.SnapshotError, match="outside"):
        tool.snapshot(src, src / "snapshot.zip")
    assert not (src / "snapshot.zip").exists()


def test_verify_does_not_restore_or_modify_source(tmp_path):
    src = payload(tmp_path)
    out = tmp_path / "snapshot.zip"
    tool.snapshot(src, out)
    (src / "kasa-native.exe").unlink()
    assert tool.verify(out)["verified"]
    assert not (src / "kasa-native.exe").exists()


def test_cli_create_then_verify(tmp_path, capsys):
    src = payload(tmp_path)
    out = tmp_path / "snap.zip"
    assert tool.main(["--create-from", str(src), "--output", str(out)]) == 0
    assert tool.main(["--verify", str(out)]) == 0
    assert '"verified": true' in capsys.readouterr().out


@pytest.mark.parametrize("newline", [b"\\n", b"\\r\\n"])
def test_identity_marker_line_endings_are_portable(tmp_path, newline):
    src = payload(tmp_path)
    identity = (tool.IDENTITY.encode("ascii") + newline)
    (src / "kasa-install-identity.txt").write_bytes(identity)
    out = tmp_path / "snapshot.zip"
    created = tool.snapshot(src, out)
    assert created["verified"]
    assert tool.verify(out)["verified"]
    with zipfile.ZipFile(out) as archive:
        assert archive.read("kasa-payload/kasa-install-identity.txt") == identity


@pytest.mark.parametrize("bad", [b"", b"org.kasalang.kasa.windows.preview.v1",
                                  b"org.kasalang.kasa.windows.preview.v1\\n\\n",
                                  b"org.kasalang.kasa.windows.preview.v1 \\n",
                                  b"org.kasalang.kasa.windows.preview.v1\\r"])
def test_reject_malformed_marker_even_with_whitespace(tmp_path, bad):
    src = payload(tmp_path)
    (src / "kasa-install-identity.txt").write_bytes(bad)
    with pytest.raises(tool.SnapshotError, match="Identity marker"):
        tool.snapshot(src, tmp_path / "nope.zip")
