# Kasa → Academy approved release process (Phase 4A)
Updated: 2026-11-19

## Purpose
A verified language release can update Kasa Academy's first-party Studio in one atomic GitHub commit. No hosted GitHub Actions runner is required; the release is triggered **locally** after tests and review, not on every experimental commit.

## Prerequisites
- Local checked-out Kasa language repository.
- Emscripten SDK activated (`em++` available), Python 3 and Node.js.
- A fine-grained GitHub token with **Contents: Read and write** access to `fosterb1/kasa-learning-academy` only.
- The Academy's GitHub main branch must be current; do not force-push over concurrent work.

## Procedure

```sh
# 1. Build native compiler and VM
bash native/wasm/build.sh

# 2. Independently verify the native artifacts and JS browser contract
node native/wasm/validate_artifacts.mjs
node --test tests/test_kasa_wasm.cjs tests/test_kasa_browser.cjs
python playground/build_site.py --require-wasm

# 3. Check exactly which files need updating; never writes to GitHub
python scripts/release_to_academy.py --academy ../kasa-learning-academy

# 4. Publish only after deliberate review
# Unix/macOS:
export GITHUB_TOKEN='YOUR_FINE_GRAINED_TOKEN'
python scripts/release_to_academy.py --publish --yes-reviewed
```

For Windows PowerShell set `$env:GITHUB_TOKEN = "YOUR_FINE_GRAINED_TOKEN"` in the current terminal session and run the same Python command. A Windows or WSL installation capable of building the Emscripten target is required for step 1.

The **publish command reruns** WASM validation, browser-runtime tests, the WebAssembly packaging check and the offline publisher unit tests before contacting GitHub. It refuses absent or invalid WASM and a missing or incomplete Emscripten loader.

## Publication and safeguards
- Creates a content-addressed 12-file release: 11 website assets plus `release-manifest.json`.
- Hashes every published asset (SHA-256) and records its byte length, including the actual `.wasm` executable.
- Revisions the service-worker cache when the source changes.
- Stages all new assets in GitHub's Git Data API and advances the Academy's `main` branch with **one non-force commit**.
- A competing branch update prevents forced overwrite. No CMS database records, course videos, transcripts or student data are touched.
- Academy `tests/academy-studio.test.mjs` confirms all checked-in files match the published manifest.
- The live native binary is a compiled artefact. Releasing a fresh language revision requires compiling the actual current C++ source first, not reusing an old downloaded binary.

## After release
1. Confirm Vercel deploys the new Academy commit successfully.
2. Verify `/playground` shows Native WebAssembly available.
3. Run sample arithmetic, loops, list mutation, functions, Unicode identifiers and error handling with Native selected.
4. Confirm JS fallback works.
5. Run `node --test tests/*.test.mjs` in an Academy checkout.
6. If any gate fails, do not approve/continue the deployment. Use a known-good Git revision to restore the prior Studio bundle, then retest.

## What remains
Publication remains a **release-owner initiated** command, not a background event watcher. This deliberately avoids unreviewed updates and paid hosted Actions. The automation handles artifact collection, validation and atomic GitHub synchronization *after* a developer invokes the approved release. A later signed/tagged release process may further tighten provenance.
