"""G0.3 native Python environment isolation, independent of import grammar."""
import io

import pytest

from kasa.core import Environment, Interpreter, Node, parse
from kasa.modules import ModuleBindingError, instantiate_module


SOURCE = """dwumadie hidden(x)
    sanma x + 1
awiei

dwumadie public(x)
    sanma hidden(x) * 2
awiei
"""


def invoke(runtime, function, value):
    """Use the existing Kasa evaluator/call path to honor runtime budgets."""
    token = parse("ka 1")[0].token
    environment = Environment({"selected": function})
    expression = Node(
        "call", token,
        children=(
            Node("name", token, value="selected"),
            (Node("literal", token, value=value),),
        ),
    )
    return runtime.evaluate(expression, environment)


def test_private_helper_available_only_inside_module():
    runtime = Interpreter(stdout=io.StringIO())
    namespace = instantiate_module(
        "sample", parse(SOURCE), ["public"], runtime
    )
    assert invoke(runtime, namespace.resolve("public"), 4) == 10
    assert runtime.globals.values == {}
    with pytest.raises(ModuleBindingError, match="does not export"):
        namespace.resolve("hidden")
    with pytest.raises(TypeError):
        namespace.exports["hidden"] = namespace.resolve("public")


def test_two_modules_can_have_same_private_declarations():
    runtime = Interpreter(stdout=io.StringIO())
    a = instantiate_module("a", parse(SOURCE), ["public"], runtime)
    b = instantiate_module(
        "b", parse(SOURCE.replace("x + 1", "x + 3")), ["public"], runtime
    )
    assert invoke(runtime, a.resolve("public"), 2) == 6
    assert invoke(runtime, b.resolve("public"), 2) == 10
    assert runtime.globals.values == {}


@pytest.mark.parametrize("source,exports,reason", [
    ("ka 10", ["public"], "only function declarations"),
    (SOURCE, ["missing"], "undeclared"),
    (SOURCE, ["public", "public"], "duplicates"),
    (SOURCE, [], "nonempty"),
    (SOURCE + SOURCE, ["public"], "Duplicate module function"),
])
def test_reject_invalid_declarations_before_execution(source, exports, reason):
    runtime = Interpreter(stdout=io.StringIO())
    with pytest.raises(ModuleBindingError, match=reason):
        instantiate_module("sample", parse(source), exports, runtime)
    assert runtime.globals.values == {}


def test_runtime_budget_applies_to_module_function_calls():
    runtime = Interpreter(stdout=io.StringIO(), max_steps=12)
    namespace = instantiate_module(
        "sample",
        parse("""dwumadie forever(x)
    bere_a nokware
        ma x = x + 1
    awiei
awiei
"""),
        ["forever"], runtime,
    )
    with pytest.raises(Exception, match="Execution limit"):
        invoke(runtime, namespace.resolve("forever"), 0)
