"""G0.3 module-member AST execution without new user-facing keywords."""
import io

import pytest

from kasa import parse
from kasa.core import Environment, KasaError, Node
from kasa.module_execution import ModuleAwareInterpreter
from kasa.modules import ModuleBindingError, instantiate_module


def prepare():
    runtime = ModuleAwareInterpreter(stdout=io.StringIO(), max_steps=2000)
    a = instantiate_module("math", parse("""
dwumadie private(x)
    sanma x + 3
awiei

dwumadie calculate(x)
    sanma private(x) * 2
awiei
"""), ["calculate"], runtime)
    b = instantiate_module("other", parse("""
dwumadie calculate(x)
    sanma x + 5
awiei
"""), ["calculate"], runtime)
    runtime.bind_namespaces({"m": a, "c": b})
    return runtime


def member(alias, name):
    token = parse("ka 1")[0].token
    return Node("module_member", token, value=name, children=(Node("name", token, value=alias),))


def call_member(alias, name, number):
    token = parse("ka 1")[0].token
    return Node("call", token, children=(member(alias, name), (Node("literal", token, value=number),)))


def test_exports_called_in_distinct_private_scopes():
    runtime = prepare()
    assert runtime.evaluate(call_member("m", "calculate", 4), runtime.globals) == 14
    assert runtime.evaluate(call_member("c", "calculate", 4), runtime.globals) == 9
    assert runtime.globals.values == {}


def test_private_and_missing_member_are_name_errors():
    runtime = prepare()
    with pytest.raises(KasaError, match="does not export"):
        runtime.evaluate(member("m", "private"), runtime.globals)
    with pytest.raises(KasaError, match="Unknown module alias"):
        runtime.evaluate(member("not_bound", "calculate"), runtime.globals)


@pytest.mark.parametrize("alias", ["ka", "ma", "tentɛn", "a", "../math", "9m"])
def test_alias_restrictions(alias):
    runtime = ModuleAwareInterpreter(stdout=io.StringIO())
    namespace = instantiate_module(
        "math", parse("dwumadie f()\n sanma 1\nawiei"), ["f"], runtime
    )
    with pytest.raises(ModuleBindingError):
        runtime.bind_namespaces({alias: namespace})


@pytest.mark.parametrize("source", [
    "ma m = 2",
    "ma m[0] = 3",
    "dwumadie m()\n sanma 1\nawiei",
    "dwumadie demo(m)\n sanma m\nawiei",
    "sɛ nokware a\n ma m = 4\nawiei",
])
def test_alias_redeclaration_is_rejected_before_execution(source):
    runtime = prepare()
    program = parse('ka "should not print"\n' + source)
    with pytest.raises(KasaError, match="Module alias cannot"):
        runtime.run(program)
    assert runtime.stdout.getvalue() == ""


def test_no_member_syntax_was_added_to_normal_parser():
    with pytest.raises(KasaError):
        parse("ka m.calculate(1)")


def test_member_resolution_uses_existing_call_budget():
    runtime = ModuleAwareInterpreter(stdout=io.StringIO(), max_steps=15)
    namespace = instantiate_module("spin", parse("""
dwumadie forever()
    bere_a nokware
        ma n = 1
    awiei
awiei
"""), ["forever"], runtime)
    runtime.bind_namespaces({"s": namespace})
    token = parse("ka 1")[0].token
    expression = Node("call", token, children=(member("s", "forever"), tuple()))
    with pytest.raises(KasaError, match="Execution limit"):
        runtime.evaluate(expression, runtime.globals)
