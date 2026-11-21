#!/usr/bin/env python3
"""G1.2.2 opt-in Python-only, pinned G1 namespace configuration.

No arbitrary paths, package downloads, global injection or new host privileges.
The existing default G0 experimental runner remains unchanged.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from kasa import parse
from kasa.module_execution import ModuleAwareInterpreter
from kasa.modules import instantiate_module

from plan_kasa_modules import plan_bindings
from validate_g1_catalog import ALLOWED, CATALOG, ROOT, G1CatalogError, validate, _regular_unlinked


def configure_g1_runtime(
    runtime: ModuleAwareInterpreter,
    selections: list[str],
    *,
    catalog_path: Path = CATALOG,
    root: Path = ROOT,
) -> dict:
    """Verify G1, rehash all source bytes and bind only reviewed functions."""
    if not isinstance(runtime, ModuleAwareInterpreter):
        raise TypeError("Expected ModuleAwareInterpreter")
    if runtime._module_aliases or runtime.globals.values:
        raise ValueError("Expected a fresh module-aware runtime")
    root = root.absolute()
    entries = validate(catalog_path, root)
    plan = plan_bindings(selections, entries)
    prepared = []
    for entry in entries:
        source = root / ALLOWED[entry["id"]]
        if not _regular_unlinked(source, root):
            raise G1CatalogError("G1 source is missing or linked")
        raw = source.read_bytes()
        if len(raw) > 50_000 or b"\r" in raw.replace(b"\r\n", b""):
            raise G1CatalogError("G1 source size/line endings invalid")
        canonical = raw.replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(canonical).hexdigest() != entry["content_identity"]:
            raise G1CatalogError("G1 source changed after validation")
        ast = parse(canonical.decode("utf-8", "strict"), filename=entry["source"])
        if any(node.kind != "function" for node in ast):
            raise G1CatalogError("G1 module contains a top-level statement")
        names = [node.value[0] for node in ast]
        if names != entry["exports"]:
            raise G1CatalogError("G1 exports changed after validation")
        prepared.append((entry, ast))
    namespaces = {
        entry["id"]: instantiate_module(entry["id"], ast, entry["exports"], runtime)
        for entry, ast in prepared
    }
    runtime.bind_namespaces({
        item["alias"]: namespaces[item["module"]] for item in plan["bindings"]
    })
    return plan
