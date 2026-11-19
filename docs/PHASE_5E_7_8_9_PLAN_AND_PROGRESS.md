# Roadmap update — Phases 5E, 7, 8, 9 (2026-11-19)

**Decision:** Defer Phase 6 Windows installer and native Windows-specific testing until the developer returns to the office Windows machine. Continue Mac-first, locally tested implementation without paying for hosted CI or triggering Vercel/Netlify builds for every source commit.

## Phase 5E — safe uninstall and recovery

- `scripts/audit_macos_install.py` verifies the existing Kasa installer receipt, build metadata, known files and expected command symlink.
- `scripts/plan_macos_uninstall.py` lists the exact package-owned paths; intentionally refuses live deletion. Personal `.kasa` projects are never eligible for removal.
- **New:** `scripts/snapshot_macos_install.py` creates a Kasa-only `.tar.gz` recovery archive under `build/recovery/`, with SHA-256 digests for package-owned files and recorded symlink target. It does **not** modify `/usr/local`, change receipts or attempt a privileged restore. The snapshot is not a one-click rollback.
- **Still open:** deliberately safe rollback/transactional uninstall on a disposable macOS test VM or secondary machine, partial failure recovery, package receipt and ownership guarantees, and appropriate privileges. Keep actual removal disabled until those checks pass.

Mac commands:

```bash
source .venv/bin/activate
bash scripts/mac_dev.sh upgrade-audit
bash scripts/mac_dev.sh uninstall-plan
bash scripts/mac_dev.sh recovery-snapshot
shasum -a 256 build/recovery/kasa-installed-preview.tar.gz
tar -tzf build/recovery/kasa-installed-preview.tar.gz
```

The recovery snapshot command refuses to overwrite an existing archive; move or rename your previous snapshot before taking a new one. Never extract the backup into `/usr/local` as a substitute for Installer.

## Phase 7 — developer experience

- Existing VS Code `.kasa` syntax highlighting, snippets, `Run Current File` and `Check Current File` commands are preserved.
- The extension now defaults to `kasa` (the actual installed macOS command), not `kasa-native`.
- A missing executable (`ENOENT`) reports how to set `kasa.executablePath`; commands continue to use `spawn(..., shell:false)` without shell injection.
- Run extension metadata regression tests: `node --test editors/vscode-kasa/tests/*.test.cjs`.
- **Still open:** Extension Development Host tests, editor diagnostics, launch configuration, extension packaging/signing and real user usability studies.

## Phase 8 — Academy and Studio

- The Academy's syntax index and individual syntax lessons link explicitly to `/playground`, while retaining their guided embedded editors.
- The `/playground` page continues to embed the first-party `/kasa-studio/index.html` WASM/JavaScript runtime.
- The CMS-managed Netlify URL, when available and valid, is exposed as a **separate optional external link**, never a replacement for the first-party Studio. URLs are normalized to secure HTTPS origins; the link uses `noopener noreferrer`.
- A SHA-256 release manifest in the Academy tracks its embedded Studio assets; production release requires a reviewed, gated sync of those assets, and live browser verification.
- Test in the Academy checkout with `node --test tests/syntax-studio-journey.test.mjs tests/academy-studio.test.mjs tests/playground-settings.test.mjs`.
- **Still open:** live production confirmation after deployment; content parity across Academy and standalone playground, learner usability/accessibility, and any unresolved CMS/DB deployment quirks.

## Phase 9 — public alpha readiness

- **New:** `scripts/audit_public_alpha.py` generates a read-only, fail-closed release audit report. By design, local files cannot falsely certify cross-platform installs, signing, a completed security review or classroom approval.
- **New:** draft `docs/LANGUAGE_COMPATIBILITY_POLICY.md` distinguishes language version, installer build, KBC version and browser bundle version.
- **New:** draft `docs/RELEASE_NOTES_0_4.md` summarizes evidence without claiming public release.
- **Required owner decision:** Select and commit an actual open-source `LICENSE`. No license is presumed or silently added by the assistant.
- The official public alpha remains **blocked**, including signing/notarization, Apple Silicon and Windows/Linux installs, real production browser build, untrusted-code security analysis, and fluent-speaker/educator reviews.

Run:

```bash
.venv/bin/python scripts/audit_public_alpha.py
cat build/public-alpha-gate.json
```

A nonzero exit is **expected** until all required gates are independently satisfied. It must not be changed just to produce a green result.

## Verification and deployment honesty

At this implementation milestone, targeted Python safeguards and VS Code metadata tests ran independently, and the initial Academy first-party Studio tests passed. Further Academy CMS-link tests and full TypeScript/Next.js builds still require the relevant Node/DB setup and user review. No public download, signed release, Vercel/Netlify deployment, real uninstall, Windows build or Apple Silicon test is claimed.

Do not equate a successful unsigned installer on the developer's Intel Mac with a secure, generally supported public release.
