#!/usr/bin/env python3
"""G0.5b/c opt-in linked-module differential: Python vs native C++ vs KBC1.

This is an acceptance test, NOT a native module loader. It links trusted,
experimental imports to a temporary plain Kasa source file and checks that
the existing native compiler and verified KBC1 reader preserve its output.

Run after: python scripts/verify_local.py --profile parity
Then: python scripts/verify_g05_native_kbc.py
No host networking; no Kasa source, bytecode, or catalog is modified.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from kasa import Interpreter, parse  # noqa: E402
from link_kasa_modules_hygienic import link_source  # noqa: E402
from run_kasa_modules_experimental import execute_module_source  # noqa: E402

DEFAULT_NATIVE = ROOT / "build" / "kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)
CASES = {
    "two-modules": (
        "fa math firi stdlib: m\n"
        "fa collections firi stdlib: c\n"
        "ma items = [10, 20, 30]\n"
        "ka m.kasa_sum(items)\n"
        "ka c.kasa_contains(items, 20)\n",
        "60\nnokware\n",
    ),
    "math-abs-clamp": (
        "fa math firi stdlib: m\n"
        "ka m.kasa_abs(-12)\n"
        "ka m.kasa_clamp(17, 0, 10)\n",
        "12\n10\n",
    ),
    "collections-count-and-false": (
        "fa collections firi stdlib: c\n"
        "ka c.kasa_count_equal([2, 2, 3], 2)\n"
        "ka c.kasa_contains([2, 4, 6], 3)\n",
        "2\natoro\n",
    ),
    "application-name-collision": (
        "fa math firi stdlib: m\n"
        "dwumadie kasa_sum(x)\n"
        "    sanma 999\n"
        "awiei\n"
        "ka m.kasa_sum([1, 2, 3])\n",
        "6\n",
    ),
}


def command(args: list[str], *, timeout: int = 30) -> str:
    result = subprocess.run(
        args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"Command failed (exit {result.returncode}): {args!r}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if result.stderr.strip():
        raise AssertionError(f"Unexpected stderr for {args!r}: {result.stderr}")
    return result.stdout


def reference_output(source: str, *, experimental: bool) -> str:
    output = io.StringIO()
    if experimental:
        execute_module_source(source, stdout=output)
    else:
        Interpreter(stdout=output).run(parse(source))
    return output.getvalue()


def verify(native: Path) -> None:
    native = native.resolve(strict=True)
    if not native.is_file():
        raise RuntimeError("Native executable path is not a file")
    completed = 0
    with tempfile.TemporaryDirectory(prefix="kasa-g05-native-kbc-") as temporary:
        temp = Path(temporary)
        for name, (program, expected) in CASES.items():
            # Source identity, import order, module exports and internal
            # symbol hygiene are checked before creating any intermediate.
            linked = link_source(program, filename="<g05-" + name + ">")
            original_output = reference_output(program, experimental=True)
            flattened_output = reference_output(linked, experimental=False)
            assert original_output == expected, (name, original_output, expected)
            assert flattened_output == expected, (name, flattened_output, expected)

            source_path = temp / (name + ".kasa")
            bytecode_path = temp / (name + ".kbc")
            source_path.write_text(linked, encoding="utf-8", newline="\n")

            # Native compilation and KBC1 have no access to the stdlib catalog
            # path: their only inputs are this linked source and bytecode.
            native_output = command([str(native), "run", str(source_path)])
            assert native_output == expected, (name, "native run", native_output)
            command([str(native), "check", str(source_path)])
            command([str(native), "compile", str(source_path),
                     "-o", str(bytecode_path)])
            if not bytecode_path.is_file() or bytecode_path.stat().st_size == 0:
                raise AssertionError("Missing compiled KBC1 output: " + name)
            if bytecode_path.read_bytes()[:4] != b"KBC1":
                raise AssertionError("Compiled bytecode lacks KBC1 magic: " + name)
            command([str(native), "check-bytecode", str(bytecode_path)])
            bytecode_output = command([str(native), "run-bytecode",
                                       str(bytecode_path)])
            assert bytecode_output == expected, (name, "KBC1", bytecode_output)
            completed += 1
            print("PASS native C++ + KBC1 " + name, flush=True)
    print(f"PASS G0.5 linked imports: {completed} portable cases, "
          "Python experimental / linked / native / KBC1 outputs agree")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=DEFAULT_NATIVE,
                        help="Path to existing kasa-native executable")
    args = parser.parse_args(argv)
    try:
        verify(args.native)
    except (AssertionError, OSError, RuntimeError, subprocess.TimeoutExpired,
            ValueError) as error:
        print("FAIL G0.5 native/KBC1 linked modules: " + str(error),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
