# G0.3 — First executable .kasa module-source experiment

**2026-11-20 | Experimental Python-only, opt-in. NOT APPROVED LANGUAGE SYNTAX.**

Kasa can now parse a complete `.kasa` program containing provisional module declarations and execute calls such as `m.kasa_sum(...)` through the pinned standard-library catalog, **only when launched through the experimental Python runner**. Regular Kasa CLI, browser JavaScript and native compiler still reject this syntax.

## Provisional grammar

```kasa
@math:m
@collections:c

ma nkontaa = [10, 20, 30]
ka m.kasa_sum(nkontaa)
ka c.kasa_contains(nkontaa, 20)
```

`@math:m` means “select the allowlisted math module under alias m,” but **the punctuation is temporary internal notation**. It is not a claim that `@` or English "import" is culturally or linguistically appropriate Twi. Review real Twi vocabulary under `docs/LANGUAGE_RESEARCH_POLICY.md` before stabilizing source grammar. Existing identifiers like `ka`, `ma`, `nokware` remain unchanged.

## macOS/Linux developer trial

Activate the project's Python environment and run from repository root:

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
python -m pytest -q tests/test_experimental_module_source.py tests/test_configure_kasa_modules.py tests/test_module_member_execution.py
python scripts/run_kasa_modules_experimental.py stdlib/demos/group0_source_import_experiment.kasa
bash scripts/mac_dev.sh quick
```

Expected example stdout:

```text
60
nokware
```

These tests are committed but **have not yet been run independently**.

## Design and safety properties

- Opt-in `parse(source, experimental_modules=True)` provides `module_import` and `module_member` AST nodes; default parser/tokenizer and legacy `.kasa` programs are unchanged.
- Import declarations must be at the top of the program; nested or late declarations are rejected.
- Module names come from the exact G0.2 catalog allowlist, whose files are pinned by SHA-256. No arbitrary path, network download, package manager or new host capabilities.
- Duplicate module imports, alias collisions and unknown modules fail before application statements execute. Export access checks reject private/unknown members and unknown aliases before output.
- Underlying module functions use the existing Python interpreter's call budget, recursion and output limits. There is no KBC1/native support.
- Source files are parsed as Kasa only: the runner never evaluates host-language Python from the file.
- This is an educational compiler prototype, **not an untrusted-code sandbox**. The Python runtime's `run()` method resets its step counter after module declarations are initialized; a full language spec must define how all initialization work is charged.

## Next gates

1. Run focused Mac tests and the sample; fix real failures, do not infer success merely because files were committed.
2. Align the declarative AST contract with the browser runtime and native compiler, with shared location/error tests.
3. Review candidate Twi import phrases with Asante and Akuapem speakers and an educator; document provenance, grammar, and keyboard usability.
4. Replace the provisional `@`-format and experimental-only runner with reviewed official grammar only after cross-runtime work, regression evidence and versioning decisions.
