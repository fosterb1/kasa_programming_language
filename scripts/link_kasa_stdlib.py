#!/usr/bin/env python3
"""Group 0 experimental source linker. NOT language-level import or sandboxing.

Only pinned repository libraries may be concatenated with a Kasa program.
Writes only a fresh file in build/stdlib-linked; never executes any Kasa.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "build" / "stdlib-linked"
# Git object IDs are pinned to the reviewed source bytes. SHA-1 is for
# accidental mutation detection, NOT publisher authentication.
LIBRARIES = {
    "math": ("stdlib/experimental/math.kasa", "315db28ed3aa215cb1511a7e463e29f76bd06cb7"),
    "collections": ("stdlib/experimental/collections.kasa", "fc68babc09c7e51d68f84415830ff0ba68bbafa9"),
}
NAME = re.compile(r"^[a-z][a-z0-9_]*$", re.ASCII)
FUNCTION = re.compile(r"(?m)^\s*dwumadie\s+([^\s(]+)\s*\(")
MAX_SOURCE_BYTES = 50_000


class LinkError(ValueError):
    pass


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _regular_file(path: Path, base: Path) -> bool:
    """Reject symlinked parents and symlinked leaf, including Windows junctions."""
    if not path.is_relative_to(base):
        return False
    current = base
    if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
        return False
    for part in path.relative_to(base).parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            return False
    return path.is_file()


def prepare_source(application: Path, modules: list[str]) -> str:
    if not modules:
        raise LinkError("Specify at least one --module")
    if len(modules) != len(set(modules)):
        raise LinkError("Duplicate module selection is not allowed")
    if not application.is_file() or application.is_symlink():
        raise LinkError("Application source must be an existing regular file")
    app_bytes = application.read_bytes()
    try:
        app_text = app_bytes.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise LinkError("Application source must be UTF-8") from exc
    parts = []
    exported_names = set()
    for module in modules:
        if not NAME.fullmatch(module) or module not in LIBRARIES:
            raise LinkError("Unknown or unsafe library module identifier: " + module)
        rel, pinned = LIBRARIES[module]
        source = ROOT / rel
        if not _regular_file(source, ROOT):
            raise LinkError("Library source missing or linked outside standard-library root")
        # Git can check out CRLF on Windows. Hash canonical LF bytes, then
        # link exactly those verified bytes; refuse lone CR line endings.
        payload = source.read_bytes()
        if b"\r" in payload.replace(b"\r\n", b""):
            raise LinkError("Unsupported library line ending")
        payload = payload.replace(b"\r\n", b"\n")
        if git_blob_id(payload) != pinned:
            raise LinkError("Library content changed; review and re-pin before linking: " + module)
        text = payload.decode("utf-8", "strict")
        names = set(FUNCTION.findall(text))
        if not names or exported_names.intersection(names):
            raise LinkError("Missing or conflicting library function declarations")
        exported_names.update(names)
        parts.append("# Begin pinned library: " + module + "\n" + text.rstrip() + "\n")
    # Our precursor cannot isolate namespaces. Refuse obvious collisions rather
    # than silently letting applications override standard-library functions.
    if exported_names.intersection(FUNCTION.findall(app_text)):
        raise LinkError("Application function collides with a selected library")
    combined = "\n".join(parts) + "\n# Application source\n" + app_text.rstrip() + "\n"
    if len(combined.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise LinkError("Combined Kasa source exceeds the 50,000-byte limit")
    return combined


def link(application: Path, modules: list[str], output: Path) -> Path:
    # Safe root is a fixed repository path; callers cannot pick arbitrary dirs.
    output = output.absolute()
    root = OUTPUT_ROOT.absolute()
    if output.parent != root or output.suffix != ".kasa" or output.name in ("", ".kasa"):
        raise LinkError("Output must be a .kasa file directly inside build/stdlib-linked")
    if output.exists() or output.is_symlink():
        raise LinkError("Output already exists; refusing overwrite")
    if root.parent.is_symlink() or (hasattr(root.parent, "is_junction") and root.parent.is_junction()):
        raise LinkError("Build directory is a linked location")
    if root.exists() and (root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()) or not root.is_dir()):
        raise LinkError("Output directory is not a regular directory")
    # Verify input before creating any output.
    source = prepare_source(application.absolute(), modules)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise LinkError("Output directory is a symlink")
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(source)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--module", required=True, action="append", help="math or collections")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print("Created linked Kasa source:", link(args.app, args.module, args.output))
    except (LinkError, OSError, UnicodeError) as exc:
        print("Link refused:", exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
