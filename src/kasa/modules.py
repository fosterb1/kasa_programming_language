"""Experimental G0.3 namespace primitives for trusted, already-validated Kasa AST.

No source loading, import grammar, member syntax, or filesystem access.
Caller must validate the pinned catalog before passing an AST to this API.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .core import Environment, Interpreter, Node, UserFunction


class ModuleBindingError(ValueError):
    """Invalid module declaration or a request for a non-public symbol."""


@dataclass(frozen=True)
class ModuleNamespace:
    module_id: str
    exports: Mapping[str, UserFunction]

    def resolve(self, symbol: str) -> UserFunction:
        """Only explicitly exported functions can be resolved."""
        try:
            return self.exports[symbol]
        except KeyError:
            raise ModuleBindingError(
                f"Module '{self.module_id}' does not export '{symbol}'"
            ) from None


def instantiate_module(
    module_id: str,
    declarations: list[Node],
    exports: list[str],
    runtime: Interpreter,
) -> ModuleNamespace:
    """Instantiate function-only module AST in a private lexical environment.

    This does not execute user-supplied top-level statements, load arbitrary
    source files, or mutate runtime.globals. Function invocation still uses
    the owning runtime's step and call-depth budgets.
    """
    if not module_id or not isinstance(module_id, str):
        raise ModuleBindingError("Module ID must be a nonempty string")
    if not exports or len(exports) != len(set(exports)):
        raise ModuleBindingError("Exports must be a nonempty list without duplicates")
    names: set[str] = set()
    for node in declarations:
        if node.kind != "function":
            raise ModuleBindingError("Modules may contain only function declarations")
        name, parameters = node.value
        if name in names or len(parameters) != len(set(parameters)):
            raise ModuleBindingError("Duplicate module function or parameter")
        names.add(name)
    if not set(exports).issubset(names):
        raise ModuleBindingError("Export refers to an undeclared function")

    # Reuse the reference interpreter's native closure semantics. All
    # module declarations capture the same isolated environment; therefore
    # private helper functions remain callable inside the module.
    private = Environment()
    for node in declarations:
        runtime.execute(node, private)
    published = {name: private.values[name] for name in exports}
    return ModuleNamespace(module_id, MappingProxyType(published))
