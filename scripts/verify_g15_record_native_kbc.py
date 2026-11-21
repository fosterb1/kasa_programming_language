#!/usr/bin/env python3
"""G1.5 source-only record parity through Python, native C++ and KBC1.

Uses temporary source/KBC files. No native record syntax or binary change.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from kasa import Interpreter, parse

NATIVE = ROOT / "build/kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)


def command(exe: Path, *args: str) -> str:
    process = subprocess.run([str(exe), *args], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=60, check=False)
    if process.returncode or process.stderr:
        raise AssertionError(f"Native {args[0]} failed: return={process.returncode}; "
                             f"stdout={process.stdout!r}; stderr={process.stderr!r}")
    return process.stdout


def verify(binary: Path):
    native = binary.resolve(strict=True)
    if not native.is_file():
        raise ValueError("Missing native executable")
    library = (ROOT / "stdlib/g15/records.kasa").read_text(encoding="utf-8")
    items = json.loads((ROOT / "tests/g15_record_cases.json").read_text(encoding="utf-8"))["cases"]
    if len(items) != 10:
        raise ValueError("Unexpected fixture count")
    with tempfile.TemporaryDirectory(prefix="kasa-g15-record-") as dirname:
        tmp = Path(dirname)
        for item in items:
            name = item["id"]
            source = library + "\n" + item["source"]
            out = io.StringIO()
            Interpreter(stdout=out).run(parse(source))
            if out.getvalue() != item["output"]:
                raise AssertionError(name + ": Python mismatch")
            text_path = tmp / (name + ".kasa")
            kbc_path = tmp / (name + ".kbc")
            text_path.write_text(source, encoding="utf-8", newline="\n")
            command(native, "check", str(text_path))
            if command(native, "run", str(text_path)) != item["output"]:
                raise AssertionError(name + ": native output mismatch")
            command(native, "compile", str(text_path), "-o", str(kbc_path))
            if not kbc_path.is_file() or not kbc_path.read_bytes().startswith(b"KBC1"):
                raise AssertionError(name + ": KBC1 was not produced")
            command(native, "check-bytecode", str(kbc_path))
            text_path.unlink()
            if command(native, "run-bytecode", str(kbc_path)) != item["output"]:
                raise AssertionError(name + ": KBC1 output mismatch after source deletion")
            print("PASS G1.5 Python/native/KBC1 " + name, flush=True)
    print(f"PASS G1.5: {len(items)} record cases; no bytecode format changes")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    args = parser.parse_args(argv)
    try:
        verify(args.native)
    except (OSError, ValueError, AssertionError, subprocess.TimeoutExpired) as exc:
        print("FAIL G1.5 native/KBC1: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
