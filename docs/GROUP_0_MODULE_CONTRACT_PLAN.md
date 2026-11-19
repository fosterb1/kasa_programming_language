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
