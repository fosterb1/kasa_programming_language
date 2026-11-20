"""Controlled output-directory replacement tests for G0.5 compilation.

These tests use only pytest temporary folders and a simulated native driver.
They do not rename, link, or mutate the actual repository's build folder.
"""
from __future__ import annotations

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
def isolated_compiler(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    output_dir = root / "build" / "g05-compiled"
    output_dir.mkdir(parents=True)
    app = tmp_path / "source.kasa"
    app.write_text("fa math firi stdlib: m\nka 1\n", encoding="utf-8")
    native = tmp_path / "kasa-native.exe"
    native.write_bytes(b"mock native executable for path tests only")
    monkeypatch.setattr(compiler, "link_source",
                        lambda source, *, root, filename: "ka 1\n")

    def native_stub(executable, mode, file, output=None):
        if mode == "compile":
            assert output is not None
            output.write_bytes(b"KBC1" + b"\x00" * 32)
        return ""

    monkeypatch.setattr(compiler, "_invoke", native_stub)
    return root, output_dir, app, native


def test_unmodified_output_directory_allows_compilation(isolated_compiler):
    root, output_dir, app, native = isolated_compiler
    output = output_dir / "trusted.kbc"
    assert compiler.compile_modules(app, output, native=native, root=root) == output
    assert output.read_bytes() == b"KBC1" + b"\x00" * 32


def test_directory_replaced_during_compilation_blocks_publish(
    isolated_compiler, monkeypatch
):
    root, output_dir, app, native = isolated_compiler
    output = output_dir / "must-not-publish.kbc"
    displaced = root / "build" / "displaced-original"
    original_native_stub = compiler._invoke
    swapped = False

    def swap_after_bytecode_verification(executable, mode, file, output=None):
        nonlocal swapped
        result = original_native_stub(executable, mode, file, output)
        if mode == "check-bytecode":
            assert not swapped
            output_dir.rename(displaced)
            output_dir.mkdir()
            swapped = True
        return result

    monkeypatch.setattr(compiler, "_invoke", swap_after_bytecode_verification)
    with pytest.raises(compiler.CompileError, match="identity changed"):
        compiler.compile_modules(app, output, native=native, root=root)
    assert swapped
    assert not output.exists()
    assert not (displaced / output.name).exists()


def test_output_parent_replaced_during_compilation_blocks_publish(
    isolated_compiler, monkeypatch
):
    root, output_dir, app, native = isolated_compiler
    output = output_dir / "parent-race.kbc"
    build = root / "build"
    displaced = root / "displaced-build"
    original_native_stub = compiler._invoke

    def swap_parent(executable, mode, file, output=None):
        result = original_native_stub(executable, mode, file, output)
        if mode == "check-bytecode":
            build.rename(displaced)
            build.mkdir()
            (build / "g05-compiled").mkdir()
        return result

    monkeypatch.setattr(compiler, "_invoke", swap_parent)
    with pytest.raises(compiler.CompileError, match="identity changed"):
        compiler.compile_modules(app, output, native=native, root=root)
    assert not output.exists()
    assert not (displaced / "g05-compiled" / output.name).exists()
