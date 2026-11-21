# G1.2.3 — JavaScript G1 contract parity and worker opt-in

**Status:** Implemented on a development branch; **local tests pending**.

## Scope

The JavaScript Kasa runtime already supports **opt-in** function-only
module metadata through `executeKasa(source, input, mode,
{experimentalModules: modules})`. This milestone adds a separately
reviewed G1 metadata loader, not a new parser or stable import system.

- `scripts/load_g1_js_modules.cjs` reads only the reviewed local
  `stdlib/g1/catalog.json` and two G1 sources; checks explicit
  manifest schema, exports, source paths and canonical LF UTF-8 SHA-256.
  Node-only, development/test helper; **not** a remote module fetcher.
- `tests/test_js_g1_contract.cjs` executes all **19** G1.1 Python
  reference source/output fixtures in the JavaScript interpreter using
  explicit namespaced function calls; checks G0 compatibility, invalid
  members/aliases and tampered source.
- `playground/worker.js` accepts `experimentalGeneration: "g1"`
  in addition to the existing `experimentalModules: true` request.
  The G1 source bundle gate is **false by default**, with a distinct
  `./kasa-g1-pinned-modules.js` asset name and global
  `KasaG1PinnedModules`; the existing G0 path remains the default.
  The separately verified bundle must be produced by an audited build
  stage before any real browser can opt into G1.
- `tests/test_js_g1_worker.cjs` simulates the worker with Node VM
  with/without a G1 bundle and rejects unavailable, invalid-generation,
  G0-only and native-engine cases.

## Known boundaries

The 19 JS tests use the existing G1.1 fixture cases, adapting top-level
function names to their explicit import aliases; **not** a broad
randomized Python/JS differential suite or a full browser test. The
Node worker simulation is not Chromium. No `kasa-g1-pinned-modules.js`
asset is generated or committed by this milestone, and no Studio
control, CMS, Academy, Netlify or production deployment is changed.

Source hashes establish **consistency**, not publisher signatures or
sandboxing. G0.5 remains trusted-local experimental and untrusted
public program execution is not approved. Native C++/KBC G1 integration
remains separately gated.

## Independent Google Cloud Shell test gate

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g123-js-g1-compat
source .venv/bin/activate
node --check playground/worker.js
node --check scripts/load_g1_js_modules.cjs
node tests/test_js_g1_contract.cjs
node tests/test_js_g1_worker.cjs
node tests/test_js_experimental_modules.js
node tests/test_js_worker_modules.js
python scripts/verify_local.py --profile full
git rev-parse --short HEAD
git status --short
```

If these pass, review for merge. Then build a separate, hash-checked G1
browser packaging step and run **real Chromium** module tests before
claiming deployed-browser parity.
