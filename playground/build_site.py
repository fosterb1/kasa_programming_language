"""Package the Kasa browser playground for static hosting.

Run from any working directory with: python playground/build_site.py
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "playground/index.html": "index.html",
    "playground/style.css": "style.css",
    "playground/app.js": "app.js",
    "playground/worker.js": "worker.js",
    "playground/kasa-runtime.js": "kasa-runtime.js",
}


def build_bundle(output: Path | None = None) -> Path:
    """Create a portable, static-only deployment archive."""
    output = output or ROOT / "dist" / "Kasa_Playground_Web.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source, destination in FILES.items():
            archive.write(ROOT / source, destination)
    return output


if __name__ == "__main__":
    print(f"Created {build_bundle()}")
