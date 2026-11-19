"""Cross-runtime experiment for concatenated standard-library Kasa source fragments.

Usage: python native/tests/stdlib_foundation_conformance.py path/to/kasa-native[.exe]
Tests native source and KBC1 round trip, no installation or IO from Kasa source.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CORPUS = json.loads((ROOT / "tests/conformance_stdlib_foundation.json").read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: stdlib_foundation_conformance.py path/to/kasa-native", file=sys.stderr)
        return 2
    native = Path(sys.argv[1]).resolve()
    if not native.is_file():
        print("Native binary not found:", native, file=sys.stderr)
        return 2
    library_source = "\n".join((ROOT / name).read_text(encoding="utf-8") for name in CORPUS["libraries"])
    count = 0
    with tempfile.TemporaryDirectory(prefix="kasa-stdlib-") as folder:
        temp = Path(folder)
        for fixture in CORPUS["cases"]:
            source = temp / (fixture["name"] + ".kasa")
            bytecode = temp / (fixture["name"] + ".kbc")
            source.write_bytes((library_source + "\n" + fixture["source"] + "\n").encode("utf-8"))
            checks = [
                ("run", ["run", str(source)]),
                ("compile", ["compile", str(source), "-o", str(bytecode)]),
                ("check-bytecode", ["check-bytecode", str(bytecode)]),
                ("run-bytecode", ["run-bytecode", str(bytecode)]),
            ]
            for mode, argv in checks:
                result = subprocess.run([str(native), *argv], capture_output=True, timeout=10, check=False)
                if result.returncode:
                    print(f"FAIL {fixture['name']} {mode}: {result.stderr.decode('utf-8', 'replace')}")
                    return 1
                if mode in ("run", "run-bytecode") and result.stdout.decode("utf-8", "replace") != fixture["expected_stdout"]:
                    print(f"FAIL {fixture['name']} {mode}: wrong output {result.stdout!r}")
                    return 1
            count += 1
    print(f"PASS: {count}/{len(CORPUS['cases'])} experimental stdlib programs in native source and KBC1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
