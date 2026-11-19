"""Phase 8: compare native source and KBC1 results to the shared pesewa corpus.

Usage: python native/tests/finance_subunits_conformance.py build/kasa-local/Release/kasa-native.exe
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = json.loads((ROOT / "tests/conformance_finance_subunits.json").read_text(encoding="utf-8"))["cases"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: finance_subunits_conformance.py PATH_TO_KASA_NATIVE", file=sys.stderr)
        return 2
    binary = Path(sys.argv[1]).resolve()
    if not binary.is_file():
        print("Missing native Kasa binary:", binary, file=sys.stderr)
        return 2
    passed = 0
    with tempfile.TemporaryDirectory(prefix="kasa-finance-fixtures-") as folder:
        tmp = Path(folder)
        for case in FIXTURES:
            source = tmp / (case["name"] + ".kasa")
            bytecode = tmp / (case["name"] + ".kbc")
            source.write_bytes(case["source"].encode("utf-8"))
            for command in (["run", str(source)],
                            ["compile", str(source), "-o", str(bytecode)],
                            ["check-bytecode", str(bytecode)],
                            ["run-bytecode", str(bytecode)]):
                result = subprocess.run([str(binary), *command], capture_output=True, timeout=10)
                if result.returncode != 0:
                    print("FAIL", case["name"], command[0], result.stderr.decode("utf-8", "replace"))
                    return 1
                if command[0] in ("run", "run-bytecode"):
                    actual = result.stdout.decode("utf-8", "replace")
                    if actual != case["expected_stdout"]:
                        print("FAIL", case["name"], command[0], repr(actual))
                        return 1
            passed += 1
    print(f"PASS: {passed}/{len(FIXTURES)} finance-subunit programs matched native source and KBC1 output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
