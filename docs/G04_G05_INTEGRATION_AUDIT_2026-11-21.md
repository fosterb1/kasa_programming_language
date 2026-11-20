# G0.4 → G0.5 Experimental Integration and Consolidation Audit

**Audit date:** 2026-11-21  
**Scope:** read-only GitHub PR/branch comparison plus review of current files and prior owner-provided verification.  
**Decision:** **PREPARE ONLY — DO NOT MERGE, RETARGET OR MARK READY YET.**

## 1. Frozen GitHub audit snapshot

| Item | Observed status | Reference |
| --- | --- | --- |
| Stable branch | `main` | PR #60 base `84ab2e03a94b207a2d16aba52db36f880653c52f` at audit |
| PR #60 / G0.4 | **Open, draft, mergeable**, no submitted reviews | Head `7ddc7d5f733432d64d5a6dd9a043221c02f60e6c`; base `main` |
| PR #61 / G0.5 | **Open, draft, mergeable**, no submitted reviews | Head `da0087d7856b5208c49ea09a653bf8f898ad9664`; base `dev/g04-module-cross-runtime-fixtures` |
| `main → G0.4` | **19 ahead / 0 behind**, 9 changed files | Diff contains JavaScript runtime, experimental Python runner, 13-case fixture and real-browser test |
| `G0.4 → G0.5` | **62 ahead / 0 behind**, 23 changed files | Diff adds preflight/linker/CLI, KBC1 verification, mapping, failure corpus and security tests |
| `main → G0.5` | **81 ahead / 0 behind** | Stacked history: 19 + 62, **not** 81 separately approved release changes |
| Merge conflict signal | GitHub currently says both PRs `mergeable=true` | This is not an approval or a substitute for tests/review |

**Dependency invariant:** G0.5 must be evaluated against the exact G0.4 behavior. The G0.5 PR is correctly based on the G0.4 branch. **Do not squash or retarget G0.5 ahead of G0.4 review.** If G0.4 is squashed on `main`, Git commit ancestry changes; verify the new PR #61 diff carefully and reconstruct a clean branch if needed. Avoid duplicate file additions or silently changing its base.

## 2. PR #60 audit — G0.4 cross-runtime imports

**Actual nine changed paths:**
- `docs/G03_SOURCE_IMPORT_ACCEPTANCE.md`
- `docs/G04_SHARED_MODULE_CONFORMANCE.md`
- `playground/kasa-runtime.js`
- `scripts/run_kasa_modules_experimental.py`
- `scripts/verify_real_module_browser.py`
- `tests/conformance_experimental_modules.json`
- `tests/test_g03_source_import_acceptance.py`
- `tests/test_js_module_cross_runtime_fixtures.cjs`
- `tests/test_module_cross_runtime_fixtures.py`

**Strengths found in source:** the module entry point is opt-in and the Python prototype requires declarations before statements; duplicate module IDs or aliases are rejected at the second declaration. The 13-case fixture corpus drives shared Python/JavaScript checks. The Playwright gate packages a temporary playground, explicitly disables native WASM in the temporary worker, and runs JavaScript module behavior in a real Chromium worker. Standard-mode import rejection is also asserted.

**Boundary:** G0.4 is **not** native-WASM import support, hosted Netlify/Academy verification, a general dependency loader, approved stable Twi grammar, or secure third-party modules. The browser gate deliberately disables native WASM to isolate JavaScript behavior.

**Existing evidence:** owner confirmed G0.4.3 real-browser and 11-stage parity runs, but the final exact tested commit/log was not pasted. PR #60 still has **no submitted review** and a draft badge.

**Before considering PR #60 an experimental merge candidate:**
1. Checkout the exact G0.4 head on Windows and record `git rev-parse HEAD`, clean tracked state, and `git status --short`.
2. Run shared Python, Node and real Chromium module gates, and the full native profile against that exact revision. Provide actual outputs/skip reasons.
3. Independently inspect the 15-line/12-line delta in `playground/kasa-runtime.js` to ensure non-opt-in browser programs retain existing behavior; run default browser fixtures.
4. Confirm default mode still rejects `fa` imports and JavaScript conformance cannot accidentally claim native WASM module support.
5. Review source security/data boundaries (allowlisted catalog, no arbitrary URL/file import, budgets) and note known unsupported cases.
6. Keep it tagged **experimental opt-in**. A merge into `main` would integrate an experiment, **not** promote its syntax to stable Kasa.

