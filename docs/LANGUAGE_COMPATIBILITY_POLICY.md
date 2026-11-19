# Kasa language compatibility policy — pre-1.0 draft

**Status:** Draft engineering policy, not an owner-approved 1.0 stability commitment. Kasa 0.4.0-alpha is experimental.

## Version components

- **Language version:** `0.4.0-alpha` is what `kasa --version` currently reports. Changing the installer build number does not change language semantics.
- **Installer build version:** `0.4.0.N` increases on subsequent source commits for macOS Installer upgrades. It is not a semantic-versioned language release.
- **Bytecode version:** KBC1 is independently versioned on-disk format and remains experimental. KBC2 is an opt-in experiment; do not assume arbitrary KBC1/KBC2 compatibility.
- **Studio browser bundle:** content-addressed `release-manifest.json` release ID; independently deployed to the Academy only after its gated publication and verification.

## Change classes

1. **Patch/bug fixes:** Preserve already-tested valid source behavior where possible. A bug fix that changes output should document the prior and new behavior.
2. **New features:** Require Python, JavaScript, native and browser semantics tests for all runtimes where supported; indicate any implementation gaps explicitly.
3. **Breaking changes:** Need a migration guide, old-program corpus verification, developer/educator review and a deliberately changed language release identifier. Do not silently redefine Twi keywords.
4. **Bytecode changes:** Document encoding, reject unknown versions, and offer source re-compilation if compatibility cannot be guaranteed.

## Classroom and user code

- Existing `.kasa` source files stay in user projects, never in system-owned installed directories.
- Package installation or uninstallation must not search for or delete user projects.
- Before changing syntax, verify current lessons, workbook examples and practical examples under each relevant runtime.
- Do not promise old `.kbc` files will run across future versions; recommend keeping the original `.kasa` sources.

## Before a public release

Formalize semver policy, tested compatibility matrix, release notes, language specification conformance, native-speaker approval process, migration tooling, and package signing. Review the license separately; no open-source license is conferred by this draft.
