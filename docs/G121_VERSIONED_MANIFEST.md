# G1.2.1 — Separate versioned experimental module manifest

**Status:** Manifest validation only; **does not enable G1 imports**. G1.2.2
will require separately reviewed runtime integration.

## What exists

- `stdlib/g1/catalog.json`: G1 schema version 1, generation and status
  markers, two modules (`math`, `collections`), exactly nine explicitly
  reviewed exported functions, empty dependencies and pinned SHA-256 identities.
- `scripts/validate_g1_catalog.py`: read-only, strict loader and validator.
- `tests/test_validate_g1_catalog.py`: positive/negative test suite.

The manifest uses canonical LF UTF-8 for SHA-256; Windows CRLF checkouts
are accepted after newline normalization. Lone CR endings are rejected.
Paths are fixed to two reviewed source locations, with missing/symlinked
files, junctions, source modification, unexpected exports, duplicate IDs,
duplicate JSON keys, unexpected metadata, top-level statements and invalid
identities rejected. Maximum manifest/source sizes are bounded.

**Important:** Hashes are source-integrity consistency pins, **not digital
signatures or verification of a publisher**. The validator parses Kasa source,
but does not execute it, import it into a user program or provide a sandbox.

## Compatibility restrictions

The existing `stdlib/catalog.json` is the G0 catalog and is **unchanged**.
A normal `fa math firi stdlib: m` still refers to G0 exports, not G1.
G1.2.1 does not modify any Python/JS module loader, C++ compiler, KBC
format, Web Studio, browser release assets, G0.5 safety rules or Netlify.

This deliberately avoids surprising existing Kasa programs. The next phase
must select an **explicit** opt-in/version-qualified G1 syntax or compiler
selection strategy, preserve private-module environments, and demonstrate
reference/JS/native semantics independently.

## Verification in Google Cloud Shell

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g121-versioned-manifest
source .venv/bin/activate
python scripts/validate_g1_catalog.py
python -m pytest -q tests/test_validate_g1_catalog.py tests/test_g1_contract.py
python -m pytest -q tests/test_validate_kasa_catalog.py
python scripts/verify_local.py --profile full
git rev-parse --short HEAD
git status --short
```

Passing this suite is **manifest assurance only**, not G1 import parity.
Report skips separately from passes. No hosted CI, Netlify build or deployment
is needed.
