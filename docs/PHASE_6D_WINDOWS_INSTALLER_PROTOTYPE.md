# Phase 6D — Windows installer prototype (not installed or released)

**Status, 2026-11-19:** installer source and integrity-checked staging are committed. The user independently ran the 10 targeted Python tests (**10 passed**), staged five payload files, and compiled an installer with **Inno Setup 7.1.1**, which reported **Successful compile**. **Actual Windows installation, upgrades and uninstallation have not yet been tested.**

## Design boundaries

- **Inno Setup source (compiled with 7.1.1)**: `scripts/kasa_windows_preview.iss` (no application is installed just by storing this source file).
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

## Optional actual setup compilation (verified with Inno Setup 7.1.1)

Only after reviewing the `.iss` script and staging manifest, invoke the locally installed Inno Setup compiler `ISCC.exe`, e.g. from the Inno Setup application or its command line. It will compile an unsigned setup executable in `build/dist` with name `kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup.exe`. **Building the installer does not install it.**

Do not run the resulting unsigned setup on a production/office machine as a release test. First use a disposable test VM or a machine on which you have authorization to test installations. Do not bypass SmartScreen, weaken anti-malware settings or use administrator privileges to force execution.

Before further rollout, verify actual installer compilation, install folder ownership/collisions, default install location and start menu shortcut, clean uninstall, no PATH edits, clean-machine runtime dependencies, rollback of failed installs and upgrade version rules. No public release is approved.

## Real office Windows compile evidence — 2026-11-19

User console confirms:

- `python -m pytest -q tests\\test_package_windows_preview.py tests\\test_stage_windows_installer.py` → **10 passed in 0.54s**.
- `python scripts\\stage_windows_installer.py` → staged five files: `kasa-native.exe` (389,120 bytes), `kasa.cmd` (70 bytes), `manifest.json` (452 bytes), `README.txt` (634 bytes), and `kasa-install-identity.txt` (38 bytes).
- `"C:\\Program Files\\Inno Setup 7\\ISCC.exe" scripts\\kasa_windows_preview.iss` → Inno Setup **7.1.1**, **Successful compile**, output `build\\dist\\kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup.exe` (**2,229,739 bytes**).
- Two consecutive `Get-FileHash -Algorithm SHA256` runs agree: `e46ccc0c29c4c038d11c4b548b0eed787c7aed8a849400cb55178703f66d46a6`.

**Caution:** The installation guard in `InitializeSetup` checks only the *default* install location. It does not yet audit a custom folder chosen during the wizard, and the identity marker is not proof of ownership. Therefore this *compiled artifact* is **not yet approved for real installation**. Test and harden installation path collision behavior first; use an authorized disposable VM for eventual installation and uninstall tests. This SHA-256 represents the user-built unmodified prototype; subsequent source changes require recompiling and producing a new checksum. The compiler's "Non-commercial use only" notice also means licensing/usage terms should be checked before distributing or commercializing the toolchain output.
