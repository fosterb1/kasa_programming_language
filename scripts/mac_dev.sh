#!/usr/bin/env bash
# Kasa macOS local development — no hosting, CMS or GitHub write operations.
set -euo pipefail
cd "$(dirname "$0")/.."
ACTION="${1:-doctor}"
case "$ACTION" in
  doctor)
    echo "Kasa Mac development prerequisites (read-only check)"
    echo "OS: $(uname -s) | CPU: $(uname -m)"
    if [[ "$(uname -s)" != Darwin ]]; then
      echo "NOTE: macOS certification is possible only when this runs on a Mac."
    fi
    for name in git python3 node cmake ctest clang++; do
      if command -v "$name" >/dev/null 2>&1; then
        printf 'OK       %-10s %s\n' "$name" "$(command -v "$name")"
      else
        printf 'MISSING  %-10s\n' "$name"
      fi
    done
    if command -v python3 >/dev/null 2>&1; then
      python3 -c 'import sys;print("Python:",sys.version.split()[0])'
    fi
    if command -v node >/dev/null 2>&1; then node --version; fi
    if command -v cmake >/dev/null 2>&1; then cmake --version | head -1; fi
    if command -v xcode-select >/dev/null 2>&1; then
      xcode-select -p || echo "Apple Command Line Tools may need installation: xcode-select --install"
    fi
    if command -v em++ >/dev/null 2>&1; then echo "Emscripten: available"; else
      echo "Emscripten: not installed/activated (only required for native WASM builds)"
    fi
    ;;
  setup)
    if ! command -v python3 >/dev/null 2>&1; then
      echo "Python 3 missing. Install a compatible Python before setup." >&2; exit 2
    fi
    python3 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip pytest
    echo "Local Python test environment ready; no host deployment performed."
    ;;
  quick|parity|full)
    if [[ ! -x .venv/bin/python ]]; then
      echo "Missing .venv. Run: bash scripts/mac_dev.sh setup" >&2; exit 2
    fi
    if ! command -v node >/dev/null 2>&1; then
      echo "Node.js missing. Install Node.js LTS before continuing." >&2; exit 2
    fi
    .venv/bin/python scripts/verify_local.py --profile "$ACTION" \
      --report "build/macos-${ACTION}-local.json"
    ;;
  mac-release)
    if [[ ! -x .venv/bin/python ]]; then
      echo "Missing .venv; run setup first" >&2; exit 2
    fi
    .venv/bin/python scripts/verify_macos_release.py --report build/macos-release-gate.json
    ;;
  wasm)
    if ! command -v em++ >/dev/null 2>&1; then
      echo "Emscripten not available. Activate emsdk before building WASM." >&2; exit 2
    fi
    bash native/wasm/build.sh
    python3 playground/build_site.py --require-wasm
    ;;
  studio-dry-run)
    if [[ ! -f playground/native/kasa-native.wasm || ! -f playground/native/kasa-native.js ]]; then
      echo "Build native WASM first with 'bash scripts/mac_dev.sh wasm'." >&2; exit 2
    fi
    # Intentionally no --publish or credentials; this does not change Vercel or GitHub.
    python3 scripts/release_to_academy.py
    ;;
  *)
    echo "Usage: bash scripts/mac_dev.sh {doctor|setup|quick|parity|full|mac-release|wasm|studio-dry-run}" >&2
    exit 2
    ;;
esac
