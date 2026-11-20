"""G0.5 repeatability and input-boundary checks for the opt-in compiler.

This gate intentionally FAILS if two independent builds emit different KBC1
bytes. Do not normalize or edit the bytecode to conceal reproducibility bugs.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from compile_g05_modules import (
        CompileError, DEFAULT_NATIVE, MAX_INPUT_BYTES, compile_modules,
    )
    from link_kasa_modules_hygienic import link_source
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa.core import KasaError

VALID = (
    "fa math firi stdlib: m\n"
    "fa collections firi stdlib: c\n"
    "ka m.kasa_sum([10, 20, 30])\n"
    "ka c.kasa_contains([1, 2], 2)\n"
)


@pytest.fixture
def target_factory():
    files = []

    def make():
        target = ROOT / "build" / "g05-compiled" / ("repeat-" + uuid.uuid4().hex + ".kbc")
        files.append(target)
        return target

    yield make
    for path in files:
        path.unlink(missing_ok=True)


def _app(tmp_path: Path, content: str) -> Path:
    app = tmp_path / "test.kasa"
    app.write_text(content, encoding="utf-8")
    return app


def test_linked_source_repeatable_with_same_filename():
    first = link_source(VALID, filename="repeat.kasa")
    second = link_source(VALID, filename="repeat.kasa")
    assert first == second
    assert hashlib.sha256(first.encode("utf-8")).digest() == hashlib.sha256(
        second.encode("utf-8")
    ).digest()


@pytest.mark.skipif(not DEFAULT_NATIVE.is_file(), reason="Native must be built before gate")
def test_identical_kbc1_from_two_independent_compilations(tmp_path, target_factory):
    app = _app(tmp_path, VALID)
    first, second = target_factory(), target_factory()
    compile_modules(app, first)
    compile_modules(app, second)
    a, b = first.read_bytes(), second.read_bytes()
    assert a[:4] == b[:4] == b"KBC1"
    assert hashlib.sha256(a).digest() == hashlib.sha256(b).digest(), (
        "KBC1 output is not reproducible across two temporary linked builds"
    )
    assert a == b
    result = subprocess.run(
        [str(DEFAULT_NATIVE), "run-bytecode", str(second)],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "60\nnokware\n"
    assert result.stderr == ""


def test_oversized_source_fails_before_publication(tmp_path, target_factory):
    source = _app(
        tmp_path,
        "fa math firi stdlib: m\n" + ("# filler for byte budget\n" * 2800),
    )
    assert source.stat().st_size > MAX_INPUT_BYTES
    output = target_factory()
    with pytest.raises(CompileError, match="source-size budget"):
        compile_modules(source, output)
    assert not output.exists()


@pytest.mark.parametrize("source,diagnostic", [
    ("fa math firi stdlib: x\nfa math firi stdlib: y\nka 1\n", "more than once"),
    ("fa math firi stdlib: m\nka m.not_public(1)\n", "does not export"),
    ("fa math firi stdlib: m\nma __kasa_g05_math_kasa_sum = 1\n", "reserved internal"),
    ("fa math firi stdlib: m\nka 1\nfa collections firi stdlib: c\n", "precede statements"),
])
def test_invalid_imports_never_publish(tmp_path, target_factory, source, diagnostic):
    app = _app(tmp_path, source)
    output = target_factory()
    with pytest.raises((KasaError, CompileError), match=diagnostic):
        compile_modules(app, output)
    assert not output.exists()


def test_missing_native_does_not_publish(tmp_path, target_factory):
    app = _app(tmp_path, VALID)
    output = target_factory()
    with pytest.raises(CompileError, match="Native executable missing"):
        compile_modules(app, output, native=tmp_path / "not-a-native.exe")
    assert not output.exists()
