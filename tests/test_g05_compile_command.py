"""G0.5 opt-in compilation front-end safety and portable success tests."""
from __future__ import annotations

import subprocess
from pathlib import Path
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import compile_g05_modules as compiler
    from compile_g05_modules import CompileError, DEFAULT_NATIVE, compile_modules
finally:
    sys.path.remove(str(ROOT / "scripts"))


@pytest.fixture
def output_path():
    target = ROOT / "build" / "g05-compiled" / ("test-" + uuid.uuid4().hex + ".kbc")
    yield target
    target.unlink(missing_ok=True)


def _write(tmp_path, source):
    path = tmp_path / "input.kasa"
    path.write_text(source, encoding="utf-8")
    return path


def test_rejects_missing_module_without_publishing(tmp_path, output_path):
    source = _write(tmp_path, "fa unknown firi stdlib: x\nka x.f(1)\n")
    with pytest.raises(Exception, match="Unknown catalog module"):
        compile_modules(source, output_path)
    assert not output_path.exists()


def test_rejects_unrelated_output_directory(tmp_path):
    source = _write(tmp_path, "fa math firi stdlib: m\nka 1\n")
    with pytest.raises(CompileError, match="build/g05-compiled"):
        compile_modules(source, tmp_path / "out.kbc")
    assert not (tmp_path / "out.kbc").exists()


def test_rejects_existing_output_without_mutation(tmp_path, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(b"DO NOT MODIFY")
    source = _write(tmp_path, "fa math firi stdlib: m\nka 1\n")
    with pytest.raises(CompileError, match="overwrite"):
        compile_modules(source, output_path)
    assert output_path.read_bytes() == b"DO NOT MODIFY"


def test_rejects_unlinked_source_symlink(tmp_path, output_path):
    original = _write(tmp_path, "fa math firi stdlib: m\nka 1\n")
    alias = tmp_path / "alias.kasa"
    try:
        alias.symlink_to(original)
    except (OSError, NotImplementedError):
        pytest.skip("This Windows account cannot create symlinks")
    with pytest.raises(CompileError, match="regular source"):
        compile_modules(alias, output_path)
    assert not output_path.exists()


def test_source_link_rejection_without_os_symlink_privileges(tmp_path, output_path, monkeypatch):
    """Exercise the actual guard even when Windows prohibits symlink creation.

    This is a simulated path-link check, not a substitute for the real
    filesystem symlink test (which continues to skip when unavailable).
    """
    original = _write(tmp_path, "fa math firi stdlib: m\\nka 1\\n")
    original_guard = compiler._linked_directory

    def linked_for_test(path):
        if path == original:
            return True
        return original_guard(path)

    monkeypatch.setattr(compiler, "_linked_directory", linked_for_test)
    with pytest.raises(CompileError, match="regular source"):
        compile_modules(original, output_path)
    assert not output_path.exists()


@pytest.mark.skipif(not DEFAULT_NATIVE.is_file(),
                    reason="Native build required; run verify_local parity first")
def test_compile_verified_kbc1_then_run_without_source(tmp_path, output_path):
    source = _write(
        tmp_path,
        "fa math firi stdlib: m\n"
        "fa collections firi stdlib: c\n"
        "ka m.kasa_sum([10, 20, 30])\n"
        "ka c.kasa_contains([1, 2, 3], 2)\n",
    )
    assert compile_modules(source, output_path) == output_path
    assert output_path.read_bytes().startswith(b"KBC1")
    source.unlink()
    result = subprocess.run(
        [str(DEFAULT_NATIVE), "run-bytecode", str(output_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "60\nnokware\n"
    assert result.stderr == ""
