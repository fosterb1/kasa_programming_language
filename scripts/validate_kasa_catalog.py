#!/usr/bin/env python3
"""G0.2 read-only validation of the pinned experimental Kasa library catalog.

No program execution, dynamic imports, network, or file writes.
This validator does NOT implement language-level Kasa import or namespace binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from kasa import parse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "stdlib" / "catalog.json"
# Explicit source allowlist; catalog JSON is not trusted to select arbitrary paths.
ALLOWED = {
    "math": "stdlib/experimental/math.kasa",
    "collections": "stdlib/experimental/collections.kasa",
}
MODULE_ID = re.compile(r"[a-z][a-z0-9_]*\Z", re.ASCII)
EXPORT_ID = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z", re.ASCII)
HASH_ID = re.compile(r"sha256:[a-f0-9]{64}\Z", re.ASCII)
MAX_CATALOG_BYTES = 32_000
MAX_MODULE_BYTES = 50_000


class CatalogError(ValueError):
    pass


def _is_linked(path: Path, base: Path) -> bool:
    if not path.is_relative_to(base):
        return True
    current = base
    for part in ((), *[(part,) for part in path.relative_to(base).parts]):
        if part:
            current = current / part[0]
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            return True
    return False


def _unique_list(value: object, label: str, pattern: re.Pattern) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not pattern.fullmatch(x) for x in value):
        raise CatalogError(label + " must be a list of valid identifiers")
    if len(value) != len(set(value)):
        raise CatalogError(label + " contains duplicate identifiers")
    return value


def _json_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def load_catalog(catalog_path: Path = CATALOG, root: Path = ROOT) -> list[dict]:
    """Return modules in stable dependency-first order, or raise CatalogError."""
    root = root.absolute()
    catalog_path = catalog_path.absolute()
    if _is_linked(catalog_path, root) or not catalog_path.is_file():
        raise CatalogError("Catalog must be a regular file beneath repository root")
    raw = catalog_path.read_bytes()
    if len(raw) > MAX_CATALOG_BYTES:
        raise CatalogError("Catalog exceeds size limit")
    try:
        catalog = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_json_no_duplicates)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError("Invalid UTF-8/JSON catalog") from exc
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "modules"} or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        raise CatalogError("Unsupported catalog schema")
    entries = catalog["modules"]
    if not isinstance(entries, list) or not entries or len(entries) > len(ALLOWED):
        raise CatalogError("Invalid module count")
    by_id = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"id", "source", "exports", "dependencies", "content_identity"}:
            raise CatalogError("Invalid module metadata keys")
        name = entry["id"]
        if not isinstance(name, str) or not MODULE_ID.fullmatch(name) or name not in ALLOWED:
            raise CatalogError("Unknown or unsafe module ID")
        if name in by_id:
            raise CatalogError("Duplicate module ID: " + name)
        if entry["source"] != ALLOWED[name]:
            raise CatalogError("Module source must match trusted allowlist")
        exports = _unique_list(entry["exports"], "Exports", EXPORT_ID)
        if not exports:
            raise CatalogError("Module must export at least one function")
        dependencies = _unique_list(entry["dependencies"], "Dependencies", MODULE_ID)
        if not isinstance(entry["content_identity"], str) or not HASH_ID.fullmatch(entry["content_identity"]):
            raise CatalogError("Missing or invalid SHA-256 identity")
        module_path = root / ALLOWED[name]
        if _is_linked(module_path, root) or not module_path.is_file():
            raise CatalogError("Module source is missing, outside root or linked")
        raw_module = module_path.read_bytes()
        if len(raw_module) > MAX_MODULE_BYTES:
            raise CatalogError("Module source exceeds size limit")
        if b"\r" in raw_module.replace(b"\r\n", b""):
            raise CatalogError("Unsupported module source line ending")
        raw_module = raw_module.replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(raw_module).hexdigest() != entry["content_identity"]:
            raise CatalogError("Module content hash mismatch: " + name)
        try:
            source = raw_module.decode("utf-8", "strict")
            ast = parse(source, filename=ALLOWED[name])
        except (UnicodeError, Exception) as exc:
            # Kasa syntax diagnostics are intentionally reduced to catalog
            # validation errors; the specific parser error is chained.
            raise CatalogError("Module source invalid: " + name) from exc
        if any(node.kind != "function" for node in ast):
            raise CatalogError("Module may only contain top-level functions")
        declarations = [node.value[0] for node in ast]
        if len(declarations) != len(set(declarations)):
            raise CatalogError("Duplicate function declaration")
        if not set(exports).issubset(declarations):
            raise CatalogError("Exports contain undeclared functions: " + name)
        by_id[name] = entry
    order, states = [], {}
    def visit(name: str):
        state = states.get(name, 0)
        if state == 1:
            raise CatalogError("Dependency cycle at " + name)
        if state == 2:
            return
        states[name] = 1
        for dep in sorted(by_id[name]["dependencies"]):
            if dep not in by_id:
                raise CatalogError("Missing dependency: " + dep)
            visit(dep)
        states[name] = 2
        order.append(by_id[name])
    for name in sorted(by_id):
        visit(name)
    return order


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    args = parser.parse_args(argv)
    try:
        modules = load_catalog(args.catalog)
    except (CatalogError, OSError) as exc:
        print("Catalog invalid:", exc, file=sys.stderr)
        return 2
    print("PASS: catalog schema, source identities, declared exports and dependency graph")
    for module in modules:
        print("  " + module["id"] + " -> " + ", ".join(module["exports"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
