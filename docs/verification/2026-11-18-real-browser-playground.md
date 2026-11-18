# Browser playground verification — 2026-11-18

## Capabilities now present

The Kasa playground already had a pure JavaScript interpreter running in a dedicated Web Worker, a code editor, examples, engine selection, run/check controls, program input and Kasa source download. This milestone adds:

- **Open a local `.kasa` source file** through the browser's file chooser. UTF-8 files are read locally, checked against the 50,000-byte source limit and placed in the editor; no code runs without explicitly pressing Run.
- **Save source drafts on this device** using the browser's `localStorage` key `kasa.playground.source.v1`; restore them on reload. Storage can be disabled or unavailable, in which case the playground still runs. The program-input box is **never** persisted.
- **Reset draft** to the bundled Hello Ghana example, clear temporary program input and remove the stored source draft.
- **More accurate engine messaging**: JavaScript always starts; native WebAssembly is only available when a verified bundled WASM engine has actually loaded.

Local source storage is not an encrypted private vault: someone with access to the same browser profile can inspect it. The website itself should not claim absolute security or confidentiality for sensitive source code. Importing or exporting files is a local browser operation and does not send a file to the server by design.

## Evidence: real Chromium execution (not just Node Worker mocking)

`scripts/verify_browser_playground.py` starts a loopback-only HTTP server and exercises the actual playground DOM and worker in a headless Chromium instance through Playwright. It verifies:

1. Page loads and a real Web Worker makes Run available; JS-only deployment does **not** offer Native WebAssembly selection.
2. Hello Ghana code executes, and the UI identifies the **JavaScript** engine.
3. Syntax checking does **not** execute print statements.
4. Source persists across reloads, while private program input does **not**.
5. Import a real UTF-8 `.kasa` file containing Akan characters and execute it.
6. Runtime errors are shown without permanently disabling Run.
7. Switching built-in examples updates the local draft; downloading the program produces a real `.kasa` file.
8. Reset removes the draft and restores the initial example across reloads.
9. No uncaught page errors during these tested interactions.

**Independent execution:** Real Chromium headless on Linux passed the above browser flow. Existing Node semantic and simulated WASM-protocol tests also passed **234/234**. This is direct JavaScript-browser evidence on **one Chromium environment**; it does **not** certify Chrome/Edge/Firefox/Safari on actual devices or any real Emscripten native WASM runtime.

## Reproduce locally

Install the optional test-only dependency and browser binary (not required for learners or normal Kasa operation):

```sh
python -m pip install playwright
python -m playwright install chromium
python scripts/verify_browser_playground.py
```

On Linux, Playwright may also require system libraries, provisionable with `python -m playwright install-deps chromium` from an appropriate privileged environment.

The test launches an ephemeral local server, blocks Service Workers for isolation, uses a fresh browser profile, and closes the server and browser. No external site, account, hosted API or paid GitHub Actions job is required.

## Remaining browser gates

- **Real Emscripten WASM end-to-end**: compile `native/wasm/build.sh`, build the website with `python playground/build_site.py --require-wasm`, host the resulting ZIP and run an actual worker-backed WASM execution. Existing `tests/test_kasa_wasm.cjs` uses a simulated module and is not enough.
- Cross-browser validation, including Firefox, Safari/WebKit and Edge.
- PWA/offline scenarios with an enabled service worker and full network loss.
- Screen-reader/a11y review, mobile keyboard/touch behavior, and deployment verification on the actual public host.

**Progress estimates are unchanged**: the Kasa 0.4 alpha checklist remains 90%, and Kasa 1.0 readiness remains approximately 35%; the real-browser JS result is stronger evidence, not a claim of WASM certification.
