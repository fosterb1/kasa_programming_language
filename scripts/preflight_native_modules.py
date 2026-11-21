#!/usr/bin/env python3
"""G0.5a read-only static module prelink preflight. NO native code generation.

Usage: python scripts/preflight_native_modules.py stdlib/demos/group0_source_import_experiment.kasa
This validates the existing opt-in import AST against the pinned catalog and
reports what a future hygienic source linker would have to resolve. It neither
executes Kasa nor writes any output, emits bytecode, or alters normal syntax.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kasa import parse  # noqa: E402
from kasa.core import KasaError, Node  # noqa: E402
from plan_kasa_modules import NamespacePlanError, plan_bindings  # noqa: E402
from validate_kasa_catalog import (  # noqa: E402
    ALLOWED, CATALOG, CatalogError, _is_linked, load_catalog,
)


def _walk(value):
    if isinstance(value, Node):
        yield value
        yield from _walk(value.children)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _walk(item)


def preflight(source: str, *, filename: str = "<prelink>", root: Path = ROOT,
              catalog_path: Path | None = None) -> dict:
    """Validate imports, names, and pinned source without executing/writing."""
    root = root.absolute()
    catalog = load_catalog(catalog_path or root / "stdlib/catalog.json", root)
    indexed = {entry["id"]: entry for entry in catalog}
    program = parse(source, filename=filename, experimental_modules=True)
    imports = []
    body = []
    started = False
    selected_ids: set[str] = set()
    selected_aliases: set[str] = set()

    for stmt in program:
        if stmt.kind != "module_import":
            started = True
            body.append(stmt)
            continue
        if started:
            raise KasaError("SyntaxError", "Module declarations must precede statements", stmt.token, filename)
        module, alias = stmt.value
        if module in selected_ids:
            raise KasaError("ModuleError", "Module selected more than once: " + module, stmt.token, filename)
        if alias in selected_aliases:
            raise KasaError("ModuleError", "Module alias reused: " + alias, stmt.token, filename)
        if module not in indexed:
            raise KasaError("ModuleError", "Unknown catalog module: " + module, stmt.token, filename)
        selected_ids.add(module)
        selected_aliases.add(alias)
        imports.append((stmt, module, alias))

    if not imports:
        token = program[0].token if program else parse("ka 1")[0].token
        raise KasaError("SyntaxError", "At least one module declaration is required", token, filename)

    try:
        plan = plan_bindings([f"{module}:{alias}" for _, module, alias in imports], catalog)
    except NamespacePlanError as error:
        raise KasaError("ModuleError", str(error), imports[0][0].token, filename) from error

    exported = {alias: set(indexed[module]["exports"]) for _, module, alias in imports}
    private_names = {}
    for module in plan["load_order"]:
        entry = indexed[module]
        path = root / ALLOWED[module]
        if _is_linked(path, root) or not path.is_file():
            raise CatalogError("Module source is missing or linked: " + module)
        data = path.read_bytes()
        if b"\r" in data.replace(b"\r\n", b""):
            raise CatalogError("Unsupported module source line ending: " + module)
        normalized = data.replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(normalized).hexdigest() != entry["content_identity"]:
            raise CatalogError("Module source changed after validation: " + module)
        ast = parse(normalized.decode("utf-8", "strict"), filename=entry["source"])
        if any(n.kind != "function" for n in ast):
            raise CatalogError("Module may only contain function declarations: " + module)
        names = [n.value[0] for n in ast]
        if len(names) != len(set(names)) or not set(entry["exports"]).issubset(names):
            raise CatalogError("Module declarations disagree with catalog: " + module)
        private_names[module] = sorted(set(names) - set(entry["exports"]))

    references = []
    for stmt in body:
        for node in _walk(stmt):
            if node.kind == "module_import":
                raise KasaError("SyntaxError", "Module declarations must be top-level", node.token, filename)
            if node.kind == "module_member":
                alias = node.children[0].value
                if alias not in exported:
                    raise KasaError("NameError", "Unknown module alias '" + alias + "'", node.token, filename)
                if node.value not in exported[alias]:
                    raise KasaError("NameError", "Module does not export '" + node.value + "'", node.token, filename)
                references.append({"alias": alias, "export": node.value,
                                   "line": node.token.line, "column": node.token.column})
            if node.kind == "function":
                name, parameters = node.value
                if name in selected_aliases or any(p in selected_aliases for p in parameters):
                    raise KasaError("NameError", "Module alias cannot be redeclared", node.token, filename)
            if node.kind == "assign":
                target = node.children[0]
                while target.kind == "index":
                    target = target.children[0]
                if target.kind == "name" and target.value in selected_aliases:
                    raise KasaError("NameError", "Module alias cannot be reassigned", node.token, filename)

    return {
        "schema_version": 1,
        "mode": "native_prelink_preflight_only",
        "imports": [{"module": module, "alias": alias} for _, module, alias in imports],
        "load_order": plan["load_order"],
        "references": references,
        "private_functions_by_module": private_names,
        "capabilities_granted": [],
        "emits_source": False,
        "emits_bytecode": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source .kasa file to statically analyze")
    args = parser.parse_args(argv)
    try:
        data = args.source.read_text(encoding="utf-8")
        result = preflight(data, filename=str(args.source))
    except (OSError, UnicodeError, KasaError, CatalogError) as error:
        print("Native module preflight refused: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
