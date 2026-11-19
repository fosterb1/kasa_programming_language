"""G0.3 experimental Python-only member resolution using explicit AST nodes.

No Kasa syntax changes. Callers construct Node("module_member") through a
future reviewed parser, and pass catalog-verified namespaces, never arbitrary
Python objects. Existing interpreter evaluation and quotas remain in charge
of calling exported Kasa functions.
"""
from __future__ import annotations

from collections.abc import Mapping
import re

from .core import BUILTIN_NAMES, KEYWORDS, Interpreter, Node
from .modules import ModuleBindingError, ModuleNamespace

_ALIAS = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z", re.ASCII)


class ModuleAwareInterpreter(Interpreter):
    """Experimental extension for static module-member AST expressions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._module_aliases: dict[str, ModuleNamespace] = {}

    def bind_namespaces(self, bindings: Mapping[str, ModuleNamespace]) -> None:
        """Install explicitly named namespaces, without injecting globals."""
        if self._module_aliases:
            raise ModuleBindingError("Module aliases have already been bound")
        proposed = {}
        for alias, module in bindings.items():
            if not isinstance(alias, str) or not _ALIAS.fullmatch(alias):
                raise ModuleBindingError("Invalid module alias")
            if alias in KEYWORDS or alias in BUILTIN_NAMES or alias == "a":
                raise ModuleBindingError("Reserved module alias: " + alias)
            if alias in self.globals.values:
                raise ModuleBindingError("Alias collides with application global: " + alias)
            if not isinstance(module, ModuleNamespace):
                raise ModuleBindingError("Module alias requires a validated namespace")
            proposed[alias] = module
        if not proposed:
            raise ModuleBindingError("At least one namespace must be bound")
        self._module_aliases = proposed

    def _reject_alias_shadowing(self, body: list[Node]) -> None:
        aliases = set(self._module_aliases)
        def scan(node):
            if not isinstance(node, Node):
                if isinstance(node, (list, tuple)):
                    for child in node:
                        scan(child)
                return
            if node.kind == "function":
                name, parameters = node.value
                if name in aliases or any(p in aliases for p in parameters):
                    self.error(node.token, "NameError", "Module alias cannot be redeclared")
            if node.kind == "assign":
                target = node.children[0]
                while target.kind == "index":
                    target = target.children[0]
                if target.kind == "name" and target.value in aliases:
                    self.error(node.token, "NameError", "Module alias cannot be reassigned")
            scan(node.children)
        scan(body)

    def run(self, program: list[Node], filename: str | None = None) -> None:
        # Reject alias shadowing in nested functions and blocks before any
        # top-level app statements execute. Avoid runtime alias injection.
        self._reject_alias_shadowing(program)
        super().run(program, filename=filename)

    def evaluate(self, expr: Node, env):
        if expr.kind == "module_member":
            self.tick(expr.token)
            if len(expr.children) != 1 or expr.children[0].kind != "name" or not isinstance(expr.value, str):
                self.error(expr.token, "SyntaxError", "Invalid module member expression")
            alias = expr.children[0].value
            module = self._module_aliases.get(alias)
            if module is None:
                self.error(expr.token, "NameError", f"Unknown module alias '{alias}'")
            try:
                return module.resolve(expr.value)
            except ModuleBindingError:
                self.error(expr.token, "NameError", f"Module '{module.module_id}' does not export '{expr.value}'")
        return super().evaluate(expr, env)
