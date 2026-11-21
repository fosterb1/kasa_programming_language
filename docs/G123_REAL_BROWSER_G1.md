# G1 experimental browser packaging and real Chromium gate

**Status:** Code committed on development branch; independent verification pending.

## Scope

`playground/build_site.py --include-g1` now opts into a **separate**
verified G1 static asset `kasa-g1-pinned-modules.js`. The builder reads
the G1 schema-v1 manifest, uses the strict Python G1 validator, rechecks
the exact source bytes against SHA-256 pins, emits inert JSON metadata,
and flips worker and offline-cache flags only for the opted-in ZIP.

`build_bundle(..., include_g1=False)` is the default. With no flag, G1
is absent and disabled; G0 bundles, browser UI, and existing semantics
remain unchanged. The generated zip is a **local test artifact**.
Do not upload to Netlify, publish Academy assets, or treat this as a
public release. Native KBC/WASM G1 imports remain unsupported.

`tests/test_g1_browser_packaging.py` checks both ZIP modes, source
identity and tamper rejection.

`scripts/verify_real_g1_browser.py` uses Playwright and **actual
Chromium**, loopback HTTP and a worker instantiated from the extracted
opt-in ZIP. It tests the same 19 G1.1 reference-output fixtures, G0
default imports, default parser rejection, private exports, native
engine refusal and invalid generation. This is an opt-in **JavaScript
Web Worker** validation, not native WASM G1 support or a proof of
public-hosting correctness.

## Independent verification in Google Cloud Shell

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g123-browser-g1-packaging
source .venv/bin/activate
python -m pytest -q tests/test_g1_browser_packaging.py
python -m pytest -q tests/test_validate_g1_catalog.py
node tests/test_js_g1_contract.cjs
node tests/test_js_g1_worker.cjs
python scripts/verify_real_g1_browser.py
python scripts/verify_real_module_browser.py
python scripts/verify_local.py --profile full
git rev-parse --short HEAD
git status --short
```

If Playwright Chromium is not installed on Cloud Shell:

```bash
python -m pip install playwright
python -m playwright install chromium
```

Do not classify missing-browser or skipped tests as passed. These
commands should be run without triggering any live Netlify build.

## Known limits

- The browser UI does **not** expose a G1 selector. The real-browser
  test issues explicit `experimentalGeneration: "g1"` worker messages.
- G1 source pins check local consistency, not publisher authentication.
- G0.5 untrusted-code safety remains experimental, trusted-local only.
- Actual release packaging, public browser delivery, native C++/KBC
  parity, and genuine school/learner pilots still require separate gates.
