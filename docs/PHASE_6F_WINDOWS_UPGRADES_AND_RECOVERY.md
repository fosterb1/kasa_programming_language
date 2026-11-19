# Phase 6F — Windows upgrade eligibility and recovery policy

**Status: engineering design and read-only verification implemented, not upgrade-ready.**
Date: 2026-11-19.

The existing Windows preview installer `kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup-guarded-v2.exe` is **first-install-only**. It rejects every pre-existing destination. **Do not modify its installation checks, manually overwrite a Kasa folder, delete a Windows uninstall record, or execute an upgrade on the office machine.** Real VM installation/uninstallation tests are still pending.

## Read-only upgrade inspection

Run on Windows from your existing Kasa repository and virtual environment:

```bat
git pull --ff-only
python -m pytest -q tests/test_plan_windows_upgrade.py tests/test_stage_windows_installer.py tests/test_verify_windows_installer_lifecycle.py
python scripts/plan_windows_upgrade.py
type build/windows-upgrade-plan.json
```

The script reads `build/windows-installer-stage` by default and writes only `build/windows-upgrade-plan.json`. It does not install Kasa, copy package contents, modify PATH, alter registry keys, delete files or change an installation.

An optional **read-only** examination of an existing installation (in a controlled VM only, where the path is known) uses:

```bat
python scripts/plan_windows_upgrade.py --installed-dir "C:\path\to\your\Kasa Preview"
```

Do not guess the installed directory or copy a path from a different machine. This audit does **not** prove ownership or authorize removal.

## Current expected outcome: BLOCKED

The unsigned developer ZIP's manifest currently records language release `0.4.0-alpha` and a SHA-256 for the native executable, but does **not** include a reviewed `installer_build_version` such as `0.4.0.203`. The `kasa-install-identity.txt` file is not a cryptographic ownership proof. Windows uninstaller files may exist, but the audit cannot establish their ownership merely by filename.

The planner checks basic directory hygiene, a fixed list of files, expected Windows/x64/release metadata, the executable digest and the exact identity marker; candidate builds without a valid four-component numeric build version are rejected. Even a newer numeric candidate with consistent metadata is **never** authorized: `safe_to_upgrade` is hard-coded `false` until independent VM installation, rollback and receipt validation exist.

## Proposed implementation stages — not implemented

1. **Versioned installation receipts:** Record installer identity, unique build `0.4.0.N`, source commit, installed file hashes, Windows uninstall key, architecture and language release. Validate their provenance rather than trusting user-writable text alone.
2. **Separate app-owned directory and user files:** Keep `.kasa` sources and KBC data in user project folders. Never walk, delete or migrate unrelated directories during uninstall.
3. **Recovery snapshot before an upgrade:** Capture old native executable, launcher, verified manifest, installation metadata and the current uninstall state; store outside the application directory and verify checksums.
4. **Controlled upgrade path:** Only in a disposable Windows VM, compare version/build, confirm matching package identity, verify old ownership, stage new files, swap atomically where practical, validate execution and recover on partial failure.
5. **Uninstall and rollback tests:** Exercise interrupted installs, locked executables, permissions, unexpected files, modified manifests, unreadable folders, symlink/junction paths and missing recovery archives; never assume rollback succeeded without a post-restore audit.
6. **Signing and distribution:** Owner selects an open-source license; check Inno Setup licensing before any commercial use; sign distribution binaries and document trust, runtime redistributables and supported Windows versions.

The read-only planning tool is a conservative validation aid—not a working upgrade, a recovery archive or a replacement for tested Windows Installer behavior. The existing VM lifecycle gate remains a prerequisite.

## Phase 6F.2 — Versioned portable build and build-only receipt

A **separate, additive** builder has been implemented: `scripts/version_windows_preview.py`. It uses the verified pre-existing portable ZIP and SHA-256 sidecar as input, verifies archive members, metadata, executable digest and 40-character source commit, then creates **new** files under `build/dist`. It never modifies the existing portable ZIP, the guarded-v2 setup executable, or `build/windows-installer-stage`.

From Windows CMD, where the existing unsigned portable ZIP still exists:

```bat
git pull --ff-only
python -m pytest -q tests/test_version_windows_preview.py tests/test_plan_windows_upgrade.py tests/test_package_windows_preview.py tests/test_stage_windows_installer.py tests/test_verify_windows_installer_lifecycle.py
python scripts/version_windows_preview.py --build 203
```

**Build number 203 is a development example**, not an automatically assigned or published release ID. Assign each new build a unique monotonically increasing value (1–65535), with provenance recorded in release notes. Running the command with an already-existing output refuses to overwrite artifacts; select a new reviewed build number if needed. On success it creates:

- `build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev-build-203.zip`
- the corresponding `.zip.sha256` file
- `build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev-build-203.receipt.json`

The new ZIP includes `installer_build_version: 0.4.0.203` plus the unchanged native executable and launcher, its own manifest, and an identity marker. The sidecar checks the new ZIP hash; the JSON **build-only receipt** records old ZIP SHA-256, new ZIP SHA-256, source commit, and each ZIP payload file's SHA-256. The original ZIP remains valid with its original checksum.

**Critical distinction:** the receipt says `BUILD_ONLY_NOT_INSTALLED`. It is not an installation receipt, provenance signature, trustworthy proof of installed file ownership or permission to upgrade. The package remains **UNSIGNED**, and runtime dependencies are not yet verified on a clean machine.

After packaging, inspect build-only metadata with `type build\\dist\\kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev-build-203.receipt.json`. Do not run an installer, manually overwrite an existing Kasa directory, or label this a signed release. The guarded-v2 installer is **unchanged** and **not built from this new ZIP**. A future versioned installer and real recovery workflow require separate development, Windows compilation and disposable VM testing.
