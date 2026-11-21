"""G1 source-fragment parity against native source execution and independent KBC1.

Usage: python native/tests/g1_foundation_conformance.py build/kasa-local/Release/kasa-native.exe
Does not use G0.5 native import compilation, alter catalog hashes, or install binaries.
"""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/conformance_g1_foundation.json").read_text(encoding="utf-8"))


def invoke(native: Path, *args: str):
    return subprocess.run(
        [str(native), *args], capture_output=True, timeout=30,
        check=False,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: g1_foundation_conformance.py path/to/kasa-native[.exe]", file=sys.stderr)
        return 2
    native = Path(sys.argv[1]).resolve()
    if not native.is_file():
        print("Missing native executable:", native, file=sys.stderr)
        return 2
    if CASES["schema_version"] != 1:
        print("Unsupported fixture schema", file=sys.stderr)
        return 2
    libraries = "\n".join(
        (ROOT / name).read_text(encoding="utf-8") for name in CASES["libraries"]
    )
    with tempfile.TemporaryDirectory(prefix="kasa-g1-source-kbc1-") as tmp:
        folder = Path(tmp)
        for index, case in enumerate(CASES["cases"]):
            source = folder / f"g1_{index}.kasa"
            compiled = folder / f"g1_{index}.kbc"
            source.write_text(libraries + "\n" + case["source"] + "\n", encoding="utf-8")
            stages = [
                ("run", "run", [str(source)]),
                ("compile", "compile", [str(source), "-o", str(compiled)]),
                ("check-bytecode", "check-bytecode", [str(compiled)]),
                ("run-bytecode", "run-bytecode", [str(compiled)]),
            ]
            for label, command, args in stages:
                result = invoke(native, command, *args)
                if result.returncode != 0 or result.stderr:
                    print("FAIL", case["name"], label, "code", result.returncode,
                          result.stderr.decode("utf-8", "replace"))
                    return 1
                if label in ("run", "run-bytecode"):
                    actual = result.stdout.decode("utf-8", "replace")
                    if actual != case["expected_stdout"]:
                        print("FAIL", case["name"], label,
                              "expected", repr(case["expected_stdout"]),
                              "actual", repr(actual))
                        return 1
            print("PASS native G1", case["name"])
    print(f"PASS native source + standalone KBC1: {len(CASES['cases'])} G1 cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