### G0.4 Windows gate (CMD; no Unix backslash continuations)

```cmd
git fetch origin
git switch dev/g04-module-cross-runtime-fixtures
git pull --ff-only
git status --short
git rev-parse HEAD
python -m pytest -q tests/test_module_cross_runtime_fixtures.py tests/test_g03_source_import_acceptance.py tests/test_experimental_module_source.py
node tests/test_js_module_cross_runtime_fixtures.cjs
node tests/test_js_experimental_modules.js
python scripts/verify_real_module_browser.py
python scripts/verify_local.py --profile full --report build/g04-integration-full.json
```

Run the real browser check with the locally installed Playwright/Chrome/Chromium; don't mark it passed on installation failure. Do **not** merge during the check. If a working tree has local changes, investigate before switching branches.

## 3. PR #61 audit — G0.5 native module-to-KBC1

**Actual 23 changed paths**, grouped by responsibility:
- Design/status: `docs/G05_EXIT_REVIEW.md`, `docs/G05_NATIVE_MODULE_CONTRACT.md`
- Static module preflight/link/compile: `scripts/preflight_native_modules.py`, `scripts/link_kasa_modules_hygienic.py`, `scripts/compile_g05_modules.py`
- Diagnostics/source provenance: `scripts/annotate_g05_diagnostic.py`, `scripts/run_g05_native_mapped.py`
- Native/KBC1 acceptance: `scripts/verify_g05_native_kbc.py`, `scripts/verify_g05_kbc_independence.py`, `scripts/verify_g05_release.py`
- Thirteen test modules: `tests/test_g05_*.py` plus `tests/test_hygienic_module_linker.py` and `tests/test_native_module_preflight.py`

**Strengths found in source:** opt-in prelink from SHA-pinned `math` and `collections`, static namespace isolation and export checks, self-contained KBC1, native `check/compile/check-bytecode`, exclusive publication (default), same-toolchain reproducibility comparisons, statement-level origin maps, corruption tests, malformed-source corpus, real Windows junction tests and controlled directory replacement checks. Strict publication explicitly refuses on Windows and offers POSIX-only directory-relative `os.open(..., dir_fd=...)`.

**Important security and correctness boundaries:**
- Strict POSIX publishing has **not been demonstrated executing successfully on POSIX** in the most recent Windows acceptance logs. Three POSIX-only cases skipped.
- One real Windows file-symlink test skipped because the Windows account could not create symlinks. A junction pass or mocked guard pass does not replace a real file-symlink check.
- Default Windows output creation is still pathname-based after an identity check. A directory can be replaced after that check; no hostile multiuser containment is established.
- POSIX strict publication is an experimental path-hardening measure, **not** an audited process sandbox; source/catalog identity races and post-publication filesystem mutation remain.
- `compile_g05_modules.py` currently fixes source input to 50,000 bytes and accepts only allowlisted library names; no arbitrary third-party package manager.
- Generated error mapping is statement-level; KBC1 wire format remains unchanged; default native compiler does **not** parse `fa` imports directly.
- Current collector's `REVIEW_REQUIRED` is correct when **any** test skips, even when all four stages report `PASSED`.

**Detailed owner-provided Windows evidence** for `46ff7f1e07cbb729c973ccb06725ec935d5582a6`: four collector stages passed, pytest **76 passed, 4 skipped, 0 failed**; skip list included **one** real-file-symlink creation restriction and **three** POSIX-only strict-publication tests. Subsequent focused tests were owner-reported green without full terminal count/checkout SHA. This is *development confirmation*, not cross-platform release signoff.

### G0.5 Windows integration gate (CMD)

After reviewing G0.4, switch back to the development branch **without merging**:

