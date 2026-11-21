#!/usr/bin/env python3
"""G1.3 small reproducible Python/JS/native/KBC1 differential.

Runs all shared G1 source fixtures in Python and Node, then positive
fixtures in ordinary-source native and KBC1. Negative preflight cases
must fail before any output; native never receives invalid imported source.
No production safety, native module loader or Chromium claims.
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
sys.path.insert(0, str(ROOT / "scripts"))

from kasa import Interpreter, parse
from kasa.core import KasaError
from link_kasa_modules_hygienic import HygienicLinkError, link_source
from run_kasa_modules_experimental import execute_module_source

NATIVE = ROOT / "build/kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)
FIXTURES = ROOT / "tests/g13_cross_runtime_cases.json"


def command(argv: list[str], *, timeout: int = 60) -> str:
    run = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=timeout, check=False)
    if run.returncode or run.stderr:
        raise AssertionError(
            f"Command failure {argv[0]!r}: exit={run.returncode}, "
            f"stderr={run.stderr!r}, stdout={run.stdout!r}"
        )
    return run.stdout


def verify(native_path: Path) -> None:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    cases = data["cases"]
    assert cases and len({x["id"] for x in cases}) == len(cases)
    assert all(("output" in x) != ("reject" in x) for x in cases)
    js_text = command(["node", str(ROOT / "tests/g13_js_fixture_runner.cjs")])
    js = json.loads(js_text)
    assert js["schema_version"] == 1 and js["engine"] == "javascript_g1"
    rows = js["results"]
    assert [x["id"] for x in rows] == [x["id"] for x in cases]
    for item in rows:
        if not item["pass"]:
            raise AssertionError("JS mismatch: " + repr(item))

    native = native_path.resolve(strict=True)
    if not native.is_file():
        raise AssertionError("Native executable is not a file")

    with tempfile.TemporaryDirectory(prefix="kasa-g13-conformance-") as folder:
        temp = Path(folder)
        positive = negative = 0
        for item in cases:
            name = item["id"]
            source = item["source"]
            imported = io.StringIO()
            if "reject" in item:
                for runner in (
                    lambda: execute_module_source(source, stdout=imported, generation="g1"),
                    lambda: link_source(source, generation="g1"),
                ):
                    try:
                        runner()
                    except (KasaError, HygienicLinkError, ValueError) as error:
                        if item["reject"].lower() not in str(error).lower():
                            raise AssertionError(f"{name}: unexpected diagnostic: {error}") from error
                    else:
                        raise AssertionError(f"{name}: invalid source was accepted")
                if imported.getvalue():
                    raise AssertionError(f"{name}: invalid source produced Python output")
                negative += 1
                print("PASS G1 cross-runtime rejected " + name, flush=True)
                continue

            execute_module_source(source, stdout=imported, generation="g1")
            if imported.getvalue() != item["output"]:
                raise AssertionError(f"{name}: Python import output mismatch")
            linked = link_source(source, generation="g1")
            flattened = io.StringIO()
            Interpreter(stdout=flattened).run(parse(linked))
            if flattened.getvalue() != item["output"]:
                raise AssertionError(f"{name}: Python linked output mismatch")

            path = temp / (name + ".kasa")
            kbc = temp / (name + ".kbc")
            path.write_text(linked, encoding="utf-8", newline="\n")
            command([str(native), "check", str(path)])
            if command([str(native), "run", str(path)]) != item["output"]:
                raise AssertionError(f"{name}: native source result mismatch")
            command([str(native), "compile", str(path), "-o", str(kbc)])
            if not kbc.read_bytes().startswith(b"KBC1"):
                raise AssertionError(f"{name}: expected KBC1")
            command([str(native), "check-bytecode", str(kbc)])
            path.unlink()
            if command([str(native), "run-bytecode", str(kbc)]) != item["output"]:
                raise AssertionError(f"{name}: independent KBC1 result mismatch")
            positive += 1
            print("PASS G1 Python + JS + native + KBC1 " + name, flush=True)
    print(f"PASS G1.3 shared corpus: {positive} executable and {negative} invalid-source cases")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    args = parser.parse_args(argv)
    try:
        verify(args.native)
    except (AssertionError, OSError, ValueError, KasaError, HygienicLinkError,
            subprocess.TimeoutExpired) as error:
        print("FAIL G1.3 cross-runtime conformance: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
