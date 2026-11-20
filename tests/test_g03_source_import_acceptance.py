"""G0.3 opt-in source-import acceptance cases (not stable Kasa syntax).

Run with: python -m pytest -q tests/test_g03_source_import_acceptance.py
These tests intentionally exercise the Python-only experimental runner; they
do not certify browser JS, C++ native, KBC, or standard CLI import support.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from kasa import parse
from kasa.core import KasaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from run_kasa_modules_experimental import execute_module_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def test_two_reviewed_modules_use_namespaces_without_global_leakage():
    output = io.StringIO()
    runtime = execute_module_source(
        "fa math firi stdlib: m\n"
        "fa collections firi stdlib: c\n"
        "ka m.kasa_sum([10, 20, 30])\n"
        "ka c.kasa_contains([10, 20, 30], 20)\n",
        stdout=output,
    )
    assert output.getvalue() == "60\nnokware\n"
    assert "m" not in runtime.globals.values
    assert "c" not in runtime.globals.values
    assert "kasa_sum" not in runtime.globals.values
    assert "kasa_contains" not in runtime.globals.values


@pytest.mark.parametrize(
    ("source", "category", "message"),
    [
        ("fa missing firi stdlib: m\nka 1\n", "ModuleError", "Unknown catalog module"),
        ("fa math firi stdlib: m\nfa collections firi stdlib: m\nka 1\n", "ModuleError", "alias reused"),
        ("fa math firi external: m\nka 1\n", "SyntaxError", "Only the pinned stdlib"),
        ("fa math firi stdlib: m\nka m.not_exported(1)\n", "NameError", "does not export"),
        ("fa math firi stdlib: m\nka unknown.kasa_sum([1])\n", "NameError", "Unknown module alias"),
        ("fa math firi stdlib: m\nka 1\nma m = 2\n", "NameError", "Module alias cannot"),
    ],
)
def test_invalid_import_programs_fail_before_printing(source, category, message):
    output = io.StringIO()
    with pytest.raises(KasaError, match=message) as error:
        execute_module_source(source, stdout=output)
    assert error.value.category == category
    assert output.getvalue() == ""


def test_stable_parser_still_rejects_unapproved_import_syntax():
    with pytest.raises(KasaError, match="SyntaxError"):
        parse("fa math firi stdlib: m\nka m.kasa_sum([1, 2])\n")


def test_valid_library_math_cannot_run_beyond_step_budget():
    with pytest.raises(KasaError, match="Execution limit"):
        execute_module_source(
            "fa math firi stdlib: m\n"
            "mpɛn 100\n"
            "    ka m.kasa_sum([1, 2, 3])\n"
            "awiei\n",
            stdout=io.StringIO(),
            max_steps=25,
        )
