# Netlify deploy — Kasa Playground with native WebAssembly

**Target:** Existing Netlify playground site `sunny-griffin-784c12` (the previously retained site), not a new arbitrary site. Check the current site and canonical production domain in the Netlify dashboard; do not assume the site name equals its current custom URL.

## Option A — Existing site connected to GitHub

Open the site's **Build & deploy / Continuous deployment** settings, and connect `fosterb1/kasa_programming_language` on branch `main`, or update its build settings. This repository includes `netlify.toml`:

- Base directory: repository root
- Build command: `bash scripts/netlify_build.sh`
- Publish directory: `dist/netlify`

The script detects an installed `em++` or installs pinned Emscripten 3.1.69 with emsdk, builds the genuine native WebAssembly runtime, makes a `--require-wasm` static website ZIP and extracts it into `dist/netlify`. A missing compiler, invalid WASM or failed build **fails deployment** rather than silently shipping JavaScript-only output.

## Option B — Upload to the *existing* site manually

On a machine with Emscripten active:

```sh
bash scripts/netlify_build.sh
```

Upload the contents of **`dist/netlify`** to the existing Netlify site's deploy screen (drag/drop deploy). Make sure the site root contains `index.html` and `native/kasa-native.wasm`. This manual upload changes the site only after Netlify processes it, not when the GitHub files are merged.

## Verification

Open the site using its actual published HTTPS domain. After the initial JavaScript startup, the Native WebAssembly option should become enabled and the status should indicate native availability. Choose the native engine, then run:

```kasa
ka "Maakye, Ghana!"
```

Confirm the output and status. Confirm that `/native/kasa-native.wasm` is served as WebAssembly and isn't a 404/HTML document. The build sets the `application/wasm` response type for `/native/*.wasm`.

## Embed inside the Learning Academy

The companion repository `fosterb1/kasa-learning-academy` adds **CMS → Website Settings → Playground Settings → Netlify Playground URL** after its additive database migration is applied. Paste the *published* HTTPS Netlify site-root URL, then **Save**. The `/playground` academy route dynamically embeds it via an iframe. No code redeploy is required for later URL edits.

`netlify.toml` currently allows iframe embedding from `https://kasa-learning-academy.vercel.app`. If the academy moves to a different domain, update this CSP directive with the additional exact HTTPS domain, then redeploy the playground. Third-party browser storage partitioning can mean draft storage inside the iframe differs from the same site opened directly.

## Verification status

An independent temporary Linux build using Emscripten 3.1.69 executed `bash scripts/netlify_build.sh` successfully and confirmed the publish folder contains `index.html`, worker, JavaScript runtime, Emscripten glue and a **491,371-byte native WASM binary**. This proves Netlify **build readiness**. It does not prove the live Netlify site was updated or academy integration was activated: those require authorized hosting/admin deployment.
