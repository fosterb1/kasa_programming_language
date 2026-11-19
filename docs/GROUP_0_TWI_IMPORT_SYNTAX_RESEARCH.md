# G0.3 — Twi-first module declaration research gate

**2026-11-20 | Specification experiment, not executable Kasa language syntax**

## Engineering semantics are separate from vocabulary

The import contract requires a statically identifiable trusted module ID, one unique local alias, and direct exported-member lookup. Two imports with overlapping *function names* must remain separate. Private declarations never become visible to the importer. Unsupported dynamic member access, duplicate aliases, unknown module IDs and missing exports must fail before executing application code where possible.

`scripts/study_kasa_module_syntax.py` explores this shape using the **English-only placeholder DSL** `module math alias m` and `m.kasa_sum`. Its parser **only checks standalone study text**. It cannot parse a genuine `.kasa` program; it never executes a program and does not modify the Kasa parser, lexer, CLI, browser or native VM. `tests/test_module_syntax_study.py` exercises the standalone contract and confirms real Kasa continues to reject the proposed syntax.

## Ghanaian authoring decision remains open

The actual Kasa form must use researched, natural Twi, reviewed under `docs/LANGUAGE_RESEARCH_POLICY.md`, rather than shipping `module` / `alias` as English language keywords. Candidate wording must be assessed in actual Twi *sentences* by Asante and Akuapem reviewers and an educator. The examples should include familiar Ghanaian contexts, e.g., a market sales total and school-fee balances, without assuming that translating English compiler jargon is good Twi.

No candidate word is accepted in this experiment. The future dot/member operator also requires design review since existing Kasa expressions have no member-access syntax. A dotted function expression is not equivalent to unrestricted Python object attribute access.

## Implementation gates

1. **Now:** run standalone syntax-contract tests on Mac and record pass/failure evidence.
2. Obtain linguistic evidence and documented human review for final keyword choices. Keep the existing legacy Kasa keyword spellings stable.
3. Add a versioned parser AST contract for import declarations and explicit member expressions behind a compatibility test gate; reject shadowing/duplicate aliases, unknown modules and non-exported functions.
4. Wire the Python interpreter only to pinned catalog sources, then implement the same behavior in JavaScript and the native compiler/VM. Bytecode changes require an explicit format/version policy. No network package resolution or arbitrary local file imports.
5. Add shared cross-runtime conformance fixtures and Ghanaian beginner examples, including localized errors as a separately reviewed layer.

## Mac validation (from existing checkout)

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
python -m pytest -q tests/test_module_syntax_study.py tests/test_bind_kasa_catalog.py
bash scripts/mac_dev.sh quick
```

**Evidence:** commands are provided, not claimed to have run here.
