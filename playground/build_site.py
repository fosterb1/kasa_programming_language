"""Package the Kasa Playground for static hosting.

By default, this builds the safe JavaScript-only fallback website. After running
native/wasm/build.sh with Emscripten, the same command automatically includes
the compiled C++ WebAssembly runtime and enables it in the packaged worker.
Use --require-wasm to reject accidentally producing a JS-only deployment.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "playground/index.html": "index.html",
    "playground/style.css": "style.css",
    "playground/app.js": "app.js",
    "playground/worker.js": "worker.js",
    "playground/kasa-runtime.js": "kasa-runtime.js",
    "playground/sw.js": "sw.js",
    "playground/manifest.webmanifest": "manifest.webmanifest",
    "playground/icons/kasa-192.png": "icons/kasa-192.png",
    "playground/icons/kasa-512.png": "icons/kasa-512.png",
}
WASM_FILES = {
    "playground/native/kasa-native.js": "native/kasa-native.js",
    "playground/native/kasa-native.wasm": "native/kasa-native.wasm",
}
WORKER_FLAG = "const KASA_HAS_WASM = false;"


def build_bundle(output: Path | None = None, *, require_wasm: bool = False) -> Path:
    """Produce a static ZIP; enable WASM only if both generated assets exist."""
    output = output or ROOT / "dist" / "Kasa_Playground_Web.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    have_wasm = [(ROOT / source).is_file() for source in WASM_FILES]
    if any(have_wasm) and not all(have_wasm):
        raise RuntimeError("Incomplete native build: both kasa-native.js and kasa-native.wasm are required")
    if require_wasm and not all(have_wasm):
        raise RuntimeError("WebAssembly not built. Activate Emscripten and run bash native/wasm/build.sh first")
    if all(have_wasm):
        wasm = ROOT / "playground/native/kasa-native.wasm"
        if wasm.read_bytes()[:8] != b"\x00asm\x01\x00\x00\x00":
            raise RuntimeError("WASM asset is invalid (missing WebAssembly header)")
    # A stable content digest invalidates the previous offline cache on every update.
    digest = hashlib.sha256()
    for source in (*FILES, *(WASM_FILES if all(have_wasm) else ())):
        digest.update(source.encode("utf-8"))
        digest.update((ROOT / source).read_bytes())
    revision = digest.hexdigest()[:12]
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source, destination in FILES.items():
            if destination == "sw.js":
                text = (ROOT / source).read_text(encoding="utf-8")
                if text.count("__KASA_BUILD_HASH__") != 1:
                    raise RuntimeError("Cannot safely version the offline cache")
                archive.writestr(destination, text.replace("__KASA_BUILD_HASH__", revision).encode("utf-8"))
            elif destination == "worker.js":
                text = (ROOT / source).read_text(encoding="utf-8")
                if text.count(WORKER_FLAG) != 1:
                    raise RuntimeError("Cannot patch the WASM worker flag safely")
                if all(have_wasm):
                    text = text.replace(WORKER_FLAG, "const KASA_HAS_WASM = true;")
                archive.writestr(destination, text.encode("utf-8"))
            else:
                archive.write(ROOT / source, destination)
        if all(have_wasm):
            for source, destination in WASM_FILES.items():
                archive.write(ROOT / source, destination)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Package Kasa Playground for Netlify or other static hosts")
    parser.add_argument("--require-wasm", action="store_true", help="Fail if native WebAssembly assets are missing")
    arguments = parser.parse_args()
    artifact = build_bundle(require_wasm=arguments.require_wasm)
    print(f"Created {artifact}")
    print("Native WebAssembly: " + ("included" if all((ROOT / source).is_file() for source in WASM_FILES) else "not built; JS fallback only"))
