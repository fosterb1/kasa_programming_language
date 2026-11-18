#!/usr/bin/env bash
# Netlify builds a REAL Emscripten runtime. Never silently ship JS-only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v em++ >/dev/null 2>&1; then
  EMSDK_HOME="${EMSDK_HOME:-$ROOT/.cache/emsdk}"
  mkdir -p "$(dirname "$EMSDK_HOME")"
  if [[ ! -d "$EMSDK_HOME/.git" ]]; then
    git clone --depth 1 https://github.com/emscripten-core/emsdk.git "$EMSDK_HOME"
  fi
  (
    cd "$EMSDK_HOME"
    ./emsdk install 3.1.69
    ./emsdk activate 3.1.69
  )
  # emsdk_env.sh provides em++, clang, wasm-ld and all build settings.
  # shellcheck disable=SC1091
  source "$EMSDK_HOME/emsdk_env.sh"
fi
if ! command -v em++ >/dev/null 2>&1; then
  echo 'ERROR: em++ unavailable. Refusing to publish a JS-only build.' >&2
  exit 2
fi

bash native/wasm/build.sh
python3 playground/build_site.py --require-wasm

PUBLISH="$ROOT/dist/netlify"
mkdir -p "$PUBLISH"
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile
root = Path.cwd()
zip_path = root / "dist/Kasa_Playground_Web.zip"
publish = root / "dist/netlify"
with ZipFile(zip_path) as archive:
    expected = {"index.html", "worker.js", "native/kasa-native.js", "native/kasa-native.wasm"}
    if not expected.issubset(archive.namelist()):
        raise SystemExit("Refusing incomplete WASM distribution")
    archive.extractall(publish)
print("Netlify site prepared with native WASM in", publish)
PY
