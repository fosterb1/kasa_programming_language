# Phase 6E — Windows installer destination safety and test plan

**2026-11-19 update:** The user compiled the initial guarded installer successfully with Inno Setup 7.1.1; its SHA-256 is `23be7195b31dce824b9cdb0f182c3ccfeb85d4ef548a36b7d2922760f3689613`. The **stricter guarded-v2** revision has been committed but has **not** been compiled or installed on Windows. No installation/uninstall certification exists.

## Directory collision safety change

The prior alpha setup checked only the default install path at `InitializeSetup`, allowing a custom path to bypass the guard. The revised `scripts/kasa_windows_preview.iss` checks `WizardDirValue` in Inno Setup's `PrepareToInstall` event, after the wizard chooses a directory (including `/DIR` and simulated silent-install Next clicks).

**First-install only (guarded-v2):** if the final destination **already exists at all**, even if it is empty, the installer stops before file-copy operations. This avoids the ambiguity of an unreadable or unsuccessfully enumerated folder being treated as empty. A previously installed Kasa preview, foreign app directory or custom path with personal projects is rejected. Choose a **new, nonexistent** destination. Upgrades are intentionally **not implemented**, and the presence of `kasa-install-identity.txt` does not make an occupied directory safe to overwrite. `UsePreviousAppDir=no` avoids automatic reuse of an older path.

The check is a conservative guard, **not** a security boundary against filesystem races, reparse points or inaccessible directory enumeration. Protecting against these requires separate Windows-focused testing. This revision uses the distinct `-Setup-guarded-v2.exe` output name, preserving both earlier user-built setup files. An unreadable parent directory, junction/reparse point or filesystem race still requires explicit VM validation.

## Safe recompilation on the office Windows machine

From the checked-out repository root in CMD:

```bat
git pull --ff-only
python -m pytest -q tests\test_stage_windows_installer.py
"C:\Program Files\Inno Setup 7\ISCC.exe" scripts\kasa_windows_preview.iss
dir build\dist\*Setup-guarded.exe
powershell -NoProfile -Command "Get-FileHash 'build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup-guarded-v2.exe' -Algorithm SHA256"
```

The existing `build/windows-installer-stage` directory remains valid for this source-only .iss guard change, provided the manifest and payload haven't changed. Running ISCC **builds but does not execute** setup. Targeted Python tests statically inspect the safeguard; they do not substitute for compiling or testing the wizard.

## Test installation in an authorized disposable Windows VM only

Before using the installer on any office/production Windows workstation, use a VM snapshot and test these cases:

1. **New install** to the default empty directory; run installed `kasa.cmd --version` and a temporary `.kasa` source program.
2. **Custom nonexistent folder** works; verify only intended files are placed there. An existing empty folder must be rejected.
3. **Custom occupied folder** containing `keep-me.txt` is rejected before any file changes; check the file hash stays identical.
4. **Default existing folder** (empty or occupied) and **previously installed Kasa** are rejected; no upgrade occurs.
5. **Silent install /DIR** to an occupied folder is rejected. Record exit status and setup log.
6. **Uninstall** through Windows Apps or Inno Setup; verify only Kasa-owned files are removed and `.kasa` projects outside install folder survive.
7. **PATH and elevation**: no PATH edits, no administrator prompt under an authorized per-user install.
8. **Clean machine** without Visual Studio/Python/Node: establish whether VC++ redistributables are needed.
9. **Untrusted paths and reparse points**: filesystem junctions, symlinks, unreadable dirs and race cases need separate security review before publishing.
10. **Upgrade gate** stays closed pending atomic update, version checks, user-data preservation, rollback and failure recovery tests.

Never run an unsigned preview installer just to bypass a security warning. Do not disable SmartScreen or anti-malware, or assume compilation means successful installation or uninstall. Do not claim a public release until licensing, signing, package safety and clean-machine compatibility are validated.

## Why v2 rejects even empty folders

The initial guard used `FindFirst` to enumerate the destination. If enumeration fails due to access restrictions, a naive check cannot reliably distinguish "empty directory" from "directory could not be listed." The v2 guard instead checks the existence of the final `WizardDirValue` directory (or a file at that path) via `DirExists` / `FileExists` and refuses installation when either is true. This does **not** prove safety against inaccessible parents, reparse points, unusual paths or between-check races. The stricter gate is designed to avoid known overwrites during early alpha validation, not to certify filesystem security.

The source-only regression checks verify the presence of these checks; actual Inno Setup compilation and VM testing remain necessary. Inno Setup documentation describes `PrepareToInstall` as an event that can stop Setup prior to installation when returning a non-empty error message. See https://jrsoftware.org/inno-setup/documentation/topic_scriptevents.htm.
