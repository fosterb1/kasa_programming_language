"""Cross-platform byte-for-byte KBC1/KBC2 golden fixture verifier.

Use a fixed manifest committed from an independently tested Linux compiler.
The verifier NEVER updates the manifest. --emit-candidates prints diagnostics
for preparing/reviewing a separate manifest update.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "conformance_arbitrary_integers.json"
MANIFEST = ROOT / "tests" / "kbc2_golden_sha256.json"


def checked(cmd: list[str]) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(cmd, capture_output=True, timeout=20, check=False)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd[1]}: "
                           f"{result.stderr.decode('utf-8', 'replace')[:500]}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, default=MANIFEST)
    parser.add_argument("--emit-candidates", action="store_true",
                        help="Print computed hashes, never overwrite manifest")
    args = parser.parse_args()
    binary = str(args.binary.resolve())
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]
    # Filename-independent serialization is required: identical sources,
    # independent directories and OSes must produce identical archives.
    expected = {} if args.emit_candidates else json.loads(
        args.manifest.read_text(encoding="utf-8"))["cases"]
    computed: dict[str, dict[str, object]] = {}
    for item in fixtures:
        name = item["name"]
        with tempfile.TemporaryDirectory(prefix="kasa-kbc2-golden-") as folder:
            source = pathlib.Path(folder) / "example.kasa"
            archive = pathlib.Path(folder) / "example.kbc"
            source.write_bytes(item["source"].encode("utf-8"))
            checked([binary, "compile-kbc2", str(source), "-o", str(archive)])
            data = archive.read_bytes()
            if data[:6] != b"KBC2\\x02\\x00":
                raise AssertionError(f"{name}: missing KBC2 v2 header")
            # Verify independent load and execution, not just a hash.
            checked([binary, "check-bytecode", str(archive)])
            output = checked([binary, "run-bytecode", str(archive)]).stdout
            if output != item["expected_stdout"].encode("utf-8"):
                raise AssertionError(f"{name}: incorrect bytecode result")
            computed[name] = {"sha256": hashlib.sha256(data).hexdigest(),
                              "bytes": len(data)}
            if not args.emit_candidates and computed[name] != expected.get(name):
                raise AssertionError(
                    f"{name}: bytecode differs: observed={computed[name]} "
                    f"expected={expected.get(name)}")
            if not args.emit_candidates:
                print(f"PASS {name}: {len(data)} bytes")
    if args.emit_candidates:
        print(json.dumps({"schema_version": 1, "format": "KBC2",
                          "cases": computed}, indent=2))
    elif set(expected) != set(computed):
        raise AssertionError("Golden manifest case list differs from RFC-0008 fixtures")
    else:
        print(f"PASS: {len(computed)}/{len(fixtures)} byte-for-byte KBC2 fixtures match")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, AssertionError, OSError, ValueError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
