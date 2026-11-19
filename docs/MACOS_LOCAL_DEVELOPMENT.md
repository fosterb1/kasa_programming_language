# Kasa on a MacBook — local-first development (Phase 4C.2)

**Status:** Prepared for both Intel (`x86_64`) and Apple Silicon (`arm64`) Macs. This is a setup guide, **not** a claim that macOS tests have already passed on the user's machine.

## 1. Identify your Mac before installing anything

Open **Terminal** and run:

```bash
sw_vers
uname -m
xcode-select -p
```

- `arm64`: Apple Silicon (M-series).
- `x86_64`: Intel. Older MacBooks or older macOS releases may not support current Homebrew packages or the newest Node/Python builds. Check your macOS version before upgrading.
- If Command Line Tools are missing, run `xcode-select --install` and follow Apple's installer.

## 2. Check or install tools (once)

We need Git, Python 3, Node.js and CMake. No Vercel credentials and no GitHub Actions billing are required for local tests.

If Homebrew is already installed:

```bash
brew install git python node cmake
```

Otherwise first review the installation method at https://brew.sh/ . Homebrew prefixes differ on Intel (`/usr/local`) and Apple Silicon (`/opt/homebrew`). Unsupported old macOS versions may require older compatible tools or a different Mac; **do not upgrade your operating system blindly**.

Verify:

```bash
git --version
python3 --version
node --version
cmake --version
clang++ --version
```

If you also work on Kasa Academy's Next.js application, its current `package.json` expects **Node 24.22.3 or later in the Node 24 series** (`^24.22.3`). The *language-only* Node tests are less demanding. Install/select Node 24 as appropriate for the Academy and your macOS version.

## 3. Clone the two repositories on your Mac

```bash
mkdir -p ~/Projects/kasa
cd ~/Projects/kasa
git clone https://github.com/fosterb1/kasa_programming_language.git
git clone https://github.com/fosterb1/kasa-learning-academy.git
cd kasa_programming_language
bash scripts/mac_dev.sh doctor
```

No desktop-specific Windows paths are needed.

## 4. Test locally without Netlify, Vercel or Firecrawl

```bash
bash scripts/mac_dev.sh setup    # creates .venv and installs pytest
bash scripts/mac_dev.sh quick    # Python + JS: fastest feedback
bash scripts/mac_dev.sh parity   # Python/JS and native compiler parity
bash scripts/mac_dev.sh full     # comprehensive local suite
```

Reports appear under `build/macos-quick-local.json`, `build/macos-parity-local.json`, and `build/macos-full-local.json`.

If all development tests are green and the checkout is clean, run the **existing platform-specific release gate**:

```bash
bash scripts/mac_dev.sh mac-release
```

It tests both the default VM and experimental KBC2 build. This is heavier, and the experimental build needs Boost headers (`brew install boost` on a compatible Homebrew installation).

## 5. Run the Academy independently

```bash
cd ~/Projects/kasa/kasa-learning-academy
npm ci
npm run test:smoke
```

The tests run locally without a production deployment. Running the full Next.js dev server additionally needs valid local Payload/PostgreSQL environment variables; do not put credentials in GitHub.

## 6. Build browser WebAssembly only when needed

The browser's native engine uses Emscripten. Install and activate a compatible `emsdk` version (https://emscripten.org/docs/getting_started/downloads.html) in a **separate step**. Then:

```bash
cd ~/Projects/kasa/kasa_programming_language
bash scripts/mac_dev.sh wasm
bash scripts/mac_dev.sh studio-dry-run
```

The final command checks release packaging but **never publishes anything**. Browser engine builds still require an actual browser test for release approval.

## 7. Daily work: edit → test → commit; deploy much less often

```bash
cd ~/Projects/kasa/kasa_programming_language
git pull --ff-only
# Edit code locally in VS Code
bash scripts/mac_dev.sh quick
git status
```

After milestone verification, commit/push reviewed changes. Avoid using production deployment as a substitute for local tests. An approved Academy release is a distinct reviewed publishing action: `scripts/release_to_academy.py`.

## Error-category parity (new Phase 4C.2 tests)

`tests/conformance_diagnostics_4c.json` is the shared source for nine expected error categories. The normal quick/parity/full verification runner now invokes these tests automatically:

- JavaScript browser interpreter: `node --test tests/test_diagnostics_4c.cjs`
- Python reference: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_diagnostics_4c.py`
- Native C++ VM (after compiling): `python3 native/tests/diagnostic_conformance.py build/kasa-local/kasa-native`

Exact English error strings are **not** considered the language contract. All three runtimes must reject errors with compatible **categories**. This gate does not establish complete WebAssembly, KBC1 or experimental KBC2 diagnostic parity; those require their own checks.

## If a test fails

Paste the **last error output**, macOS version (`sw_vers`) and architecture (`uname -m`). Do not delete the source code, edit language semantics to silence a test, or upgrade tools without checking the failure first.

**Research basis:** Apple Command Line Tools; https://brew.sh/ ; https://docs.brew.sh/Installation ; https://nodejs.org/en/download ; https://docs.python.org/3/library/venv.html .

## Apple Clang 14 floating-point formatter compatibility (Phase 4C.2 discovery)

On an **Intel MacBook running Ventura 13.7.8**, with Apple Clang **14.0.3** and the macOS 13.3 SDK, the initial C++ build failed in `native/include/kasa/float_display.hpp` because Apple's libc++ marked floating-point `std::to_chars(..., std::chars_format::scientific)` unavailable. Installing CMake fixed project configuration but **not** that platform-specific C++ API error.

A guarded compatibility implementation now uses standard C++20 iostreams with the classic C locale on Apple libc++, choosing the first 1–17-significant-digit scientific rendering that parses back into the exact binary64 bit pattern. The previous `std::to_chars` implementation stays in place on other platforms. Negative zero, Python-like exponent thresholds and non-finite rejection remain in the shared display logic. No new Kasa language syntax was introduced.

Before first use on the user's actual Mac, the alternative was independently evaluated on Linux against **9,999 deterministic finite IEEE-754 values**; the simplified reference prototype had **zero output mismatches** with Python `repr`. That is *preliminary evidence*, **not** validation of the compiled production header or of Apple's libc++ implementation.

After updating the repository, rerun with the already activated Python environment:

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
source .venv/bin/activate
bash scripts/mac_dev.sh parity
```

The verifier's `Native decimal display smoke` and `Native/Python decimal display differential` stages will test the **actual newly built Apple fallback**, including thousands of binary64 values. Do not bypass or delete these checks if the outputs differ.

The warnings about unused `version` parameters in `native/src/bytecode.cpp` were not the build-stopping issue. A new build should not require changing the Xcode/Command Line Tools or OS for this formatter.
