# G1.3 — Shared experimental cross-runtime conformance

**Status:** proposed implementation on `dev/g13-cross-runtime-conformance`;
**not independently run, reviewed, merged or deployed**.

## Goal

Prevent the experimental G1 subset from gradually diverging across the
Python reference runtime, the pinned-source JavaScript runtime, and the
unchanged C++ compiler/KBC1 execution path. Use **one** machine-readable
source and output/error corpus rather than silently asserting parity from
separate test suites.

## Scope implemented

- `tests/g13_cross_runtime_cases.json`: 12 cases (8 valid programs and
  4 invalid imports). Expected output is literal exact stdout, not
  approximate comparison. Cases include empty fallbacks, signed totals,
  exact half averages, strict thresholds, searches, distinct Twi-context
  text, Boolean results, and read-only collection checks.
- `tests/g13_js_fixture_runner.cjs`: verifies the reviewed, SHA-pinned G1
  metadata via the existing Node loader, then runs the **exact same
  source** through opt-in JavaScript module execution. Emits JSON with
  case IDs, outcomes and diagnostics; exits nonzero on any mismatch.
- `tests/test_g13_shared_conformance.py`: checks corpus shape, G1 Python
  execution, G1 prelink acceptance/rejection and JavaScript report
  without requiring a compiled native executable.
- `scripts/verify_g13_cross_runtime.py`: executes all 12 cases in
  Python and JavaScript. For the eight valid cases, also flattens source
  with the existing pinned G1 linker, executes the ordinary Python
  interpreter, invokes native C++ `check` and `run`, compiles to
  **unchanged** KBC1, verifies KBC1 and runs it after deleting the
  flattened source. The four invalid programs must fail before any
  Python or JavaScript output; they are **not** sent to native compiler.

## Engineering limits

- This gate tests only a **small, intentionally selected subset** of
  numeric and collection behavior. It does not imply universal semantic
  parity, randomized differential fuzzing, float precision agreement
  beyond covered examples, or performance benchmarking.
- Native G1 means **build-time trusted-local source prelinking**. There
  are no native `fa` grammar changes or KBC1 module opcodes.
- Native execution uses temporary output paths in a trusted developer
  environment, not hostile/shared filesystem safe publication.
- Existing Chromium G1 browser acceptance is a **separate** real-browser
  gate, with no new UI selector or public build/deploy in this PR.
- SHA-256 pins verify consistency, not publisher identity.
- G0.5 remains experimental trusted-local only. No PR #65 changes,
  Netlify deployment, Academy changes, or security promotion.

## Cloud Shell verification

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g13-cross-runtime-conformance
source .venv/bin/activate

python -m pytest -q tests/test_g13_shared_conformance.py
node tests/g13_js_fixture_runner.cjs
python scripts/verify_g13_cross_runtime.py

python scripts/verify_g124_native_kbc.py
python scripts/verify_g05_native_kbc.py
python -m pytest -q tests/test_g124_native_prelink.py
python scripts/verify_real_g1_browser.py
python scripts/verify_local.py --profile full

git rev-parse HEAD
git status --short
```

If the executable `build/kasa-local/kasa-native` is absent on Linux:

```bash
cmake -S native -B build/kasa-local -DCMAKE_BUILD_TYPE=Release
cmake --build build/kasa-local --target kasa-native --config Release
```

On Windows the gate expects
`build/kasa-local/Release/kasa-native.exe`.

**Do not count missing binary, skipped Chromium or failed runs as a pass.**
Record exact HEAD, counts and any skipped tests. No merge until owner
verification and final PR review.
