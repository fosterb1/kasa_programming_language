#!/usr/bin/env python3
"""Opt-in source-to-execution experiment for local Kasa standard-library imports.

Usage: python scripts/run_kasa_modules_experimental.py path/to/file.kasa

Prototype declaration syntax is @math:m; it is NOT final Twi grammar.
Normal Python/JS/native Kasa CLI and browser syntax remain unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Direct file execution sets sys.path[0] to scripts/, whereas the Kasa
# package lives in src/. Pytest config adds src/ only during test runs.
# Resolve relative to this trusted script, not the caller's current directory.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kasa import parse
from kasa.core import KasaError, Node
from kasa.module_execution import ModuleAwareInterpreter
from plan_kasa_modules import NamespacePlanError
from validate_kasa_catalog import CatalogError
from configure_kasa_modules import configure_module_runtime


def execute_module_source(
    source: str,
    *,
    filename: str = "<module-experiment>",
    stdout=None,
    max_steps: int = 100_000,
) -> ModuleAwareInterpreter:
    """Parse complete Kasa source then preflight/bind before executing it.

    Only catalog-pinned modules; no filename-provided import paths.
    The prototype accepts import declarations only at the beginning.
    """
    program = parse(source, filename=filename, experimental_modules=True)
    declarations = []
    body = []
    body_started = False

    def walk(node):
        if isinstance(node, Node):
            yield node
            for child in node.children:
                yield from walk(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                yield from walk(child)

    for stmt in program:
        if stmt.kind == "module_import":
            if body_started:
                raise KasaError("SyntaxError", "Module declarations must precede statements", stmt.token, filename)
            module_id, alias = stmt.value
            declarations.append(f"{module_id}:{alias}")
        else:
            body_started = True
            body.append(stmt)
    if not declarations:
        token = program[0].token if program else parse("ka 1")[0].token
        raise KasaError("SyntaxError", "At least one module declaration is required", token, filename)

    for stmt in body:
        for node in walk(stmt):
            if node.kind == "module_import":
                raise KasaError("SyntaxError", "Module declarations must be top-level", node.token, filename)

    runtime = ModuleAwareInterpreter(filename=filename, stdout=stdout, max_steps=max_steps)
    try:
        configure_module_runtime(runtime, declarations)
    except (NamespacePlanError, CatalogError, ValueError) as error:
        raise KasaError("ModuleError", str(error), program[0].token, filename) from error

    for stmt in body:
        for node in walk(stmt):
            if node.kind != "module_member":
                continue
            alias = node.children[0].value
            namespace = runtime._module_aliases.get(alias)
            if namespace is None:
                raise KasaError("NameError", f"Unknown module alias '{alias}'", node.token, filename)
            if node.value not in namespace.exports:
                raise KasaError("NameError", f"Module '{namespace.module_id}' does not export '{node.value}'", node.token, filename)
    runtime.run(body, filename=filename)
    return runtime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args(argv)
    try:
        content = args.source.read_text(encoding="utf-8")
        execute_module_source(content, filename=str(args.source))
    except (OSError, UnicodeError, KasaError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
