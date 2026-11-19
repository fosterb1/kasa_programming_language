# Phase 6C — Windows x64 portable Kasa developer preview

**Status:** Tooling implemented, pending first real Windows package creation and extract-and-run verification. Not an installer, signed release, or public download. Phase 6B user reports full Windows verification passed following POSIX-only test isolation; retain the exact report for provenance.

## Create the portable package on the office Windows machine

In the repository root, using Command Prompt with the Kasa venv and a configured Visual Studio Build Tools environment:

```bat
git pull --ff-only
python scripts\verify_local.py --profile full --report build\windows-full.json
python -m pytest -q tests\test_package_windows_preview.py
python scripts\package_windows_preview.py
dir build\dist\*windows-x64-UNSIGNED-dev*
```

Only continue packaging if full verification shows **Passed: 19 | Failed: 0 | Not run: 0**. The package script inspects and executes `build\kasa-local\Release\kasa-native.exe --version`, checks the source timestamp to prevent repackaging stale native code, and fails when artifacts with the same name already exist. It never edits your PATH, registry, `Program Files`, or installed Kasa.

The output is named `kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip`, with a matching `.zip.sha256`. The ZIP contains **exactly** four files under one folder: native `kasa-native.exe`, `kasa.cmd` launcher, `manifest.json` source/binary digests, and `README.txt`. There is no auto-updater or uninstaller.

## Verify and run from a new extraction directory

From the project root in Command Prompt:

```bat
powershell -NoProfile -Command "Get-FileHash 'build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip' -Algorithm SHA256"
type build\dist\kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip.sha256
powershell -NoProfile -Command "Expand-Archive -LiteralPath 'build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip' -DestinationPath 'build/portable-windows-test' -ErrorAction Stop"
cd build\portable-windows-test\kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev
kasa.cmd --version
kasa.cmd run ..\..\..\examples\hello.kasa
```

Compare the two SHA-256 hashes; the checksum is an **integrity** check, not a code-signing identity check. The extracted directory is inside `build/` and is separate from development source. If this directory already exists, select a new `-DestinationPath`; the packaging script deliberately refuses to overwrite artifacts.

The `kasa.cmd` launcher resolves the adjacent `kasa-native.exe` using `%~dp0`, so it can run from a different current directory. `kasa-native.exe` is a C++20 native VM executable and does not need Python or Node to execute; Windows may require Visual C++ redistributables. Test a Windows machine **without Visual Studio Build Tools** to learn what redistributables need bundling.

## Security and compatibility limitations

- ZIP is unsigned and intended only for local testing; do not ask users to disable SmartScreen or antivirus.
- Never assume that a successful MSVC build proves Windows 11 compatibility, x86, ARM64, Windows Server, or clean-PC runtime dependencies.
- This preview is **portable**: it does not register a package or install a PATH command. Removing the extracted directory removes only this preview.
- Do not run arbitrary untrusted Kasa bytecode or distribute this alpha as a secure sandbox.
- Phase 6D will design a genuine installer, opt-in install path, signed publishing and safe upgrades/uninstall only after portable ZIP validation.
