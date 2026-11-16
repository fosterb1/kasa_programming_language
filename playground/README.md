# Kasa Playground — browser interpreter (v0.2 prototype)

**No CDN, Pyodide, remote Python runtime, or server-side code execution needed.**

The browser playground runs a **standalone JavaScript implementation of the Kasa 0.1 language** in a Web Worker. It implements Kasa's grammar and built-ins directly rather than downloading Pyodide. The original Python interpreter in [`src/kasa/core.py`](../src/kasa/core.py) remains the reference implementation for the language and the `kasa` CLI.

This is an independent browser runtime; although tested against the reference, it may have differences at extreme numeric sizes, unusual Unicode edge cases or floating-point representations. Report discrepancies rather than treating the browser version as authoritative.

## Redeploy to Netlify Drop

From the repository root, create the standalone ZIP:

```bash
python playground/build_site.py
```

Upload `dist/Kasa_Playground_Web.zip` to the **existing** Netlify site's **Deploys** page, or upload the extracted contents folder. It contains `index.html`, `app.js`, `style.css`, `worker.js`, and `kasa-runtime.js` at the ZIP root. It does **not** load Python or JavaScript code from any third-party CDN.

The old uploaded website remains unchanged until you replace its deployment. After uploading, hard refresh the site (`Ctrl + Shift + R`) and click **Run code**.

## Local hosting

For a local preview, run `python -m http.server 8000` in the repository root and visit http://localhost:8000/playground/ .

Use HTTP or HTTPS (not `file://`) because browsers restrict Web Workers opened from disk. No external network access is needed once the files are available.

## Features

- Twi-first Kasa code editor, six samples, Run / Check syntax, input for `bisa()` and `.kasa` downloads.
- Zero external runtime requests; output stays on-device, written with `textContent` to avoid HTML injection.
- Kasa lexer, AST parser, lexical-scope functions, loops, conditions, lists and built-in functions in the browser.
- 20,000 instruction-step ceiling, 50,000-character source and input caps, 64,000-character output cap, 48 call-depth ceiling and a 5-second Web Worker watchdog.
- Fresh variables per run; no data sent to a remote service.

## Architecture

```text
Netlify static files
  index.html / style.css / app.js
              |
           worker.js
              |
        kasa-runtime.js
              |
    Kasa text -> tokenizer -> parser -> AST -> evaluator -> output
```

The Web Worker and resource budgets help prevent accidental infinite loops, but this is a programming-language MVP, not a formally verified sandbox. Importantly, source text never passes into JavaScript `eval()` or `new Function()`.

## Developer verification

```bash
python -m pytest -q
node --check playground/kasa-runtime.js
node --check playground/worker.js
node --check playground/app.js
node --test tests/test_kasa_browser.cjs
```

The browser port must continue to match the Python reference interpreter on examples, syntax errors and core language features. Browser end-to-end testing on a deployed Netlify URL is still required after upload. GitHub Actions hosted runners currently cannot start because of the account billing lock; that is separate from the interpreter's local tests.
