# G1.2.4 — Experimental native/KBC1 source-prelink integration

**Status:** implementation proposed; Cloud Shell and native tests pending.
**Scope:** trusted-local development only, not production safe.

## Repository audit (2026-11-21)

1. `native/src/main.cpp` confirms `kasa-native run/check/compile`
   lexes, parses and compiles ordinary source and `run-bytecode/check-bytecode`
   calls the existing verified bytecode reader. Default `compile` emits KBC1;
   experimental `compile-kbc2` remains separately gated. Existing G0.5 evidence includes a
   Python/native/KBC1 differential test and a source-deletion/corruption gate
   (`scripts/verify_g05_native_kbc.py`,
   `scripts/verify_g05_kbc_independence.py`).
2. The native parser does **not** directly parse `fa ... firi stdlib`
   as import statements. The existing
   `scripts/link_kasa_modules_hygienic.py` statically rewrites reviewed
   G0 function-only modules into ordinary Kasa source, then the normal native
   compiler and KBC1 pipeline handle it.
3. `scripts/preflight_native_modules.py` validates imports/aliases/public
   exports and checks pinned source content before linking.
4. `native/README.md` documents a C++20 parser/compiler/stack VM, while
   `docs/KBC2_FORMAT.md` confirms KBC2 is opt-in, not an extension of
   default KBC1 module loading. G1 experimental imports require source
   transformation **before** invoking the native binary.
5. G0.5 output-path TOCTOU and shared-filesystem/source mutation race
   concerns remain, and true KBC runtime module loading is not implemented.
   There is no justification for changing the KBC1 binary format now.

## Narrow experimental G1.2.4 implementation

- `preflight(..., generation="g1")` validates the **separate pinned G1**
  manifest and its strict source allowlist; `generation="g0"` remains
  the default with unchanged result structure.
- `link_source(..., generation="g1")` reuses the existing restricted
  hygienic source rewriting, source-integrity checks, internal-name
  collision protections, export isolation and output-size limits with
  G1 source/exports. The synthesized internal prefix is deliberately
  retained as `__kasa_g05_` to avoid changing the vetted emitter.
- `scripts/link_g124_native.py app.kasa` is an explicit, no-publication
  **stdout-only** local source bridge. It does not compile a binary or
  write into the repository.
- `tests/test_g124_native_prelink.py` checks reference G1 execution
  against flattened ordinary Kasa, G0 default behavior and negative cases.
- `scripts/verify_g124_native_kbc.py` performs three live differential
  cases: Python G1 imports, Python flattened source, native C++ `run`,
  native `compile`, checked/runnable KBC1, and KBC1 execution *after*
  deleting the intermediate source, using temporary local files only.

**Important:** The phrase "native integration" here means a **build-time,
generation-selected G1 source prelinker** feeding the existing compiler.
Native C++ has no built-in G1 import parser, and KBC1 has no G1 module
opcode, package metadata or dynamic loader. No KBC2 claims. The source
linker is not approved for hostile shared workspaces or uploads, and
SHA-256 source pins are not publisher signatures.

## Cloud Shell verification gate

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g124-native-g1-prelink
source .venv/bin/activate
python -m pytest -q tests/test_g124_native_prelink.py
python -m pytest -q tests/test_hygienic_module_linker.py tests/test_native_module_preflight.py
python -m pytest -q tests/test_validate_g1_catalog.py tests/test_g122_python_imports.py
python scripts/verify_g124_native_kbc.py
python scripts/verify_g05_native_kbc.py
python scripts/verify_g05_kbc_independence.py
python scripts/verify_local.py --profile full
git rev-parse HEAD
git status --short
```

`scripts/verify_g124_native_kbc.py` requires a previously built native
executable at `build/kasa-local/kasa-native` on Linux or
`build/kasa-local/Release/kasa-native.exe` on Windows. If absent, build
the normal native target using the repository's existing documented
CMake steps before running that check. A missing native binary or
skipped scenario is **not** a pass.

If desired, inspect the flattened source without generating KBC:

```bash
cat > /tmp/g124-demo.kasa <<'KASA'
fa math firi stdlib: m
ma scores = [40, 60, 80, 90]
ka m.kasa_total(scores)
ka m.kasa_average_or(scores, 0)
KASA
python scripts/link_g124_native.py /tmp/g124-demo.kasa
```

Review any failures and platform-specific skips. **Do not merge before
owner confirmation**; Netlify and the Academy remain unchanged. G0.5
remains experimental trusted-local.
