#!/usr/bin/env python3
"""G1.2.4 explicit native/KBC1 differential gate; trusted-local only.

No native import grammar, bytecode format changes, public artifact publication,
or untrusted compilation service. Uses the existing native executable.
"""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from kasa import Interpreter, parse
from link_kasa_modules_hygienic import link_source
from run_kasa_modules_experimental import execute_module_source

NATIVE = ROOT / "build" / "kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)
CASES = {
    "g1-scores": (
        "fa math firi stdlib: m\n"
        "ma scores = [40, 60, 80, 90]\n"
        "ka m.kasa_total(scores)\n"
        "ka m.kasa_average_or(scores, 0)\n"
        "ka m.kasa_count_above(scores, 60)\n",
        "270\n67.5\n2\n",
    ),
    "g1-collections": (
        "fa collections firi stdlib: c\n"
        "ka c.kasa_first_index([4, 8, 4], 4)\n"
        "ka c.kasa_last_index([4, 8, 4], 4)\n"
        "ka c.kasa_count_distinct([1, 2, 1, 3])\n"
        "ka c.kasa_all_equal([8, 8])\n",
        "0\n2\n3\nnokware\n",
    ),
    "g1-two-modules": (
        "fa math firi stdlib: m\n"
        "fa collections firi stdlib: c\n"
        "ka m.kasa_min_or([5, -4, 2], 99)\n"
        "ka m.kasa_max_or([5, -4, 2], 99)\n"
        "ka c.kasa_all_equal([])\n",
        "-4\n5\nnokware\n",
    ),
}


def invoke(native: Path, *args: str) -> str:
    result = subprocess.run([str(native), *args], cwd=ROOT,
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60, check=False)
    if result.returncode != 0 or result.stderr:
        raise AssertionError(
            f"Native {args[0]} rejected input: exit={result.returncode}, "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
    return result.stdout


def verify(native_path: Path) -> None:
    native = native_path.resolve(strict=True)
    if not native.is_file() or native.is_symlink():
        raise RuntimeError("Native executable must be a regular trusted-local file")
    with tempfile.TemporaryDirectory(prefix="kasa-g124-native-") as folder:
        temp = Path(folder)
        for label, (program, expected) in CASES.items():
            linked = link_source(program, filename=f"<{label}>", generation="g1")
            imported = io.StringIO()
            execute_module_source(program, stdout=imported, generation="g1")
            flat = io.StringIO()
            Interpreter(stdout=flat).run(parse(linked))
            if imported.getvalue() != expected or flat.getvalue() != expected:
                raise AssertionError(f"{label}: Python G1/import/link output mismatch")

            source = temp / (label + ".kasa")
            bytecode = temp / (label + ".kbc")
            source.write_text(linked, encoding="utf-8", newline="\n")
            invoke(native, "check", str(source))
            actual_source = invoke(native, "run", str(source))
            if actual_source != expected:
                raise AssertionError(f"{label}: native interpreter output mismatch: {actual_source!r}")
            invoke(native, "compile", str(source), "-o", str(bytecode))
            if not bytecode.is_file() or not bytecode.read_bytes().startswith(b"KBC1"):
                raise AssertionError(f"{label}: missing or invalid KBC1 magic")
            invoke(native, "check-bytecode", str(bytecode))
            if invoke(native, "run-bytecode", str(bytecode)) != expected:
                raise AssertionError(f"{label}: KBC1 output mismatch")
            source.unlink()
            if invoke(native, "run-bytecode", str(bytecode)) != expected:
                raise AssertionError(f"{label}: KBC1 execution depends on linked source")
            print("PASS G1 Python + native C++ + independent KBC1 " + label, flush=True)
    print(f"PASS G1.2.4: {len(CASES)} local differential cases; KBC1 unchanged")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    args = parser.parse_args(argv)
    try:
        verify(args.native)
    except (OSError, ValueError, RuntimeError, AssertionError,
            subprocess.TimeoutExpired) as error:
        print("FAIL G1.2.4 local native/KBC1 gate: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
