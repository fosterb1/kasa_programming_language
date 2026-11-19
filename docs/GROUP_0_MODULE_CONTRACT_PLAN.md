# Group 0 — Module contracts and namespace implementation sequence

**Date:** 2026-11-19  
**Status:** Next engineering specification, **not implemented import syntax**.  
**Prerequisite accepted:** pinned source linker passed user Windows unit, Python, native and KBC1 example verification (see `GROUP_0_MODULE_LINKER_CHECKPOINT.md`).

## Goal

A Kasa program should reference a library without receiving its private functions or globals in the application scope. Start with two existing Kasa-authored libraries, not arbitrary third-party code.

## Metadata shape proposed for the first experimental module catalog

```json
{
  "schema_version": 1,
  "modules": [
    {
      "id": "math",
      "source": "stdlib/experimental/math.kasa",
      "exports": ["kasa_abs", "kasa_clamp", "kasa_sum"],
      "dependencies": [],
      "content_identity": "<verified SHA-256 of canonical LF UTF-8 source>"
    },
    {
      "id": "collections",
      "source": "stdlib/experimental/collections.kasa",
      "exports": ["kasa_count_equal", "kasa_contains"],
      "dependencies": [],
      "content_identity": "<verified SHA-256 of canonical LF UTF-8 source>"
    }
  ]
}
```

This is **illustrative metadata**; placeholder hashes must be replaced by calculated values before implementing the catalog. Dependencies must be a closed allowlisted graph. Module IDs and exports are case-sensitive and explicitly validated. Version pinning should not be replaced with runtime source searching.

## Surface syntax choices (requiring Twi language-policy approval)

A future syntax must name a module and alias without relying on globally injected function names. Example below is **pseudocode only**:

```text
# Not currently valid Kasa
<module declaration> math <alias> m
ka m.kasa_sum([1, 2, 3])
```

The current Kasa parser does not define a member-access expression `m.kasa_sum`; both a module-use declaration and dotted-name/member resolution need a grammar and bytecode contract. Retain the existing `ma`, `ka`, `dwumadie` and other vocabulary unmodified until reviewed.

## Non-negotiable name and execution rules

1. Import creates one namespace binding; exported functions are visible only through its alias. Existing application globals and built-ins remain unchanged.
2. Module-internal names are not exported by default. Public exports are explicit and must refer to top-level declared functions.
3. Two modules may export the same function name without collision, but aliases must be unique within an importing scope.
4. Dependency graph loading must be deterministic and reject cycles before module execution; failed partial loads must not leak names.
5. No imported source may gain file, network, clock or other permissions beyond the caller's host capability policy.
6. Library source identity must be pinned at compilation. KBC1 must not resolve arbitrary changing external files at runtime. A future bundle format/version or carefully specified compiler prelink is required.
7. Unsupported platform features fail explicitly, never silently degrade into host-specific behavior.
8. Runtime budgets include module initialization and function invocation. Cross-runtime Kasa semantics stay aligned with the existing portable subset.

## Group 0 remaining delivery slices

| Slice | Implement | Tests required | Status |
|---|---|---|---|
| G0.1 | Pinned source linker and safety checks | Input paths, content changes, no overwrite, Python/native/KBC example | **Targeted Windows proof completed** |
| G0.2 | Manifest catalog + declared export/dependency validator | Unknown/duplicate exports, invalid IDs, changed content, missing dependencies, cycle detection | **Planned** |
| G0.3 | Reviewed Kasa import/member syntax and reference-engine namespaces | Two modules sharing names, alias collision, local/private names, missing module, original syntax regressions | **Planned** |
| G0.4 | JavaScript/browser runtime parity | Shared success + expected-error fixtures | **Planned** |
| G0.5 | Native compiler, VM and bytecode self-contained dependency model | Windows native and KBC test, version mismatch and corruption handling | **Planned** |

At each slice, report **what changed, how it works, what it enables, actual test evidence, unresolved limits, next slice**. Proceed to Group 1 only after explicit G0 exit criteria are satisfied or a documented phased exception is approved.

## G0.2 implementation checkpoint (2026-11-19)

**New source:** `stdlib/catalog.json` records two current Kasa-authored modules with stable IDs, exact repository paths, explicit exported functions, no dependencies, and canonical LF UTF-8 source SHA-256 identities. `scripts/validate_kasa_catalog.py` validates the allowlist, manifest schema, declarations against Kasa's parser AST, source hashes, dependencies and deterministic dependency-first order. `tests/test_validate_kasa_catalog.py` tests positive and negative cases.

**Why:** the previous G0.1 linker trusted a hardcoded pair of Git SHA-1 blob IDs and broadly discovered function declarations. The new G0.2 metadata separates **public exports** and module identities from private implementation and prepares future namespace/import semantics. SHA-256 is a source consistency check, **not package signature verification**.

**What it does now:** Run `python scripts/validate_kasa_catalog.py`; if successful the catalog's exact two known library source files have valid syntax, no executable top-level statements, declared exports that exist, and a closed acyclic dependency graph. Malformed manifests, duplicate keys, invalid names, hashes, unsafe source paths and cycles are rejected. No Kasa application is executed by this validator.

**What it does NOT do:** It does not implement Kasa imports, namespaces or exports at runtime, install dependencies, or yet replace the G0.1 linker's independent hardcoded allowlist. Browser/JS and C++ runtimes remain unchanged. In a later integration stage, the validated catalog can feed a checked build-time linker and self-contained bytecode bundle.

**Test gate:**

```bat
git pull --ff-only
python -m pytest -q tests/test_validate_kasa_catalog.py tests/test_link_kasa_stdlib.py
python scripts/validate_kasa_catalog.py
python -m kasa run build/stdlib-linked/group0-demo-001.kasa
```

The last command runs the **previously generated** source only if it exists on this machine. Existing G0.1 native/KBC1 evidence remains valid and is not evidence that G0.2 has been separately run or approved. The new tests are **pending Windows verification**.

**Next G0.3 decision:** whether to introduce reviewed Kasa syntax for module use and member access or to first integrate the manifest into build-time source linking, always without granting unapproved I/O capabilities.


## G0.3 first preflight checkpoint (2026-11-20)

**Implemented, not yet tested on Windows:** `scripts/plan_kasa_modules.py` reads the validated G0.2 catalog and checks explicit command-line module-to-alias requests without interpreting a Kasa program. For example, `python scripts/plan_kasa_modules.py --use math:m --use collections:c` emits deterministic JSON including public exported names, dependency-first load order, and an empty capability-grant list. It rejects duplicate module selections, alias collisions, unsafe/reserved aliases, unknown IDs, missing dependencies and cycles. `tests/test_plan_kasa_modules.py` covers positive and negative paths.

**Critical scope limit:** this is a **read-only namespace plan**; no import grammar, member expression, isolated runtime scope, module execution, JS parity or native/KBC bundling is implemented. Aliases are provisionally ASCII identifiers and are **not** approved Twi syntax. The script does not modify the app or linker. The underlying catalog still checks source hashes.

**Local proof requested (no hosted CI required):**

```bat
git pull --ff-only
python -m pytest -q tests/test_validate_kasa_catalog.py tests/test_plan_kasa_modules.py
python scripts/plan_kasa_modules.py --use math:m --use collections:c
```

An external checkout/test attempt in the assistant container could not run because DNS resolution of github.com failed. No new test pass is claimed. Next: verify preflight on Windows, then review grammar and scope mechanics before shipping actual namespace access.
