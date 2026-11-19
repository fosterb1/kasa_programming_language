#!/usr/bin/env python3
"""G0.3 trusted catalog -> namespace-aware Python runtime integration.

Opt-in developer API only. It does NOT implement a Kasa import declaration,
parse dotted source, install packages, or grant filesystem/network abilities.
The validated catalog remains the only source of module definitions.
"""
from __future__ import annotations

from pathlib import Path

from kasa.module_execution import ModuleAwareInterpreter

from bind_kasa_catalog import bind_catalog_modules
from plan_kasa_modules import plan_bindings
from validate_kasa_catalog import CATALOG, ROOT, load_catalog


def configure_module_runtime(
    runtime: ModuleAwareInterpreter,
    selections: list[str],
    *,
    catalog_path: Path = CATALOG,
    root: Path = ROOT,
) -> dict:
    """Preflight aliases, verify pinned sources, and bind requested namespaces.

    Call only on a new, unused ModuleAwareInterpreter. The caller supplies
    trusted synthetic AST nodes for now; ordinary .kasa syntax is unchanged.
    """
    if not isinstance(runtime, ModuleAwareInterpreter):
        raise TypeError("Expected ModuleAwareInterpreter")
    if runtime._module_aliases:
        raise ValueError("Runtime already has module bindings")
    if runtime.globals.values:
        raise ValueError("Expected a fresh runtime without application globals")

    catalog = load_catalog(catalog_path, root)
    plan = plan_bindings(selections, catalog)
    modules = bind_catalog_modules(runtime, catalog_path=catalog_path, root=root)
    runtime.bind_namespaces({
        binding["alias"]: modules[binding["module"]]
        for binding in plan["bindings"]
    })
    return plan
