"""G0.5a read-only prelink gate. No native import implementation is claimed."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from preflight_native_modules import preflight
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa.core import KasaError


def test_two_pinned_modules_and_members_preflight_without_exec_or_output():
    plan = preflight(
        "fa math firi stdlib: m\n"
        "fa collections firi stdlib: c\n"
        "ka m.kasa_sum([10, 20, 30])\n"
        "ka c.kasa_contains([1, 2], 2)\n"
    )
    assert plan["mode"] == "native_prelink_preflight_only"
    assert plan["load_order"] == ["collections", "math"]
    assert plan["imports"] == [
        {"module": "math", "alias": "m"},
        {"module": "collections", "alias": "c"},
    ]
    assert [(ref["alias"], ref["export"]) for ref in plan["references"]] == [
        ("m", "kasa_sum"), ("c", "kasa_contains")
    ]
    assert plan["capabilities_granted"] == []
    assert plan["emits_source"] is False
    assert plan["emits_bytecode"] is False


@pytest.mark.parametrize(("source", "category", "message", "line"), [
    ("fa missing firi stdlib: m\nka 1\n", "ModuleError", "Unknown catalog module", 1),
    ("fa math firi stdlib: m\nfa math firi stdlib: n\nka 1\n",
     "ModuleError", "more than once", 2),
    ("fa math firi stdlib: m\nfa collections firi stdlib: m\nka 1\n",
     "ModuleError", "alias reused", 2),
    ("fa math firi external: m\nka 1\n", "SyntaxError", "pinned stdlib", 1),
    ("fa math firi stdlib: m\nka m.private(1)\n", "NameError", "does not export", 2),
    ("fa math firi stdlib: m\nka x.kasa_sum([1])\n",
     "NameError", "Unknown module alias", 2),
    ("fa math firi stdlib: m\nma m = 3\n", "NameError", "cannot be reassigned", 2),
    ("fa math firi stdlib: m\nka 1\nfa collections firi stdlib: c\n",
     "SyntaxError", "precede statements", 3),
    ("fa math firi stdlib: m\ndwumadie f(m)\n sanma m\nawiei\n",
     "NameError", "cannot be redeclared", 2),
    ("ka 1\n", "SyntaxError", "At least one module", 1),
])
def test_prelink_fail_closed(source, category, message, line):
    with pytest.raises(KasaError) as caught:
        preflight(source)
    assert caught.value.category == category
    assert message.lower() in str(caught.value).lower()
    assert caught.value.token.line == line


def test_program_strings_preserved_in_preflight():
    result = preflight('fa math firi stdlib: m\nka "m.kasa_sum([100])"\n')
    assert result["references"] == []


def test_nested_member_calls_accounted_without_running():
    result = preflight(
        "fa math firi stdlib: m\n"
        "dwumadie demo(x)\n"
        "    sanma m.kasa_sum([x, m.kasa_abs(-2)])\n"
        "awiei\n"
    )
    assert [ref["export"] for ref in result["references"]] == ["kasa_sum", "kasa_abs"]


def test_no_output_artifact_is_written(tmp_path):
    before = set(tmp_path.iterdir())
    preflight("fa math firi stdlib: m\nka m.kasa_sum([1])\n")
    assert set(tmp_path.iterdir()) == before