```cmd
git switch dev/g05-native-module-contract
git pull --ff-only
git status --short
git rev-parse HEAD
python scripts/verify_g05_release.py
python scripts/verify_real_module_browser.py
```

The release collector covers full native checks, G0.5 pytest, native/KBC1 parity and bytecode independence. The browser check is the G0.4 dependency gate and must not be lost while testing G0.5. Preserve **failed**, **skipped**, **review_required** and **not_run** distinctions. A Windows strict gate that skips POSIX cases is not a zero-skip acceptance.

### Additional actual POSIX verification before proposing broader use

Run `python -m pytest -q -rs tests/test_g05_strict_publication.py tests/test_g05_publication_race.py` in a POSIX checkout; provide exact Git SHA and output. For a full native release evidence claim, compile and run the native full profile on that POSIX checkout too. WSL is acceptable only when actual `dir_fd` support and filesystem semantics are available; do not infer Windows-native secure output creation from a WSL pass.

## 4. Integration order and review gates

```text
main (no new G0.4/G0.5 merges)
  │
  └── PR #60: dev/g04-module-cross-runtime-fixtures [DRAFT]
         └── PR #61: dev/g05-native-module-contract [DRAFT]
```

**Stage I — Documentation-only audit [DONE]:** record exact refs, changed files and risks; keep source behavior untouched. This document is a development artifact, not executable acceptance evidence.

**Stage II — G0.4 candidate [NOT DONE]:** complete exact-HEAD Windows gate; review browser source delta; collect complete logs. Optionally request a reviewer. Only after owner explicitly authorizes an experimental integration and all policy gates are satisfied should PR #60 be marked ready, retargeted or merged.

**Stage III — G0.5 candidate [NOT DONE]:** complete exact-HEAD G0.5 collector + G0.4 browser regression, preserve Windows skip record, run POSIX strict tests separately and independently review security assumptions. Decide whether a limited **trusted-local experimental** merge is acceptable with an explicit exception for known, platform-specific skips. **Never change the release collector to hide them.**

**Stage IV — Stack reconciliation [NOT DONE]:** once a separately authorized G0.4 merge lands, fetch `main` and inspect the new `main...G0.5` diff. If the G0.4 branch was squash-merged, avoid duplicating its changes: build a fresh integration branch if needed, carry only the reviewed G0.5 file delta, run complete regression and have its exact commit reviewed. Do not force-push or rewrite a branch with uncommitted work.

**Stage V — Limited experimental merge [NOT AUTHORIZED]:** only after review, owner decision, scoped release notes, no unintended grammar or binary-format changes, and explicit acknowledgment of non-hosted use. Merge **must not** be interpreted as an approval to deploy the compiler or accept user-uploaded programs.

**Stage VI — Broader release [BLOCKED]:** secure untrusted execution, verified Windows-native handle-based file output or a properly isolated alternative, platform-specific installation and source validation, license decision, Twi/educator review, production browser/Academy release checks, and stable compatibility policies.

## 5. Changes intentionally NOT made during this sprint

- No merge, rebase, cherry-pick, forced branch update, branch retargeting or switch to `main`.
- No suppression or waiver of skip reporting; no manufactured all-green status.
- No change to the native parser, KBC1/KBC2 format or default Kasa import grammar.
- No Netlify/Vercel/Academy deployment, publishing or mutation of CMS records.
- No official public alpha, production runtime authorization, new license or claim of security certification.

## 6. Immediate recommendation

**First finish exact-HEAD G0.4 acceptance on Windows**, before revisiting G0.5 merging. In parallel, a POSIX-only smoke on the strict output implementation can collect independent safety evidence. Keep the companion Academy release work gated separately.

Once source and tests are accepted, update PR #60's checklist first and PR #61's checklist second. **Nothing gets merged just because GitHub currently reports `mergeable=true`.**

## 7. G0.4 Windows acceptance reported and browser delta reviewed (2026-11-21)

**User report:** the owner confirmed **"all pass"** after the exact-head G0.4 Windows acceptance commands were supplied (shared pytest fixtures, both Node module runners, `verify_real_module_browser.py`, and the `--profile full` native runner). The owner did not paste the final command outputs, clean-tree status or `git rev-parse HEAD`; hence record this as *owner-confirmed*, not independently observed test execution at a particular SHA. The intended unchanged G0.4 head at review time is `7ddc7d5f733432d64d5a6dd9a043221c02f60e6c`.

