# Kasa Playground (prototype)

A browser-based editor for **Kasa 0.1.0** using the actual Python interpreter (`src/kasa/core.py`) via [Pyodide](https://pyodide.org/). No Python or server-side code execution is required for the visitor.

## Run locally

From the **repository root** (not `playground/`):

```bash
python -m http.server 8000
```

Open **http://localhost:8000/playground/** in a modern browser with internet access. Do not open `index.html` via `file://`: workers and `fetch()` need a web origin. The first load downloads the pinned Pyodide `v314.0.8` engine, trying jsDelivr and UNPKG and can take several seconds.

## Publish immediately with Netlify Drop (no GitHub Actions needed)

From the repository root, build the bundle with `python playground/build_site.py`. This generates `dist/Kasa_Playground_Web.zip`. The ZIP has `index.html`, JavaScript, CSS, and the original Kasa `core.py` in the paths expected by the Worker. To publish it, open https://app.netlify.com/drop/ and upload the ZIP. Netlify's current Drop interface accepts ZIP archives (or unzip and drag the containing folder), and it will return a public URL. Open that URL and try the Hello sample. No server-side Python is used. Remember: the browser still downloads the Pyodide engine from jsDelivr.

## Publish online (GitHub Pages)

The playground uses relative paths to `/src/kasa/core.py` and `/playground/runner.py`. **Serve the repository root as the site root**. After merging the playground branch, go to **Settings → Pages** in your GitHub repository, choose **Deploy from a branch**, branch **main**, folder **/(root)**, and save. Once GitHub reports a successful deployment, visit:

**https://fosterb1.github.io/kasa_programming_language/playground/**

This URL is **not live until Pages has been enabled and deployment succeeds**. GitHub Actions is currently blocked by an account-level billing lock and that may also prevent Pages deployment; resolve the billing issue if GitHub reports a deployment failure. Alternatively upload a copy of the repository to a static hosting service keeping the directory structure intact.

## Features

- Edit `.kasa` code, switch between six educational samples, run or syntax-check.
- Enter input for `bisa()` (one response per line).
- Download source as a `.kasa` file.
- Fresh interpreter instance per run; variables are not shared between runs.
- Browser Web Worker isolation with hard execution timeout, plus Kasa step limits and output caps.
- No submission or storage of users' source code on an application server.

## Security, limitations and compatibility

- The Python engine uses pinned Pyodide **314.0.8** and tries three sources: `https://cdn.jsdelivr.net/pyodide/v314.0.8/full/`, `https://unpkg.com/pyodide@314.0.8/`, and `https://cdn.jsdelivr.net/npm/pyodide@314.0.8/`. An internet connection is required. If the first source fails, the Worker tries the other two. Browser or network policies can still block all of them.
- Program execution runs locally in a separate Worker and stops after **5 seconds**; interpreter startup has a separate **120-second** timeout. Large/infinite programs are stopped by resource limits, and a timed-out Worker is terminated. This is defense-in-depth, **not a verified security sandbox for untrusted Python source**.
- Kasa's own parser accepts Kasa syntax, not Python. The playground's Python bridge never `eval()`s or `exec()`s user-entered Kasa source.
- The page uses plain text output (`textContent`), not HTML rendering, so user program output cannot inject page markup.
- Colab and the local CLI remain options for programs requiring more time or larger outputs.
- Twi vocabulary and teaching content require review by educators and fluent speakers.

## Developer checks

```bash
python -m pytest -q
node --check playground/app.js
node --check playground/worker.js
```

`tests/test_playground.py` exercises the runner against the same interpreter as the CLI. Browser end-to-end smoke tests require a working network connection to load the external Pyodide CDN and are **not** yet performed automatically in GitHub Actions while the account is billing-locked.

## If you see `importScripts` failed

This indicates a blocked/unavailable Pyodide download, **not a Kasa syntax error**. Click **Retry engine** and let the page try alternate CDN providers. If that fails, open browser Developer Tools (F12 → Network), reload, and inspect the failed `pyodide.js` requests. Consider checking filtering extensions, network restrictions, or a different browser. The script URL used in the original playground is valid according to official Pyodide 314.0.8 docs; failure in a particular browser does not establish that the Pyodide release is missing.

If you previously uploaded a ZIP to Netlify Drop, **rebuild and redeploy** it using `python playground/build_site.py`. Updating GitHub does not change an already uploaded Netlify ZIP. If using a restrictive content-security policy, allow the external runtime and Web Worker.
