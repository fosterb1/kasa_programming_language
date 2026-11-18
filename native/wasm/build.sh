#!/usr/bin/env bash
# Build Kasa's actual C++ compiler/VM for browser WebAssembly.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if ! command -v em++ >/dev/null 2>&1; then
  echo 'Emscripten em++ not found. Install/activate emsdk first: https://emscripten.org/docs/getting_started/downloads.html' >&2
  exit 2
fi
mkdir -p "$ROOT/playground/native"
em++ \
  -std=c++20 -O2 -fexceptions \
  -I"$ROOT/native/include" \
  "$ROOT/native/src/lexer.cpp" \
  "$ROOT/native/src/parser.cpp" \
  "$ROOT/native/src/compiler.cpp" \
  "$ROOT/native/src/vm.cpp" \
  "$ROOT/native/wasm/bridge.cpp" \
  --no-entry \
  -s MODULARIZE=1 \
  -s EXPORT_NAME=createKasaModule \
  -s ENVIRONMENT=worker \
  -s ALLOW_MEMORY_GROWTH=1 \
  -s INITIAL_MEMORY=16777216 \
  -s FILESYSTEM=0 \
  -s ASSERTIONS=0 \
  -s 'EXPORTED_FUNCTIONS=["_kasa_run","_kasa_free"]' \
  -s 'EXPORTED_RUNTIME_METHODS=["ccall","UTF8ToString"]' \
  -o "$ROOT/playground/native/kasa-native.js"
ls -lh "$ROOT/playground/native/kasa-native.js" "$ROOT/playground/native/kasa-native.wasm"
if command -v node >/dev/null 2>&1; then
  node "$ROOT/native/wasm/validate_artifacts.mjs"
fi
echo 'Now run: python playground/build_site.py --require-wasm'