**Independent source-diff review:** GitHub's exact `playground/kasa-runtime.js` patch for PR #60 adds the `moduleFailure(category, message, token)` helper and changes **only the error category at experimental module validation sites** from `SyntaxError` to `ModuleError` (catalog and namespace validation) or `NameError` (unknown alias/export and alias mutation). It does not alter tokenization, numeric operators, default interpreter execution, runtime quotas, bytecode or module evaluation logic in that file. Existing browser tests remain necessary, but this diff supports *narrow diagnostic classification scope* rather than a broad interpreter rewrite.

**G0.4 decision:** *eligible for review as an opt-in experimental integration candidate*, **not yet merge-authorized**. PR #60 remains draft, no reviews submitted at last inspection. Explicit owner merge authorization and the policy decision about any remaining platform skips are still separate. Do not mark it ready or merge during the consolidation audit.

**Next no-merge action:** return to the G0.5 branch, run its entire release collector and the inherited G0.4 real-browser worker test, and record the final HEAD/skip details:

```cmd
git status --short
git switch dev/g05-native-module-contract
git pull --ff-only
git rev-parse HEAD
python scripts/verify_g05_release.py
python scripts/verify_real_module_browser.py
```

If the Windows environment still lacks real symlink privileges and POSIX-specific functionality, `REVIEW_REQUIRED` remains **expected and mandatory** despite passing executable checks. Do not bypass the release collector or claim Linux directory-handle publication passed on Windows.

## 8. Combined G0.5 and inherited G0.4 Windows verification — owner confirmation (2026-11-21)

The owner replied **"all pass"** after receiving the G0.5 integration command set:
`git switch dev/g05-native-module-contract`, `git pull --ff-only`, `git rev-parse HEAD`, `python scripts/verify_g05_release.py`, and `python scripts/verify_real_module_browser.py`.

**Evidence classification:** owner-confirmed successful execution of the applicable Windows tests and inherited G0.4 browser module gate. The actual terminal output, final HEAD and updated `skip_details` were not pasted. We therefore **do not** assert every OS-dependent test ran or that the release collector's overall status was `PASSED`. Its known Windows outcome is generally `REVIEW_REQUIRED` because the real file-symlink test may skip and POSIX strict-publishing checks necessarily skip.

**Integration assessment:** both PRs have owner-confirmed Windows acceptance for their tested alpha functionality, a reviewed G0.4 runtime delta, and a documented stack ordering. **Neither PR is yet authorized to merge**. Before an experimental G0.4 merge, gather independently reviewed test evidence at exact HEAD and an explicit merge decision; before G0.5 integration, separately execute POSIX strict-publication tests and review the remaining TOCTOU/security limitation, or approve a narrowly scoped experimental exception with a documented non-hosted restriction. Windows `REVIEW_REQUIRED` must remain visible and must never be turned green by hiding skips.

**Immediate next activity:** prepare a non-destructive PR #60 experimental merge-readiness checklist (no merge, no retarget) and request code review if appropriate. After the G0.4 decision is explicitly authorized and completed, reconcile the G0.5 branch against the actual resulting `main` history, especially if G0.4 is squash-merged.

## 9. PR #60 merge-readiness packet prepared (2026-11-21)

