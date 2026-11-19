# Phase 5B — macOS Installer preview and Kasa upgrade lifecycle

**Status (19 November 2026):** Intel macOS Ventura successfully built, inspected and installed unsigned preview `0.4.0.194`, and ran `kasa` from a home directory without the Python virtual environment. Reported full local verification: 19/19. Apple Silicon, clean-machine compatibility, upgrades and uninstall are not yet verified; do not publish as a trusted public release.

## What happens when Kasa changes?

An installed executable is an **immutable snapshot**. Editing the Kasa compiler or interpreter repository does **not** change older binaries, browser runtime deployments, or packages already in users' hands. For every release:

1. Commit the source changes, update behavior and compatibility tests.
2. Run `quick`, `parity` and `full` on all required release platforms.
3. Rebuild the native executable from the updated source (never repackage stale binaries).
4. Generate a higher-version package and its SHA-256 checksum.
5. Check a clean installation **and** an upgrade from the previous package on each supported OS.
6. Publish an explicit changelog, downloads, checksums, compatibility and migration notes. Users choose whether/when to install an update; **there is no auto-update today**.

Kasa 0.4 alpha has not made a language syntax or bytecode compatibility guarantee. Do not promise that every old `.kbc` file or program will execute forever. Prefer recompiling old source programs when compatibility is uncertain. Plan versioned KBC readers and a formal compatibility policy before stable releases.

## Create an installer on your real Mac (no installation at build time)

```bash
cd ~/Projects/kasa/kasa_programming_language
source .venv/bin/activate
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
bash scripts/mac_dev.sh full
bash scripts/mac_dev.sh installer
```

The `installer` action requires Apple's `pkgbuild`, a clean Git working tree, an executable freshly compiled after all native source timestamps, and a passing `--version` response. It **builds** the package but does not run `sudo`, open Installer, modify system paths, upload to any host, or install anything.

Expected output names in `build/dist/` are like `kasa-0.4.0.N-macos-x86_64-UNSIGNED.pkg` and its `.sha256`; `N` is Git's commit count. This provides increasing package versions for subsequent commits without claiming that the language itself has moved past **0.4.0-alpha**. After any change, rerun `full` to refresh compiled artifacts.

### What would installation change? (requires deliberate administrator approval)

This is a **system-wide** preview, unlike Phase 5A's entirely user-local tar archive.

- Package identifier: `org.kasalang.kasa.preview`
- Installer root: `/`
- Executable and launcher: `/usr/local/lib/kasa-preview/kasa-native` and `/usr/local/lib/kasa-preview/kasa`
- Command symlink: `/usr/local/bin/kasa` targeting `../lib/kasa-preview/kasa`
- Metadata: `/usr/local/lib/kasa-preview/build-info.txt`
- A bundled root-executed preinstall script refuses to replace a preexisting `/usr/local/bin/kasa` file or a symlink with another destination.

The preinstall script does not delete other installations. On an upgrade, an existing symlink to the expected target is allowed and macOS Installer should replace this package's own payload in place. This is not yet upgrade-tested on real macOS, so avoid sharing the package with others until installed/upgrade tests succeed.

To inspect the package **without installing it**:

```bash
cd build/dist
ls -lh *UNSIGNED.pkg
shasum -a 256 -c <exact-pkg-filename>.sha256
pkgutil --check-signature <exact-pkg-filename>
pkgutil --expand <exact-pkg-filename> expanded-pkg-preview
```

An unsigned package will not have a trusted Developer ID Installer signature. Do not bypass Gatekeeper or weaken macOS security to accept an unknown downloaded installer.

Install **only if you deliberately want a system-wide local preview**, by opening the locally built `.pkg` with Apple's Installer and approving the changes. This step is optional; the extracted tarball remains the safer initial choice. Avoid installing if `/usr/local/bin/kasa` already belongs to another tool or setup.

After an explicitly approved installation, check `/usr/local/bin/kasa --version` and run a sample program from an unrelated directory. Validate installation receipts with `pkgutil --pkg-info org.kasalang.kasa.preview`.

### Uninstallation

macOS package receipts do not automatically include a one-click uninstaller. For now, **do not use a broad destructive command or delete `/usr/local`**. A future uninstall script must verify the package receipt and ownership of every target path before deleting only Kasa-owned files. A local tarball can always be used without installing system-wide.

## Still needed before a public installer

- Real `pkgbuild` build and package contents inspection on Intel macOS.
- Installation/upgrade/uninstallation regression tests, including ownership collisions.
- Apple Silicon build and actual on-device conformance.
- Security review for root-executed scripts, signing, notarization and Gatekeeper behavior.
- Tested Windows/Linux packages and maintained release notes.

## Phase 5C — safe upgrade inspection and uninstall planning (new)

The first Intel preview was installed successfully under package identifier `org.kasalang.kasa.preview`, with receipt `0.4.0.194` and a functioning standalone native command. Phase 5C adds two **read-only** tools:

```bash
cd ~/Projects/kasa/kasa_programming_language
source .venv/bin/activate
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
bash scripts/mac_dev.sh upgrade-audit
bash scripts/mac_dev.sh uninstall-plan
```

The upgrade audit refuses to certify the installation when the receipt and `build-info.txt` disagree, a Kasa-owned executable is missing, or `/usr/local/bin/kasa` points to an unrelated application. A candidate version can be checked with `bash scripts/mac_dev.sh upgrade-audit --candidate-version 0.4.0.195`; this is only a version sanity check, **not** a real binary compatibility or signed-package verification. The candidate number is illustrative, not a release.

The uninstall planner lists only four package-owned paths and the package receipt. It refuses unexpected files in Kasa's installation directory and unexpected links. **It cannot remove anything**: `--execute` is disabled even for direct Python callers. It does not delete your source programs, `~/hello.kasa`, Academy materials, or any home-directory files.

Upgrades and uninstall still require on-device safe testing and further engineering before any automated system changes will be enabled. Do not execute speculative `sudo rm` commands to emulate this workflow.
