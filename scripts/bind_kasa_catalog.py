#!/usr/bin/env python3
"""G0.3 experimental catalog-to-Python module binder.

This opt-in developer API is NOT Kasa import syntax, a sandbox or a package
manager. Only the G0.2 allowlisted, SHA-256-pinned source modules are loaded.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from kasa import parse
from kasa.core import Interpreter
from kasa.modules import ModuleNamespace, instantiate_module

from validate_kasa_catalog import (
    ALLOWED, CATALOG, ROOT, CatalogError, _is_linked, load_catalog,
)


def bind_catalog_modules(
    runtime: Interpreter,
    *,
    catalog_path: Path = CATALOG,
    root: Path = ROOT,
) -> dict[str, ModuleNamespace]:
    """Validate all sources then instantiate distinct function-only scopes.

    No files are written. No runtime globals or parser keywords are changed.
    Validation is repeated against the exact bytes parsed, so a source edit
    between the initial catalog validation and reading is rejected.
    """
    root = root.absolute()
    entries = load_catalog(catalog_path, root)
    pending: list[tuple[dict, list]] = []
    for entry in entries:
        path = root / ALLOWED[entry["id"]]
        if _is_linked(path, root) or not path.is_file():
            raise CatalogError("Module source is missing or linked: " + entry["id"])
        payload = path.read_bytes()
        if b"\r" in payload.replace(b"\r\n", b""):
            raise CatalogError("Unsupported module source line ending")
        payload = payload.replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(payload).hexdigest() != entry["content_identity"]:
            raise CatalogError("Module source changed after validation: " + entry["id"])
        ast = parse(payload.decode("utf-8", "strict"), filename=entry["source"])
        pending.append((entry, ast))
    # Every AST and content identity has been checked before constructing
    # namespace objects. Only explicit public functions are accessible.
    return {
        entry["id"]: instantiate_module(entry["id"], ast, entry["exports"], runtime)
        for entry, ast in pending
    }
