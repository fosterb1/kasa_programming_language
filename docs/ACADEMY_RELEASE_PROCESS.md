# Kasa → Academy reviewed Studio release process (Phase 9C)
Updated: 2026-11-20

## Purpose
A verified language release can update Kasa Academy's first-party Studio in one atomic GitHub commit. No hosted GitHub Actions runner is required; the release is triggered **locally** after tests and review, not on every experimental commit. **This Phase 9C publisher revision is not itself a deployment of a new native compiler:** it needs the user's current verified local Emscripten binaries and test results before publication.

## Prerequisites
- Local checked-out Kasa language repository.
- Emscripten SDK activated (`em++` available), Python 3 and Node.js.
- A fine-grained GitHub token with **Contents: Read and write** access to `fosterb1/kasa-learning-academy` only.
- The Academy's GitHub main branch must be current; do not force-push over concurrent work.
- The Academy CMS and curricula **may be upgraded during active development**. Such upgrades belong in the Academy repository, with reviewed Payload/DB migrations, focused tests, and preservation of existing records, uploads, lesson videos and transcripts. They are not in the scope of this browser-asset publisher.

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

The **publish command first checks that both native Emscripten artifacts are newer than native sources**, then reruns WASM validation, browser-runtime tests, the WebAssembly packaging check, the experimental JS/Python module tests and the offline publisher unit tests before contacting GitHub. Timestamp freshness is only a fail-closed heuristic, not cryptographic build provenance. It refuses absent or invalid WASM and a missing or incomplete Emscripten loader.

## Publication and safeguards
- Creates a content-addressed **14-file Studio publication**: 13 tracked website assets (including a verified, generated pinned `math` and `collections` library asset) plus `release-manifest.json`. The pinned module sources come only from the allowlisted catalog; the worker and service-worker opt-in flags are enabled in release output.
- Hashes every published asset (SHA-256) and records its byte length, including the actual `.wasm` executable.
- Revisions the service-worker cache and the versioned worker URL when the browser runtime or pinned modules change.
- Stages all new assets in GitHub's Git Data API and advances the Academy's `main` branch with **one non-force commit**. Publication is always explicit; never run `--publish` merely to preview differences.
- A competing branch update prevents forced overwrite. No CMS database records, course videos, transcripts or student data are touched.
- Academy `tests/academy-studio.test.mjs` checks bundled first-party files and SHA-256 metadata. Its build refreshes the release manifest from the actual Academy assets; the language publisher separately includes hashes for all 13 tracked Studio files.
- The live native binary is a compiled artefact. Releasing a fresh language revision requires compiling the actual current C++ source first, not reusing an old downloaded binary.

## After release
1. Confirm Vercel deploys the new Academy commit successfully.
2. Verify `/playground` shows native WebAssembly available and experimental imports remain available in the JavaScript Studio mode.
3. Run sample arithmetic, loops, list mutation, functions, Unicode identifiers and error handling with Native selected.
4. Confirm JS fallback works, and experimental `fa math firi stdlib: m` imports print expected results in the JavaScript module mode; native module imports remain unsupported.
5. Run `node --test tests/*.test.mjs` in an Academy checkout; verify the 13 tracked Studio assets and compare their recorded hashes.
6. If any gate fails, do not approve/continue the deployment. Use a known-good Git revision to restore the prior Studio bundle, then retest.

## What remains
Publication remains a **release-owner initiated** command, not a background event watcher. This deliberately avoids unreviewed updates and paid hosted Actions. The automation handles artifact collection, validation and atomic GitHub synchronization *after* a developer invokes the approved release. A later signed/tagged release process may further tighten provenance.

## Development-era CMS policy — owner direction, 2026-11-20

The Academy CMS is **not frozen**. We may improve Payload collections, admin UI, lesson/challenge metadata, content types, assessment workflows and related features as Kasa grows. Apply changes in the Academy repo, not as side effects of the language browser-asset release tool. Use explicit database schema migrations and backwards-compatible reads where practical. Back up or snapshot important data before destructive schema changes; never silently overwrite existing published lessons, user records, transcripts or recorded videos. Treat upgrades to the CMS as separately verified development changes, rather than claiming the asset publisher updates them.

**Pre-publication guard:** Phase 9C changes to `scripts/release_to_academy.py` are awaiting fresh local Mac tests and a new Emscripten/native build. Do not run `--publish` on stale binaries. The current Academy production assets remain deployed, independent of this release-tool update.
