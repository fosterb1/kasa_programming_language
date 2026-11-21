#!/usr/bin/env python3
"""G1.4 source-only table fixtures through native C++ and independent KBC1.

Not a Kasa import, new bytecode format, security boundary or production tool.
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
from kasa import Interpreter, parse  # noqa: E402

NATIVE = ROOT / "build/kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)


def invoke(binary: Path, *args: str) -> str:
    done = subprocess.run([str(binary), *args], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=60, check=False)
    if done.returncode or done.stderr:
        raise AssertionError(f"Native {args[0]} failed: exit={done.returncode}, "
                             f"stderr={done.stderr!r}, stdout={done.stdout!r}")
    return done.stdout


def verify(binary: Path) -> None:
    executable = binary.resolve(strict=True)
    if not executable.is_file():
        raise RuntimeError("Native compiler executable missing")
    source = (ROOT / "stdlib/g14/tables.kasa").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "tests/g14_table_cases.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != 1 or len(manifest["cases"]) != 10:
        raise ValueError("Unexpected table fixture manifest")
    with tempfile.TemporaryDirectory(prefix="kasa-g14-data-") as folder:
        work = Path(folder)
        for test in manifest["cases"]:
            name = test["id"]
            combined = source + "\n" + test["source"]
            out = io.StringIO()
            Interpreter(stdout=out).run(parse(combined))
            if out.getvalue() != test["output"]:
                raise AssertionError(name + ": Python reference output mismatch")
            kasa_file = work / (name + ".kasa")
            kbc = work / (name + ".kbc")
            kasa_file.write_text(combined, encoding="utf-8", newline="\n")
            invoke(executable, "check", str(kasa_file))
            if invoke(executable, "run", str(kasa_file)) != test["output"]:
                raise AssertionError(name + ": C++ runtime output mismatch")
            invoke(executable, "compile", str(kasa_file), "-o", str(kbc))
            if not kbc.read_bytes().startswith(b"KBC1"):
                raise AssertionError(name + ": native compiler did not produce KBC1")
            invoke(executable, "check-bytecode", str(kbc))
            kasa_file.unlink()
            if invoke(executable, "run-bytecode", str(kbc)) != test["output"]:
                raise AssertionError(name + ": independent KBC1 output mismatch")
            print("PASS G1.4 table Python/native/KBC1 " + name, flush=True)
    print(f"PASS G1.4: {len(manifest['cases'])} table contract cases in native/KBC1")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    arguments = parser.parse_args(argv)
    try:
        verify(arguments.native)
    except (AssertionError, ValueError, RuntimeError, OSError,
            subprocess.TimeoutExpired) as error:
        print("FAIL G1.4 table native gate: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
