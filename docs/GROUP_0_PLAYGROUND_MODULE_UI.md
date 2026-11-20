# G0.4 — Experimental modules in the playground editor

**2026-11-20 | Implemented; Mac and real-browser verification pending**

The hosted-or-local Kasa playground now offers a manual **Experimental modules (JavaScript only)** checkbox and an optional **Market baskets · experimental modules** example. Selecting this example enables the switch; selecting an ordinary example returns to normal mode. The switch itself remains manually controllable when editing or opening `.kasa` files.

The example invokes the two locally pinned libraries through provisional syntax:

```kasa
@math:m
@collections:c
ma nneɛma = [10, 20, 30]
ka m.kasa_sum(nneɛma)
ka c.kasa_contains(nneɛma, 20)
```

Expected output:

```text
60
nokware
```

The UI sends `experimentalModules: true` **only when the checkbox is enabled** in the existing worker `EXECUTE` message. In this mode the UI routes the request to the JavaScript engine; native WebAssembly has no supported imports. The worker loads trusted hash-checked module assets only in the built static archive, and non-packaged development workers fail closed.

The checkbox is **not automatically enabled for arbitrary opened files** and the default editor continues to use standard Kasa syntax. Existing Twi keywords and default execution paths remain intact. `@math:m` is a provisional technical notation, **not approved Twi import grammar**.

## Testing gate

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
node --check playground/app.js
node tests/test_js_playground_module_ui.js
node tests/test_js_worker_modules.js
python -m pytest -q tests/test_playground_module_ui.py tests/test_playground.py
python playground/build_site.py
bash scripts/mac_dev.sh quick
```

Open the extracted archive via a small local HTTP static server (rather than opening `index.html` directly via `file://`) to verify the worker and offline assets. In the UI, select the market baskets example, run and check output `60` / `nokware`; then switch back to **Hello, Ghana** and confirm ordinary programs still work. The Node DOM/Worker test verifies event-handling logic but is not evidence of real browser rendering.

## Hosting decision

The project owner has explicitly discontinued Netlify. This feature is hosting-neutral: **no provider selected or deployed here**. The existing `dist/Kasa_Playground_Web.zip` filename is a historical artifact label, not a Netlify target. Do not implement provider-specific hosting or CMS wiring until the owner identifies the current workflow.

The Academy and KBC1/native compilers remain unchanged; native module support and reviewed Asante/Akuapem/educator Twi wording require separate milestones.