[The standalone PR #60 experimental merge-readiness review](G04_PR60_EXPERIMENTAL_MERGE_READINESS.md) provides a nine-file code/diff scope audit, an evidence register, a concrete Windows exact-head command sequence and explicit non-merge controls. This packet is intentionally authored **on the existing G0.5 branch**, not on G0.4, so it does not shift the base of dependent PR #61. Both PR descriptions now link to the packet.

**Current state:** PR #60 and PR #61 remain draft/open, no merge or retarget occurred. Owner reports all applicable Windows tests passed, but exact-head terminal output and independent review are still outstanding. No authorization has been requested or inferred by this documentation change.

## 10. Read-only stacked branch auditor added (2026-11-21)

After the PR #60 code-review packet, the integration branch now includes `scripts/audit_g04_g05_stack.py` and `tests/test_g04_g05_stack_audit.py`. These changes are confined to the G0.5 dependent branch; PR #60 remains at its pinned reviewed head.

The auditor runs **read-only local Git commands** against `origin/main`, `origin/dev/g04-module-cross-runtime-fixtures` and `origin/dev/g05-native-module-contract`. It records commit SHA, ancestry, exact nine-file G0.4 changed-path set, necessary G0.5 paths, whether G0.5 has touched `native/`, `src/` or `playground/` unexpectedly, current HEAD and tracked worktree state. Its JSON result is only `scope_ok_not_merge_approval` or `review_required`; **even success never authorizes merging**. Missing refs, stale head, dirty tracked files or unexpected changes are reported rather than silently accepted. It performs no fetch, checkout, write, merge or GitHub API change.

Use Windows CMD from the G0.5 checkout:

```cmd
git status --short
git fetch origin
git pull --ff-only
python -m py_compile scripts/audit_g04_g05_stack.py tests/test_g04_g05_stack_audit.py
python -m pytest -q -rs tests/test_g04_g05_stack_audit.py
python scripts/audit_g04_g05_stack.py --pretty
git rev-parse HEAD
```

The audit itself was written based on the GitHub connector's current PR comparisons, **not independently executed** against the owner's Windows Git checkout. Do not confuse branch scope success with previous G0.4/G0.5 functional test passes. The script does not solve POSIX strict-publication verification or authorize public compilation.

An attempt to reach GitHub directly from the available Linux runtime was blocked by DNS/network policy; **no actual POSIX G0.5 tests were run or claimed** during this step. POSIX security coverage remains open and the two PRs stay draft.

## 11. Windows branch topology audit — exact owner-supplied evidence (2026-11-21)

**Evidence received:** full Windows CMD terminal output, including revision and JSON report, from the user's checked-out Kasa repository. This is **owner-provided direct terminal evidence**, not a claim that the GitHub connector or assistant executed the Windows commands.

- `git pull --ff-only` advanced `14ff847` to **`56083070326c663acc45c328a87ced69208a62de`**.
- `python -m py_compile scripts/audit_g04_g05_stack.py tests/test_g04_g05_stack_audit.py` exited without reported errors.
- `python -m pytest -q -rs tests/test_g04_g05_stack_audit.py` reported **5 passed in 0.07s**, no failures/skips shown.
- `python scripts/audit_g04_g05_stack.py --pretty` returned `"status": "scope_ok_not_merge_approval"` with **all eight checks true**.
- `git rev-parse HEAD` matched `56083070326c663acc45c328a87ced69208a62de`.
- The report listed `main=84ab2e03a94b207a2d16aba52db36f880653c52f`, `g04=7ddc7d5f733432d64d5a6dd9a043221c02f60e6c`, and `g05=56083070326c663acc45c328a87ced69208a62de`.
- Confirmed true: `main_ancestor_of_g04`, `g04_ancestor_of_g05`, `g04_exact_file_scope`, `g05_minimum_expected_files`, `g05_files_restricted_to_docs_scripts_tests`, `no_native_or_core_parser_changed_in_g05`, `local_head_matches_g05_remote`, `tracked_worktree_clean`.
- The G0.4 changed-file list contained exactly the nine expected paths; the G0.5 list included the new audit docs/tool/tests and no unexpected changes to `native/`, `src/`, or `playground/`.

**Disposition:** local Git ancestry and code-change scope are **confirmed at the cited revision**. This does not independently rerun Python/Node/browser/native functional suites at that same SHA, prove the 3 POSIX strict publication tests (which skip on Windows), clear the Windows symlink test coverage gap, certify hostile-code isolation, or approve a merge.

**Next integration gate:** independent code review / explicit decision on the narrow experimental G0.4 merge, plus G0.5 POSIX and security evidence before broader adoption. Maintain both PRs in draft pending authorization; no bypass of `REVIEW_REQUIRED`.
