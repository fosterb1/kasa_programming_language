# Phase 6D — Windows installer prototype (not installed or released)

**Status, 2026-11-19:** installer source and integrity-checked staging are committed; 10/10 targeted Windows-package/staging Python regression tests passed on an independent POSIX test host. **Inno Setup compilation, actual Windows installation, upgrade and uninstallation have not yet been tested.**

## Design boundaries

- **Inno Setup 6** source: `scripts/kasa_windows_preview.iss` (no application is installed just by storing this source file).
- Per-user default install under `%LOCALAPPDATA%\Programs\Kasa Preview`, with `PrivilegesRequired=lowest`.
- Windows Add/Remove Programs uninstall record via Inno Setup, and a Start Menu uninstall shortcut.
- No global or user PATH modification; users run `kasa.cmd` from the installation directory.
- No Run section, background services, network calls, custom elevated install actions or auto-updaters.
- Default install location refuses to overwrite a pre-existing directory without the package's identity marker. This marker is **not a cryptographic signature**; the prototype requires a thorough installer threat review.
- End-user `.kasa` projects outside the preview install directory are never among the packaged file entries. A user who deliberately saves personal data inside that app directory must back it up before uninstalling.
- The source currently sets `AppVersion=0.4.0` for a first-install prototype. **Versioned upgrades are not implemented or validated yet**; do not treat repeated runs of this installer as a certified upgrade workflow.

## Stage exactly the verified ZIP contents (no installation)

From repository root in an ordinary Windows CMD terminal:

```bat
git pull --ff-only
python -m pytest -q tests\test_package_windows_preview.py tests\test_stage_windows_installer.py
python scripts\stage_windows_installer.py
dir build\windows-installer-stage
```

The staging tool refuses a missing or modified ZIP, mismatched manifest/digest, unexpected extra file, or an existing staging directory. Its output is limited to a newly created directory under `build/windows-installer-stage`. **It does not install any software.**

If you want to refresh a previous stage, preserve the old one separately before choosing a fresh staging destination with `--output`; do not blindly delete files in an office environment.

## Optional actual setup compilation (requires locally installed Inno Setup 6)

Only after reviewing the `.iss` script and staging manifest, invoke the locally installed Inno Setup 6 compiler `ISCC.exe`, e.g. from the Inno Setup application or its command line. It will compile an unsigned setup executable in `build/dist` with name `kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup.exe`. **Building the installer does not install it.**

Do not run the resulting unsigned setup on a production/office machine as a release test. First use a disposable test VM or a machine on which you have authorization to test installations. Do not bypass SmartScreen, weaken anti-malware settings or use administrator privileges to force execution.

Before further rollout, verify actual installer compilation, install folder ownership/collisions, default install location and start menu shortcut, clean uninstall, no PATH edits, clean-machine runtime dependencies, rollback of failed installs and upgrade version rules. No public release is approved.
