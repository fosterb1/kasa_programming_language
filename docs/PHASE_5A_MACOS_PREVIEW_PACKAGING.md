# Phase 5A — Kasa native macOS development preview

**Status:** Local packaging workflow implemented; no public installer has been signed, notarized, shipped, or certified. Test on a real Mac before any announcement. This is not Kasa 1.0.

## Prerequisites

Use the same real macOS machine on which native parity/full passed. Intel x86_64 and Apple Silicon arm64 must be separately tested. CMake, Clang, Node, and Python are development-only dependencies; the distributed Kasa native executable itself does not require Python or Node to run.

```sh
cd ~/Projects/kasa/kasa_programming_language
source .venv/bin/activate
bash scripts/mac_dev.sh full
bash scripts/mac_dev.sh package
```

The package command requires the executable at `build/kasa-local/kasa-native`, invokes its `--version` check, and creates these files under ignored local `build/dist`:

- `kasa-0.4.0-alpha-darwin-x86_64-dev.tar.gz` on an Intel Mac
- `kasa-0.4.0-alpha-darwin-x86_64-dev.tar.gz.sha256`
- For an Apple Silicon build, the architecture in the filename is `arm64`.

Each archive includes `kasa` (POSIX shell launcher), `kasa-native` (native compiled executable), `manifest.json` (source revision, architecture and executable hash), and `README.txt` (installation notes). It does not bundle CMake, Python, Node, Git, the SDK, or a compiler. No GitHub release or hosting deployment occurs.

## Test directly from the extracted archive

```sh
cd build/dist
shasum -a 256 -c kasa-0.4.0-alpha-darwin-x86_64-dev.tar.gz.sha256
tar -xzf kasa-0.4.0-alpha-darwin-x86_64-dev.tar.gz
cd kasa-0.4.0-alpha-darwin-x86_64-dev
./kasa --version
./kasa run ../../../examples/hello.kasa
```

The example path above is relative to the extracted archive directory under `build/dist`. On Apple Silicon replace `x86_64` with `arm64`. This preview is built locally, unsigned, and not notarized; do not use system-security bypasses to install unknown third-party archives.

## Optional private installation (no sudo)

From the extracted directory:

```sh
mkdir -p "$HOME/.local/opt/kasa" "$HOME/.local/bin"
cp kasa kasa-native "$HOME/.local/opt/kasa/"
ln -s "$HOME/.local/opt/kasa/kasa" "$HOME/.local/bin/kasa"
"$HOME/.local/bin/kasa" --version
```

Before creating the symbolic link, check whether `~/.local/bin/kasa` already exists. Do **not** overwrite an existing file or link. Add `~/.local/bin` to your shell PATH only if desired. Installation is user-local; no system files are modified.

Uninstall only the files created by this preview:

```sh
rm "$HOME/.local/bin/kasa"
rm "$HOME/.local/opt/kasa/kasa" "$HOME/.local/opt/kasa/kasa-native"
rmdir "$HOME/.local/opt/kasa"
```

## Verification and release boundaries

1. Run the unit tests: `.venv/bin/python -m pytest -q tests/test_package_native_preview.py`.
2. Verify the archive hash and the version output from **extracted**, not source-tree, binaries.
3. Test native source programs and compiled KBC1 examples from outside the repository on the actual Mac.
4. Confirm no dynamic dependency paths accidentally point to `build/`, and test on a second machine of the same architecture before sharing publicly.
5. Plan a signed/notarized `.pkg` and independently tested `arm64`, Windows and Linux packages later. Signing and notarization require appropriate Apple credentials and reviews.

The release-channel name is `development-preview` deliberately. Passing parity and full profile verifies language behavior on the tested machine, not portability of a packaged binary to other Macs. More hardening, reproducibility, security review, and external classroom usability testing remain before a stable installer.
