"""Package the Kasa Playground for static hosting.

By default, this builds the safe JavaScript-only fallback website. After running
native/wasm/build.sh with Emscripten, the same command automatically includes
the compiled C++ WebAssembly runtime and enables it in the packaged worker.
Use --require-wasm to reject accidentally producing a JS-only deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "playground/index.html": "index.html",
    "playground/style.css": "style.css",
    "playground/app.js": "app.js",
    "playground/diagnostics.js": "diagnostics.js",
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
MODULE_FLAG = "const KASA_HAS_PINNED_MODULES = false;"
SERVICE_WORKER_MODULE_FLAG = "const KASA_PACKAGED_MODULES = false;"
MODULE_DESTINATION = "kasa-pinned-modules.js"


def packaged_pinned_modules(root: Path) -> bytes:
    """Verify fixed local catalog and produce a deterministic, inert JS asset."""
    catalog = json.loads((root / "stdlib/catalog.json").read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("modules"), list):
        raise RuntimeError("Invalid packaged Kasa module catalog")
    expected = {
        "math": ("stdlib/experimental/math.kasa", {"kasa_abs", "kasa_clamp", "kasa_sum"}),
        "collections": ("stdlib/experimental/collections.kasa", {"kasa_count_equal", "kasa_contains"}),
    }
    modules = {}
    if len(catalog["modules"]) != len(expected):
        raise RuntimeError("Unexpected number of packaged Kasa modules")
    for entry in catalog["modules"]:
        module_id = entry.get("id")
        if module_id not in expected or module_id in modules:
            raise RuntimeError("Unknown or duplicate packaged module")
        source_path, exports = expected[module_id]
        if entry.get("source") != source_path or set(entry.get("exports", [])) != exports or len(entry["exports"]) != len(exports) or entry.get("dependencies") != []:
            raise RuntimeError("Packaged Kasa module metadata mismatch")
        current = root
        for part in source_path.split("/"):
            current = current / part
            if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
                raise RuntimeError("Linked packaged module source rejected")
        payload = current.read_bytes()
        if b"\r" in payload.replace(b"\r\n", b""):
            raise RuntimeError("Unexpected module line ending")
        payload = payload.replace(b"\r\n", b"\n")
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        if entry.get("content_identity") != digest:
            raise RuntimeError("Packaged Kasa module source hash mismatch: " + module_id)
        modules[module_id] = {"source": payload.decode("utf-8", "strict"), "exports": entry["exports"]}
    # Emit ASCII-safe JSON as a JavaScript literal; no source interpolation.
    serialized = json.dumps(modules, ensure_ascii=True, sort_keys=True)
    return ("/* Verified, local Kasa standard libraries; generated at build time. */\n"
            "self.KasaPinnedModules = Object.freeze(" + serialized + ");\n").encode("utf-8")



def build_bundle(output: Path | None = None, *, require_wasm: bool = False) -> Path:
    """Produce a hosting-neutral static ZIP; enable WASM only with complete assets."""
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
    pinned_asset = packaged_pinned_modules(ROOT)
    # A stable content digest invalidates the previous offline cache on every update.
    digest = hashlib.sha256()
    for source in (*FILES, *(WASM_FILES if all(have_wasm) else ())):
        digest.update(source.encode("utf-8"))
        digest.update((ROOT / source).read_bytes())
    digest.update(MODULE_DESTINATION.encode("utf-8"))
    digest.update(pinned_asset)
    revision = digest.hexdigest()[:12]
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source, destination in FILES.items():
            if destination == "sw.js":
                text = (ROOT / source).read_text(encoding="utf-8")
                if text.count("__KASA_BUILD_HASH__") != 1:
                    raise RuntimeError("Cannot safely version the offline cache")
                if text.count(SERVICE_WORKER_MODULE_FLAG) != 1:
                    raise RuntimeError("Cannot safely patch offline module cache flag")
                text = text.replace(SERVICE_WORKER_MODULE_FLAG, "const KASA_PACKAGED_MODULES = true;")
                archive.writestr(destination, text.replace("__KASA_BUILD_HASH__", revision).encode("utf-8"))
            elif destination == "worker.js":
                text = (ROOT / source).read_text(encoding="utf-8")
                if text.count(WORKER_FLAG) != 1:
                    raise RuntimeError("Cannot patch the WASM worker flag safely")
                if text.count(MODULE_FLAG) != 1:
                    raise RuntimeError("Cannot safely patch the module worker flag")
                text = text.replace(MODULE_FLAG, "const KASA_HAS_PINNED_MODULES = true;")
                if all(have_wasm):
                    text = text.replace(WORKER_FLAG, "const KASA_HAS_WASM = true;")
                archive.writestr(destination, text.encode("utf-8"))
            else:
                archive.write(ROOT / source, destination)
        archive.writestr(MODULE_DESTINATION, pinned_asset)
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
