"""Uninstaller must never modify a path, even when directly invoked."""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("kasa_uninstall_plan", ROOT / "scripts/plan_macos_uninstall.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fixture(tmp_path):
    lib = tmp_path / "lib/kasa-preview"
    lib.mkdir(parents=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "kasa").symlink_to("../lib/kasa-preview/kasa")
    (lib / "kasa").write_text("launcher")
    (lib / "kasa-native").write_text("binary")
    (lib / "build-info.txt").write_text(
        "Source commit: " + "a" * 40 + "\n"
        "Installer build version: 0.4.0.194\n"
        "Release: 0.4.0-alpha\n")
    return lib


def test_plan_preserves_installed_and_user_files(tmp_path, capsys):
    lib = fixture(tmp_path)
    project = tmp_path / "my_program.kasa"
    project.write_text('ka "hello"\n')
    tool.remove(tmp_path, "0.4.0.194", execute=False)
    assert "READ-ONLY" in capsys.readouterr().out
    assert (lib / "kasa-native").is_file()
    assert project.read_text() == 'ka "hello"\n'


def test_execute_does_not_unlink_even_when_called_directly(tmp_path):
    lib = fixture(tmp_path)
    try:
        tool.remove(tmp_path, "0.4.0.194", execute=True)
    except ValueError as exc:
        assert "intentionally disabled" in str(exc)
    else:
        raise AssertionError("Execute must remain disabled")
    assert (lib / "kasa-native").is_file()
    assert (tmp_path / "bin/kasa").is_symlink()


def test_extra_content_blocks_plan(tmp_path):
    lib = fixture(tmp_path)
    (lib / "other-tool").write_text("do not remove")
    try:
        tool.remove(tmp_path, "0.4.0.194", execute=False)
    except ValueError as exc:
        assert "Unexpected files" in str(exc)
    else:
        raise AssertionError("Unexpected files must be protected")


def test_alien_symlink_blocks_plan(tmp_path):
    fixture(tmp_path)
    (tmp_path / "bin/kasa").unlink()
    (tmp_path / "bin/kasa").symlink_to("other")
    try:
        tool.remove(tmp_path, "0.4.0.194", execute=False)
    except ValueError as exc:
        assert "ownership audit" in str(exc)
    else:
        raise AssertionError("Alien symlink must be protected")
