#!/usr/bin/env python3
"""Experimental Kasa module-to-KBC1 front-end (explicit opt-in).

Consumes the SHA-256-pinned Kasa stdlib catalog, links module imports to a
temporary ordinary Kasa source, invokes the existing native compiler, checks
KBC1 integrity, then publishes a NEW bytecode file under build/g05-compiled.

This is NOT a native import grammar extension, general package manager, or
KBC1 format change. Never overwrite an output, even if compilation fails.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kasa.core import KasaError  # noqa: E402
from link_kasa_modules_hygienic import HygienicLinkError, link_source  # noqa: E402
from validate_kasa_catalog import CatalogError  # noqa: E402

DEFAULT_NATIVE = ROOT / "build" / "kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)
OUTPUT_ROOT = ROOT / "build" / "g05-compiled"
MAX_INPUT_BYTES = 50_000


class CompileError(ValueError):
    pass


def _linked_directory(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _invoke(native: Path, command: str, file: Path, output: Path | None = None):
    args = [str(native), command, str(file)]
    if output is not None:
        args.extend(["-o", str(output)])
    process = subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    if process.returncode or process.stderr:
        raise CompileError(
            f"Native {command} failed (exit {process.returncode}): "
            + (process.stderr.strip() or process.stdout.strip())
        )
    return process.stdout


def compile_modules(application: Path, output: Path, *, native: Path = DEFAULT_NATIVE,
                    root: Path = ROOT) -> Path:
    root = root.absolute()
    destination = output.absolute()
    permitted = root / "build" / "g05-compiled"
    if destination.parent != permitted or destination.suffix != ".kbc" or destination.name == ".kbc":
        raise CompileError("Output must be a .kbc file directly within build/g05-compiled")
    if any(_linked_directory(folder) for folder in (root, root / "build", permitted)):
        raise CompileError("Linked output directory refused")
    if permitted.exists() and not permitted.is_dir():
        raise CompileError("Output directory is not a directory")
    if destination.exists() or destination.is_symlink():
        raise CompileError("Refusing to overwrite existing bytecode output")
    if not application.is_file() or _linked_directory(application):
        raise CompileError("Application must be an existing regular source file")
    if application.stat().st_size > MAX_INPUT_BYTES:
        raise CompileError("Application exceeds the source-size budget")
    payload = application.read_bytes()
    if len(payload) > MAX_INPUT_BYTES:
        raise CompileError("Application exceeds the source-size budget")
    source = payload.decode("utf-8", "strict")
    # Trust check, parse and namespace isolation all precede output creation.
    linked = link_source(source, root=root, filename=str(application))
    executable = native.absolute()
    if not executable.is_file() or _linked_directory(executable):
        raise CompileError("Native executable missing or linked: " + str(executable))
    with tempfile.TemporaryDirectory(prefix="kasa-g05-compile-") as folder:
        directory = Path(folder)
        intermediate = directory / "linked.kasa"
        compiled = directory / "linked.kbc"
        intermediate.write_text(linked, encoding="utf-8", newline="\n")
        _invoke(executable, "check", intermediate)
        _invoke(executable, "compile", intermediate, compiled)
        if not compiled.is_file():
            raise CompileError("Native compiler produced no bytecode")
        result = compiled.read_bytes()
        if len(result) < 20 or result[:4] != b"KBC1":
            raise CompileError("Native compiler did not produce KBC1 bytecode")
        _invoke(executable, "check-bytecode", compiled)

        # Every validation is completed before publication. 'xb' creates the
        # destination exclusively, refusing races with an existing file.
        permitted.mkdir(parents=True, exist_ok=True)
        if _linked_directory(permitted):
            raise CompileError("Output directory became linked")
        created = False
        try:
            with destination.open("xb") as handle:
                created = True
                handle.write(result)
        except OSError:
            if created:
                destination.unlink(missing_ok=True)
            raise
    return destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--native", type=Path, default=DEFAULT_NATIVE)
    args = parser.parse_args(argv)
    try:
        output = compile_modules(args.app, args.output, native=args.native)
    except (CompileError, HygienicLinkError, KasaError, CatalogError,
            OSError, UnicodeError, subprocess.TimeoutExpired) as error:
        print("G0.5 module compile refused: " + str(error), file=sys.stderr)
        return 2
    print("Compiled experimental Kasa modules to verified KBC1:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
