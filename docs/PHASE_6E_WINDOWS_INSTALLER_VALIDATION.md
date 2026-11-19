# Phase 6E — Windows installer destination safety and test plan

**2026-11-19 update:** The user compiled the initial guarded installer successfully with Inno Setup 7.1.1; its SHA-256 is `23be7195b31dce824b9cdb0f182c3ccfeb85d4ef548a36b7d2922760f3689613`. The **stricter guarded-v2** revision was compiled successfully on the user's Windows PC using Inno Setup 7.1.1 (size **2,229,729 bytes**, SHA-256 **`2af6ac1347da03870fe1e80543c1fba1af78fac12d087103a52f230f1c003b87`**). It has **not** been installed or uninstalled in a disposable VM. No installation/uninstall certification exists.

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

## Lifecycle harness added — 2026-11-19

The first repeatable Windows lifecycle audit is `scripts/verify_windows_installer_lifecycle.py`. It requires **no installer execution by default**. Its expected guarded-v2 installer hash is the user's reported SHA-256 `2af6ac1347da03870fe1e80543c1fba1af78fac12d087103a52f230f1c003b87` and it reports to `build/windows-installer-lifecycle.json`.

For **read-only preflight on the office workstation**:

```bat
git pull --ff-only
python -m pytest -q tests\test_package_windows_preview.py tests\test_stage_windows_installer.py tests\test_verify_windows_installer_lifecycle.py
python scripts\verify_windows_installer_lifecycle.py
type build\windows-installer-lifecycle.json
```

This verifies the SHA-256 and records a JSON test plan. **It does not install, uninstall, invoke, or execute the unsigned Setup executable.** A verified hash is artifact identity, not a digital signature or trust certificate.

For eventual execution, **copy the verified installer and the audited repository checkout into a disposable Windows VM you own or are authorized to test in; create a VM snapshot first.** After independently checking that the VM has no important personal/office data and the installer matches the expected hash, explicitly run **inside the VM only**:

```bat
python scripts\verify_windows_installer_lifecycle.py --execute-in-disposable-vm --acknowledge-vm-snapshot DISPOSABLE-VM-SNAPSHOT-CONFIRMED
```

The harness checks Windows VM identity using `Win32_ComputerSystem` and refuses to execute setup without the explicit flag, exact snapshot acknowledgment and expected installer hash. VM identity recognition is **heuristic** and not a guarantee of isolation or authorization. The harness uses `/VERYSILENT` only after these gates; it installs into a new temporary VM workspace, tests occupied destination rejection, runs the installed native executable, invokes Inno Setup's generated uninstaller, and checks two external sentinel files. The script retains a JSON record of results. It does not grant administrator rights, change PATH or disable security software.

**Evidence limitations:** the latest source-level tests passed **21/21** in a separate test environment (including one simulated second-install attempt); the user earlier confirmed **6/6** lifecycle harness tests on Windows, before the new simulated check was added. No user VM lifecycle execution has yet been reported. This harness checks only its own process's PATH string, **not** persistent user/machine environment variables in the registry or the shell; a separate VM inspection is required to establish no persistent PATH modification. It doesn't establish clean-machine VC++ runtime requirements, native `kasa.cmd` launcher behavior after installer installation, GUI wizard defaults, full registry uninstall ownership, rollback on crashes, or junction/ACL race safety. It requires VM snapshots before destructive rollback tests and must not be used on a real office workstation. Failures must not be interpreted as successful verification.

## Phase 6E additional harness coverage — 2026-11-19

The opt-in VM-only harness now also refuses a second installation to the same directory and checks that the installed `kasa.cmd --version` launcher works. The supplemental test uses **mocked executable commands** and does not install Kasa or simulate Windows file ownership. On a disposable VM the relevant planned checks are:

1. Occupied foreign directory refuses installation without modifying a sentinel.
2. Fresh installation into a nonexistent directory succeeds.
3. Immediate second installer execution to that directory refuses to overwrite the existing Kasa binary.
4. Native `kasa-native.exe --version`, Twi program and user-facing `kasa.cmd --version` work.
5. Uninstall removes its native executable and preserves external sentinel files.

The run report records process exit codes and stdout/stderr tails. The temporary workspace is created under a new VM-only temp directory and automatically cleaned after the run; a VM snapshot remains the correct recovery mechanism. The harness **does not** verify persistent registry PATH, all uninstall registry entries, accessible directory races, or actual upgrades.

On the **office Windows PC** use only the safe command sequence:

```bat
git pull --ff-only
python -m pytest -q tests/test_package_windows_preview.py tests/test_stage_windows_installer.py tests/test_verify_windows_installer_lifecycle.py
python scripts/verify_windows_installer_lifecycle.py
```

The last command is **read-only** and should again report `Installer SHA-256 matches: True` and `Installer executed: False`. No installer recompilation is needed; the .iss source and pinned compiled guarded-v2 executable are unchanged. Only run the execution switch in an authorized disposable Windows VM with a real snapshot; the VM identifier is not sufficient proof of isolation by itself.
