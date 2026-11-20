"""Integration tests for a catalog-verified module-aware Python runtime."""
import importlib.util
import io
from pathlib import Path
import sys

import pytest

from kasa import parse
from kasa.core import KasaError, Node
from kasa.module_execution import ModuleAwareInterpreter
from kasa.modules import ModuleBindingError

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
sys.path.insert(0, SCRIPTS)
try:
    from configure_kasa_modules import configure_module_runtime
    from plan_kasa_modules import NamespacePlanError
finally:
    sys.path.remove(SCRIPTS)


def _token():
    return parse("ka 1")[0].token


def _call(alias, export, args):
    token = _token()
    receiver = Node("name", token, value=alias)
    member = Node("module_member", token, value=export, children=(receiver,))
    arguments = tuple(Node("literal", token, value=arg) for arg in args)
    return Node("call", token, children=(member, arguments))


def test_real_catalog_exports_execute_without_global_leaks():
    out = io.StringIO()
    runtime = ModuleAwareInterpreter(stdout=out, max_steps=4000)
    plan = configure_module_runtime(runtime, ["math:m", "collections:c"])
    runtime.run([
        Node("print", _token(), children=(_call("m", "kasa_sum", [[10, 20, 30]]),)),
        Node("print", _token(), children=(_call("c", "kasa_contains", [[1, 2, 3], 2]),)),
    ])
    assert out.getvalue() == "60\nnokware\n"
    assert runtime.globals.values == {}
    assert plan["mode"] == "preflight_only"
    assert plan["capabilities_granted"] == []


def test_private_or_unknown_module_member_fails():
    runtime = ModuleAwareInterpreter(stdout=io.StringIO())
    configure_module_runtime(runtime, ["math:m"])
    with pytest.raises(KasaError, match="does not export"):
        runtime.evaluate(_call("m", "private_helper", [1]), runtime.globals)
    with pytest.raises(KasaError, match="Unknown module alias"):
        runtime.evaluate(_call("other", "kasa_sum", [[1]]), runtime.globals)


@pytest.mark.parametrize("selections, expected", [
    (["math:m", "collections:m"], "alias reused"),
    (["math:m", "math:x"], "more than once"),
    (["random:x"], "Unknown catalog module"),
])
def test_invalid_selection_rejected_without_global_mutation(selections, expected):
    runtime = ModuleAwareInterpreter(stdout=io.StringIO())
    with pytest.raises(NamespacePlanError, match=expected):
        configure_module_runtime(runtime, selections)
    assert runtime.globals.values == {}
    assert runtime._module_aliases == {}


def test_binding_rejects_application_shadowing_before_output():
    output = io.StringIO()
    runtime = ModuleAwareInterpreter(stdout=output)
    configure_module_runtime(runtime, ["math:m"])
    with pytest.raises(KasaError, match="Module alias cannot"):
        runtime.run(parse('ka "first"\nma m = 4'))
    assert output.getvalue() == ""


def test_existing_parser_still_refuses_unreviewed_import_syntax():
    with pytest.raises(KasaError):
        parse("module math alias m\nka m.kasa_sum([1, 2])")
