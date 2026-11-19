"""Phase 5B package design tests. No system installer is executed."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("kasa_macos_pkg", SCRIPTS / "package_macos_installer.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def test_preinstall_refuses_unknown_command_owners():
    assert 'if [ -L "$link" ]' in tool.PREINSTALL
    assert 'target=$(readlink "$link")' in tool.PREINSTALL
    assert 'Refusing to replace existing' in tool.PREINSTALL
    assert tool.PACKAGE_LINK == "../lib/kasa-preview/kasa"
    assert "rm -f" not in tool.PREINSTALL


def test_install_identifier_and_path_are_separate_from_older_user_local_preview():
    assert tool.PACKAGE_ID == "org.kasalang.kasa.preview"
    assert "usr/local/lib/kasa-preview" in tool.build.__code__.co_consts


def test_non_macos_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(tool.platform, "system", lambda: "Linux")
    try:
        tool.build(tmp_path / "nothing", tmp_path / "out")
    except ValueError as e:
        assert "macOS" in str(e)
    else:
        raise AssertionError("NonmacOS must be rejected")


def test_dirty_source_refuses_package(monkeypatch):
    outputs = iter([
        "a" * 40,
        "287",
        " M native/src/vm.cpp",
    ])
    monkeypatch.setattr(tool, "checked", lambda command, **kwargs: type("Result", (), {"stdout": next(outputs)})())
    try:
        tool.version_from_git()
    except ValueError as e:
        assert "dirty" in str(e)
    else:
        raise AssertionError("Dirty source must not be labeled release-ready")


def test_git_commit_count_produces_incrementing_installer_version(monkeypatch):
    def fake(cmd, **kwargs):
        if cmd[1:3] == ["rev-parse", "HEAD"]:
            out = "a" * 40
        elif cmd[1:3] == ["rev-list", "--count"]:
            out = "287"
        else:
            out = ""
        return type("Result", (), {"stdout": out})()
    monkeypatch.setattr(tool, "checked", fake)
    assert tool.version_from_git() == ("0.4.0.287", "a" * 40)
