#!/usr/bin/env python3
"""G0.3 preflight for planned Kasa module namespace bindings.

Read-only planning: validates aliases, module selections and transitive
dependencies against the pinned G0.2 catalog. Does not parse imports, execute
code, concatenate source or grant host capabilities.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from validate_kasa_catalog import CatalogError, load_catalog

ALIAS = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z", re.ASCII)
# Restrict names that would already have language-level meaning. Additional
# tokens can be included here after a full lexer inventory / linguistic review.
RESERVED = frozenset({
    "ma", "ka", "dwumadie", "sanma", "awiei", "nokware", "atoro",
    "sɛ", "anyɛ_saa_a", "mpɛn", "bere_a", "gyae", "toa_so",
    "ne", "anaa", "ɛnyɛ",
})


class NamespacePlanError(ValueError):
    """The requested module/alias binding is invalid."""


def plan_bindings(specs: list[str], catalog: list[dict]) -> dict:
    """Produce a deterministic *plan*, not active namespace bindings."""
    if not specs:
        raise NamespacePlanError("Specify at least one --use module:alias")
    indexed = {entry["id"]: entry for entry in catalog}
    if len(indexed) != len(catalog):
        raise NamespacePlanError("Catalog contains duplicate module IDs")
    selected: dict[str, str] = {}
    aliases: set[str] = set()
    for spec in specs:
        if spec.count(":") != 1:
            raise NamespacePlanError("Expected --use module:alias")
        module, alias = spec.split(":", 1)
        if module not in indexed:
            raise NamespacePlanError("Unknown catalog module: " + module)
        if not ALIAS.fullmatch(alias) or alias in RESERVED:
            raise NamespacePlanError("Invalid or reserved module alias: " + alias)
        if module in selected:
            raise NamespacePlanError("Module selected more than once: " + module)
        if alias in aliases:
            raise NamespacePlanError("Module alias reused: " + alias)
        selected[module] = alias
        aliases.add(alias)

    needed: set[str] = set()
    visiting: set[str] = set()

    def include(name: str) -> None:
        if name not in indexed:
            raise NamespacePlanError("Missing module dependency: " + name)
        if name in visiting:
            raise NamespacePlanError("Module dependency cycle: " + name)
        if name in needed:
            return
        visiting.add(name)
        for dep in sorted(indexed[name]["dependencies"]):
            include(dep)
        visiting.remove(name)
        needed.add(name)

    for name in sorted(selected):
        include(name)
    # Catalog validator guarantees dependency-first topological order.
    ordered = [entry for entry in catalog if entry["id"] in needed]
    if len(ordered) != len(needed):
        raise NamespacePlanError("Incomplete dependency ordering")
    return {
        "schema_version": 1,
        "mode": "preflight_only",
        "bindings": [
            {"module": name, "alias": selected[name], "exports": indexed[name]["exports"]}
            for name in sorted(selected)
        ],
        "load_order": [entry["id"] for entry in ordered],
        "capabilities_granted": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use", action="append", required=True,
                        help="module:alias (example math:m)")
    args = parser.parse_args(argv)
    try:
        plan = plan_bindings(args.use, load_catalog())
    except (NamespacePlanError, CatalogError, OSError) as exc:
        print("Module namespace plan refused:", exc, file=sys.stderr)
        return 2
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
