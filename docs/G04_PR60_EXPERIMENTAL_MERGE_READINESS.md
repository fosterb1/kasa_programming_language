# PR #60 — G0.4 Experimental Merge-Readiness Review

**Review date:** 2026-11-21  
**PR:** https://github.com/fosterb1/kasa_programming_language/pull/60  
**Decision:** **CANDIDATE FOR REVIEW; NOT AUTHORIZED TO MERGE**  
**Frozen audited head:** `7ddc7d5f733432d64d5a6dd9a043221c02f60e6c`  
**Base:** `main`; **stacked dependent:** PR #61, G0.5.

This review is deliberately stored on the **G0.5 documentation branch**, not on G0.4: committing a new file to G0.4 would move PR #60's head and invalidate G0.5's pinned parent relationship unless consciously rebased. No default-branch changes, retargets, merges or production deployments occurred.

## Exact PR change audit

GitHub comparison: **19 commits ahead / 0 behind main**, **9 files**; current GitHub metadata says **open, draft, mergeable**, with **no submitted reviews**. Diff scope:

| Area | Paths | Finding |
| --- | --- | --- |
| Browser runtime | `playground/kasa-runtime.js` | Exact patch: a `moduleFailure(category, message, token)` helper and module-only diagnostic classification changes (`ModuleError` vs `NameError`); no changed general parser operators, quotas or KBC schema |
| Python experimental source runner | `scripts/run_kasa_modules_experimental.py` | Tracks selected module IDs/aliases as declarations are scanned; flags duplicate at second declaration before initialization |
| Python/JS fixtures | `tests/conformance_experimental_modules.json`, `tests/test_module_cross_runtime_fixtures.py`, `tests/test_js_module_cross_runtime_fixtures.cjs` | 13 shared success/error fixtures, including source positions and no preflight output on rejection |
| Acceptance tests | `tests/test_g03_source_import_acceptance.py` | Stable/default parse still rejects experimental syntax; exported names remain namespaced; step-budget rejection tested |
| Real browser gate | `scripts/verify_real_module_browser.py` | Builds temporary packaged playground, *disables WASM* to target JavaScript worker, checks fixture outputs/errors and normal-mode rejection |
| Documentation | `docs/G03_SOURCE_IMPORT_ACCEPTANCE.md`, `docs/G04_SHARED_MODULE_CONFORMANCE.md` | Explicit opt-in/alpha scope and previous owner verification notes |

### Security and review observations

1. **No native or production source syntax claim.** `fa math firi stdlib: m` remains experimental; normal Kasa parser must still reject it without opt-in. A limited G0.4 merge must not activate it silently.
2. **JavaScript execution remains bounded.** The PR runtime patch does not change runtime budgets or code-evaluation semantics; it reclassifies module validation errors. Verify the existing negative/resource fixtures in a real browser.
3. **Locally packaged imports only.** The JS test harness reads `stdlib/catalog.json`, checks source SHA-256, and supplies module definitions via explicit trusted metadata. Not a general untrusted package resolver.
4. **Actual browser gate is *JS-only*.** It specifically forces native WASM off in the temporary worker. A pass proves neither browser WASM import execution nor production Netlify/Academy deployment.
5. **Local ZIP extraction:** `verify_real_module_browser.py` calls `ZipFile.extractall(site)` for an archive produced immediately by first-party `build_bundle` in a fresh temporary directory. Its test-runner input is trusted local output, **not a general untrusted-archive extraction API**; do not reuse it for untrusted uploads without independent review.
6. **Real-language governance:** `fa ... firi` grammar is an opt-in prototype. Twi-speaking community review, compatibility and spelling decisions remain pending.

## Evidence register (do not confuse reports with fresh execution)

| Gate | Observed evidence | Disposition |
| --- | --- | --- |
| Python shared G0.4 fixtures | Owner reported pass on Windows after explicit commands | **Owner-confirmed**; raw count/SHA not attached |
| Node shared fixtures and regression | Owner reported pass | **Owner-confirmed** |
| Real Chromium worker G0.4.3 | Owner reported pass with browser script | **Owner-confirmed**; selected JavaScript module path only |
| Native full profile at G0.4 | Owner reported pass | **Owner-confirmed**; report file contents not reviewed |
| G0.5 inherited browser gate | Owner later reported pass on stacked branch | **Owner-confirmed**; useful regression evidence, not exact G0.4 HEAD |
| Independent PR review | None submitted in GitHub PR review records | **Outstanding** |
| Merge authorization | Not granted for either PR | **Outstanding** |

## Final G0.4 review checklist

- [x] Confirm GitHub base/head stacking and nine-file diff.
- [x] Review every changed path's diff for scope; do not extrapolate G0.4 into native/WASM imports.
- [x] Review browser diagnostic error-category delta and Python duplicate-import detection.
- [x] Preserve tests for default parser rejecting import syntax, source quotas and module export restrictions.
- [x] Record owner-confirmed Windows tests as reported.
- [ ] Capture **the exact checked-out commit and complete output** of the Python/Node/browser/native full checks on that commit, including native count and any skips.
- [ ] Independent code reviewer signs off on opt-in semantics, browser test isolation and safe catalog assumptions.
- [ ] Confirm the desired experimental integration strategy (no automatic runtime feature enablement; no production web deployment; no third-party imports).
- [ ] **Obtain explicit owner authorization** for PR #60 merge (separate action, not implied by testing or this report).
- [ ] After any approved merge, independently verify `main` and reconcile PR #61 depending on merge type before testing/merging it.

## Safe final evidence commands (Windows CMD)

Do not switch branches with uncommitted changes:

```cmd
git status --short
git switch dev/g04-module-cross-runtime-fixtures
git pull --ff-only
git rev-parse HEAD
python -m pytest -q -rs tests/test_module_cross_runtime_fixtures.py tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py
node tests/test_js_module_cross_runtime_fixtures.cjs
node tests/test_js_experimental_modules.js
python scripts/verify_real_module_browser.py
python scripts/verify_local.py --profile full --report build/g04-integration-full.json
```

**Avoid accidental merge.** Do not run `git merge`, `gh pr merge`, mark PR ready, or update PR bases as part of these checks. Afterward return to `dev/g05-native-module-contract` to continue development.

## Merge-path note

If PR #60 is eventually explicitly authorized and squash-merged into `main`, PR #61's commit ancestry will still include original G0.4 commits. In that case compare `main...dev/g05-native-module-contract` and consider rebuilding a clean G0.5-only branch from the new main using the precise 23-file G0.5 delta; do not assume the old PR #61 diff is safe to retarget without inspection.

**Verdict:** code is reasonably narrow for an *experimental* opt-in merge review, with meaningful owner-reported tests. This is not an automatic merge recommendation, production approval, or signed release.
