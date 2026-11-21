#!/usr/bin/env python3
"""Opt-in source-to-execution experiment for local Kasa standard-library imports.

Usage: python scripts/run_kasa_modules_experimental.py path/to/file.kasa

Prototype declaration syntax is @math:m or fa math firi stdlib: m; it is NOT final Twi grammar.
The optional --generation g1 uses a separate pinned G1 catalog; g0 is default.
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
from configure_g1_modules import configure_g1_runtime
from validate_g1_catalog import G1CatalogError


def execute_module_source(
    source: str,
    *,
    filename: str = "<module-experiment>",
    stdout=None,
    max_steps: int = 100_000,
    generation: str = "g0",
) -> ModuleAwareInterpreter:
    """Parse complete Kasa source then preflight/bind before executing it.

    Only catalog-pinned modules; no filename-provided import paths.
    The prototype accepts import declarations only at the beginning.
    """
    if generation not in ("g0", "g1"):
        raise ValueError("Only experimental g0 and g1 generations are supported")
    program = parse(source, filename=filename, experimental_modules=True)
    declarations = []
    body = []
    body_started = False
    # Track the exact import statement that introduces a conflict. The
    # catalog planner still validates the full graph after this local check.
    selected_modules: set[str] = set()
    selected_aliases: set[str] = set()

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
            if module_id in selected_modules:
                raise KasaError("ModuleError", "Module selected more than once: " + module_id, stmt.token, filename)
            if alias in selected_aliases:
                raise KasaError("ModuleError", "Module alias reused: " + alias, stmt.token, filename)
            selected_modules.add(module_id)
            selected_aliases.add(alias)
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
        if generation == "g1":
            configure_g1_runtime(runtime, declarations)
        else:
            configure_module_runtime(runtime, declarations)
    except (NamespacePlanError, CatalogError, G1CatalogError, ValueError, OSError) as error:
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
    parser.add_argument("--generation", choices=("g0", "g1"), default="g0",
                        help="Experimental module catalog generation; default g0")
    args = parser.parse_args(argv)
    try:
        content = args.source.read_text(encoding="utf-8")
        execute_module_source(content, filename=str(args.source), generation=args.generation)
    except (OSError, UnicodeError, KasaError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
