#!/usr/bin/env python3
"""Read-only G1 experimental manifest validator; does not enable imports.

G0 catalog, loader, compiler, VM and browser behavior remain unchanged.
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
CATALOG = ROOT / "stdlib/g1/catalog.json"
ALLOWED = {"math": "stdlib/g1/math.kasa", "collections": "stdlib/g1/collections.kasa"}
EXPECTED_EXPORTS = {
    "math": ("kasa_min_or", "kasa_max_or", "kasa_total", "kasa_average_or", "kasa_count_above"),
    "collections": ("kasa_first_index", "kasa_last_index", "kasa_count_distinct", "kasa_all_equal"),
}
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*\Z", re.ASCII)
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
MAX_MANIFEST = 32_000
MAX_SOURCE = 50_000


class G1CatalogError(ValueError):
    pass


def _regular_unlinked(path: Path, root: Path) -> bool:
    if not path.is_relative_to(root):
        return False
    current = root
    for part in ((), *[(p,) for p in path.relative_to(root).parts]):
        if part:
            current = current / part[0]
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            return False
    return path.is_file()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise G1CatalogError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def validate(catalog_path: Path = CATALOG, root: Path = ROOT) -> list[dict]:
    """Validate fixed, closed G1 catalog without executing any Kasa source."""
    root = root.absolute()
    catalog_path = catalog_path.absolute()
    if not _regular_unlinked(catalog_path, root):
        raise G1CatalogError("Manifest must be a regular unlinked file under root")
    raw = catalog_path.read_bytes()
    if len(raw) > MAX_MANIFEST:
        raise G1CatalogError("Manifest exceeds byte limit")
    try:
        payload = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise G1CatalogError("Invalid UTF-8/JSON manifest") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "library_generation", "status", "modules"}:
        raise G1CatalogError("Manifest schema keys do not match G1 v1")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise G1CatalogError("Unsupported schema version")
    if payload["library_generation"] != "G1" or payload["status"] != "experimental_manifest_only":
        raise G1CatalogError("Unsupported library generation or status")
    modules = payload["modules"]
    if not isinstance(modules, list) or len(modules) != len(ALLOWED):
        raise G1CatalogError("Manifest must name exactly the two reviewed G1 modules")
    by_id = {}
    for module in modules:
        if not isinstance(module, dict) or set(module) != {"id", "source", "exports", "dependencies", "content_identity"}:
            raise G1CatalogError("Invalid module metadata")
        name = module["id"]
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name not in ALLOWED:
            raise G1CatalogError("Unknown or unsafe G1 module identifier")
        if name in by_id:
            raise G1CatalogError("Duplicate module identifier")
        if module["source"] != ALLOWED[name]:
            raise G1CatalogError("Source does not match G1 allowlist")
        if module["exports"] != list(EXPECTED_EXPORTS[name]):
            raise G1CatalogError("Exports differ from reviewed G1 contract")
        if module["dependencies"] != []:
            raise G1CatalogError("G1.2.1 does not permit module dependencies")
        digest = module["content_identity"]
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise G1CatalogError("Invalid SHA-256 source identity")
        source_path = root / ALLOWED[name]
        if not _regular_unlinked(source_path, root):
            raise G1CatalogError("G1 source is missing or linked")
        data = source_path.read_bytes()
        if len(data) > MAX_SOURCE:
            raise G1CatalogError("G1 source exceeds byte limit")
        if b"\r" in data.replace(b"\r\n", b""):
            raise G1CatalogError("Unsupported source line endings")
        canonical = data.replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(canonical).hexdigest() != digest:
            raise G1CatalogError("G1 source hash mismatch: " + name)
        try:
            nodes = parse(canonical.decode("utf-8", "strict"), filename=ALLOWED[name])
        except Exception as exc:
            raise G1CatalogError("G1 source parse failed: " + name) from exc
        if any(node.kind != "function" for node in nodes):
            raise G1CatalogError("G1 source permits top-level functions only")
        declarations = [node.value[0] for node in nodes]
        if len(declarations) != len(set(declarations)) or declarations != module["exports"]:
            raise G1CatalogError("Function declarations differ from G1 manifest exports")
        by_id[name] = module
    return [by_id[name] for name in sorted(by_id)]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    options = parser.parse_args(argv)
    try:
        modules = validate(options.catalog)
    except (G1CatalogError, OSError) as exc:
        print("G1 manifest invalid:", exc, file=sys.stderr)
        return 2
    print("PASS: separate experimental G1 catalog, content hashes and reviewed exports")
    for module in modules:
        print("  " + module["id"] + " -> " + ", ".join(module["exports"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
