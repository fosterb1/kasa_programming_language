# Group 0.4 — Verified browser bundle and opt-in worker protocol

**2026-11-20 | Implementation committed, Mac verification pending**

## What changed

The static playground packaging script `playground/build_site.py` now reads the exact two allowlisted standard-library modules from `stdlib/catalog.json`, verifies each canonical LF source SHA-256 and expected export list, rejects linked module paths, and writes a deterministic `kasa-pinned-modules.js` file into the Netlify ZIP. The bundle's cache revision includes these bytes.

The packaged worker is patched to `KASA_HAS_PINNED_MODULES = true` and can load that file with `importScripts` **only when a worker EXECUTE request explicitly includes `experimentalModules: true`**. Normal requests use the existing JavaScript/native selection logic. If experimental modules are requested with `engine: "native"`, the worker rejects the request rather than silently changing engines. Unpackaged workers refuse experimental modules because they contain no verified library asset.

The packaged service worker includes the local module asset in its offline precache. The unbundled development service worker does not refer to that missing file.

**Current user-facing UI:** No experimental-modules checkbox has been added; `playground/app.js` does not yet send the new flag. This is a worker protocol and packaging foundation, **not a Netlify rollout** or an Academy integration.

## Tests

- `tests/test_playground.py`: ZIP must contain the generated module asset; packed worker/service-worker flags are enabled; altered standard-library source is rejected before packaging.
- `tests/test_js_worker_modules.js`: Node VM worker simulation checks standard execution, missing-asset failure, module invocation, native rejection and unmodified legacy behavior. This simulation does not establish actual-browser deployment.
- Existing `tests/test_js_experimental_modules.js`: expected positive and negative module-runtime behavior.

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
python -m pytest -q tests/test_playground.py
node tests/test_js_experimental_modules.js
node tests/test_js_worker_modules.js
node --check playground/worker.js
python playground/build_site.py
bash scripts/mac_dev.sh quick
```

Inspect the generated `dist/Kasa_Playground_Web.zip` offline if necessary; it has **not** been deployed automatically. Do not deploy until these commands pass.

## Limits and next gates

This source bundle's SHA-256 validates its packaged contents against the checked-in manifest; **it is not an independently signed publisher authenticity guarantee**. The JavaScript runtime still trusts caller-provided module metadata when used as an API without this controlled worker. No arbitrary uploaded module code, npm packages, runtime network imports or native/KBC1 module execution have been enabled. The `@math:m` syntax is a provisional engineering notation and **not approved Twi vocabulary**.

Next work: confirm Mac results, add a deliberate user opt-in control to the playground and a Ghanaian market example, test with a real browser and then design shared Python/JS conformance fixtures. Final Kasa import naming requires Asante and Akuapem speaker and educator review.
