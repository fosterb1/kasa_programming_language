# Group 0.4 — Opt-in JavaScript module execution experiment

**2026-11-20 | Implementation committed; independent Mac/Node verification pending**

This slice adds an **experimental fourth argument** to `KasaRuntime.executeKasa(source, input, mode, options)`:

```js
const result = KasaRuntime.executeKasa(
  "@math:m\nka m.kasa_sum([10,20,30])",
  "",
  "run",
  { experimentalModules: {
    math: { source: "<trusted verified math.kasa text>", exports: ["kasa_abs", "kasa_clamp", "kasa_sum"] }
  }}
);
```

Only the explicit `experimentalModules` option activates `@math:m` and dotted access. The normal `executeKasa(source, input, mode)` behavior remains unchanged. We have not introduced any unreviewed Twi or English reserved keyword.

## Contract and current proof

The JavaScript parser recognizes `module_import` and `module_member` only in opt-in mode. Namespace bindings remain outside the application's global environment. For selected module sources, the engine parses Kasa function declarations and executes them in a separate lexical `Environment`. Public exports are explicitly listed. Missing/duplicate aliases and modules, unknown or private exports and alias shadowing are rejected before running app statements.

`tests/test_js_experimental_modules.js` constructs source metadata from repository-pinned `stdlib/catalog.json`, independently checks SHA-256 against the catalog using Node's `crypto`, then tests Kasa math/collections execution and negative cases.

**Security limitation:** The interpreter API trusts its `experimentalModules` options. It **does not itself authenticate or SHA-256-verify arbitrary injected module metadata**. The Node test verifies the shipped local fixture; this is **not** proof that arbitrary caller-supplied source is safe. The browser currently has no packaged pinned-module loader, no Netlify/worker import mode and no UI exposed to learners. Do not pass untrusted module sources to this API.

**Parity limitation:** The Python experimental runner verifies catalog-pinned modules before binding; the JavaScript experimental API instead receives already-trusted source metadata from its caller. The two are **not equivalent for source trust**, and Python/JS behavior has not been fully conformance-tested. Current `check` mode validates experimental syntax but not module export selection.

## Run on Mac

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
node --check playground/kasa-runtime.js
node tests/test_js_experimental_modules.js
python -m pytest -q tests/test_experimental_module_source.py
bash scripts/mac_dev.sh quick
```

**Gates before actual playground enablement:** Test results from Mac, strict pinned-source packaging, worker protocol version and controlled option handoff, JS/Python error parity, default-mode regression, capability/step quota tests, dependency order, and Asante/Akuapem/educator review of final Twi import vocabulary. Native C++/KBC1 module support remains separate.
