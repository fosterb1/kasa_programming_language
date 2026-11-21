#!/usr/bin/env python3
"""Experimental G1 source linker for local native/KBC1 consumers.

Prints flattened verified Kasa to stdout; does not publish bytecode, modify
native C++/KBC, or enable standard native import syntax. Trusted-local only.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from kasa.core import KasaError
from link_kasa_modules_hygienic import HygienicLinkError, link_source
from validate_g1_catalog import G1CatalogError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("application", type=Path, help="Locally trusted .kasa application")
    args = parser.parse_args(argv)
    try:
        path = args.application
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 50_000:
            raise HygienicLinkError("Application must be an unlinked file within source size limit")
        raw = path.read_bytes()
        if len(raw) > 50_000:
            raise HygienicLinkError("Application exceeds source size limit")
        linked = link_source(raw.decode("utf-8", "strict"),
                             filename=str(path), generation="g1")
    except (OSError, UnicodeError, KasaError, HygienicLinkError, G1CatalogError, ValueError) as exc:
        print("G1 native prelink refused: " + str(exc), file=sys.stderr)
        return 2
    sys.stdout.write(linked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
