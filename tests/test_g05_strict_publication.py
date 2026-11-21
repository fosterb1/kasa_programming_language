"""Opt-in directory-handle KBC publication tests.

Runs on POSIX when dir_fd operations exist. Windows verifies fail-closed
unavailability without requiring symlink privileges or a native compiler.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import compile_g05_modules as compiler
finally:
    sys.path.remove(str(ROOT / "scripts"))


@pytest.fixture
def fake_compiler(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    folder = root / "build" / "g05-compiled"
    folder.mkdir(parents=True)
    app = tmp_path / "valid.kasa"
    app.write_text("fa math firi stdlib: m\nka 1\n", encoding="utf-8")
    native = tmp_path / "native-stub"
    native.write_bytes(b"fake native executable")
    monkeypatch.setattr(compiler, "link_source",
                        lambda source, *, root, filename: "ka 1\n")

    def stub(executable, mode, file, output=None):
        if mode == "compile":
            output.write_bytes(b"KBC1" + b"\x00" * 32)
        return ""

    monkeypatch.setattr(compiler, "_invoke", stub)
    return root, folder, app, native


def test_windows_strict_mode_refuses_before_any_source_read(tmp_path):
    if compiler._strict_publication_supported():
        pytest.skip("Platform provides POSIX directory-handle publication")
    missing = tmp_path / "missing.kasa"
    output = tmp_path / "missing.kbc"
    with pytest.raises(compiler.CompileError, match="Strict publication unavailable"):
        compiler.compile_modules(missing, output, strict_publication=True)
    assert not output.exists()


@pytest.mark.skipif(not compiler._strict_publication_supported(),
                    reason="Requires POSIX dir_fd and O_NOFOLLOW")
def test_handle_bound_success(fake_compiler):
    root, folder, app, native = fake_compiler
    target = folder / "success.kbc"
    assert compiler.compile_modules(
        app, target, native=native, root=root, strict_publication=True
    ) == target
    assert target.read_bytes() == b"KBC1" + b"\x00" * 32


@pytest.mark.skipif(not compiler._strict_publication_supported(),
                    reason="Requires POSIX dir_fd and O_NOFOLLOW")
def test_handle_mode_exclusive_creation_preserves_existing_file(fake_compiler):
    root, folder, app, native = fake_compiler
    target = folder / "existing.kbc"
    target.write_bytes(b"ORIGINAL")
    with pytest.raises(compiler.CompileError, match="overwrite"):
        compiler.compile_modules(
            app, target, native=native, root=root, strict_publication=True
        )
    assert target.read_bytes() == b"ORIGINAL"


@pytest.mark.skipif(not compiler._strict_publication_supported(),
                    reason="Requires POSIX dir_fd and O_NOFOLLOW")
def test_swapped_directory_after_last_path_check_refuses_without_publication(
    fake_compiler, monkeypatch
):
    root, folder, app, native = fake_compiler
    replacement = folder.parent / "original-moved"
    target = folder / "must-not-exist.kbc"
    original_check = compiler._directory_fingerprint
    calls = 0

    def swap_just_after_last_path_check(root_arg, folder_arg):
        nonlocal calls
        calls += 1
        identity = original_check(root_arg, folder_arg)
        if calls == 2:
            folder.rename(replacement)
            folder.mkdir()
        return identity

    monkeypatch.setattr(compiler, "_directory_fingerprint",
                        swap_just_after_last_path_check)
    with pytest.raises(compiler.CompileError, match="identity changed"):
        compiler.compile_modules(
            app, target, native=native, root=root, strict_publication=True
        )
    assert calls == 2
    assert not target.exists()
    assert not (replacement / target.name).exists()
