"""Check bytecode conformance test orchestration using a disposable fake native CLI.

This tests test-harness failure handling; it does NOT verify the Kasa compiler/VM.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "native" / "tests" / "conformance.py"

# The fake executable uses a POSIX shebang, not a Windows .exe launcher.
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX fake executable fixture")


@pytest.fixture
def driver(monkeypatch, tmp_path):
    # conformance.py reads and trims sys.argv at import time; isolate that side
    # effect from pytest and let the module resolve its dependencies normally.
    monkeypatch.setattr(sys, "argv", [str(CONFORMANCE)])
    spec = importlib.util.spec_from_file_location("kasa_native_parity_driver_test", CONFORMANCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    fake = tmp_path / "fake-kasa-native"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib, sys\n"
        "a = sys.argv[1:]\n"
        "if a[0] == 'compile':\n"
        "    source = pathlib.Path(a[1]).read_text(encoding='utf-8')\n"
        "    if source.startswith('BAD_SOURCE'):\n"
        "        print('SyntaxError: bad input', file=sys.stderr); sys.exit(1)\n"
        "    pathlib.Path(a[3]).write_text(source, encoding='utf-8')\n"
        "    print('compiled')\n"
        "elif a[0] == 'check-bytecode':\n"
        "    blob = pathlib.Path(a[1]).read_text(encoding='utf-8')\n"
        "    if blob.startswith('BAD_BYTECODE'):\n"
        "        print('Invalid KBC bytecode', file=sys.stderr); sys.exit(1)\n"
        "elif a[0] == 'run-bytecode':\n"
        "    blob = pathlib.Path(a[1]).read_text(encoding='utf-8')\n"
        "    if blob.startswith('RUNTIME_ERROR'):\n"
        "        print('TypeError: test', file=sys.stderr); sys.exit(1)\n"
        "    print('result:' + sys.stdin.read().strip())\n"
        "else:\n"
        "    sys.exit(40)\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    monkeypatch.setattr(module, "BINARY", fake)
    return module


def test_compile_check_run_and_input_are_sequential(driver):
    compile_result, check_result, run_result = driver.run_native_serialized("ka 10", "Akosua\n")
    assert compile_result.returncode == 0
    assert check_result is not None and check_result.returncode == 0
    assert run_result is not None and run_result.returncode == 0
    assert run_result.stdout == "result:Akosua\n"


def test_failed_compile_never_validates_or_runs(driver):
    compile_result, check_result, run_result = driver.run_native_serialized("BAD_SOURCE")
    assert compile_result.returncode == 1
    assert "SyntaxError" in compile_result.stderr
    assert check_result is None and run_result is None


def test_failed_bytecode_validation_never_runs(driver):
    compile_result, check_result, run_result = driver.run_native_serialized("BAD_BYTECODE")
    assert compile_result.returncode == 0
    assert check_result is not None and check_result.returncode == 1
    assert run_result is None


def test_runtime_failure_is_preserved(driver):
    compile_result, check_result, run_result = driver.run_native_serialized("RUNTIME_ERROR")
    assert compile_result.returncode == 0
    assert check_result is not None and check_result.returncode == 0
    assert run_result is not None and run_result.returncode == 1
    assert "TypeError" in run_result.stderr
