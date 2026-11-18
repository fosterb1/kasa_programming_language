"""Experimental RFC-0008 native source and compatible KBC1 execution tests.

Requires a native binary configured with KASA_ENABLE_BIGINT_VM=ON.
Big integer constants are intentionally NOT serialized in KBC1.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BINARY = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build" / "kasa-bigvm" / "kasa-native"
sys.argv = sys.argv[:1]
CASES = json.loads((ROOT / "tests" / "conformance_arbitrary_integers.json").read_text(encoding="utf-8"))["cases"]


def run(argv: list[str], *, source: str = "") -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([str(BINARY), *argv], input=source.encode("utf-8"),
                          capture_output=True, check=False, timeout=12)


class BigIntegerNativeExperiment(unittest.TestCase):
    def test_all_ten_rfc0008_source_programs(self):
        for case in CASES:
            with self.subTest(name=case["name"]), tempfile.TemporaryDirectory() as directory:
                path = pathlib.Path(directory) / "program.kasa"
                path.write_bytes(case["source"].encode("utf-8"))
                result = run(["run", str(path)])
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                self.assertEqual(result.stdout.decode("utf-8"), case["expected_stdout"])

    def test_kbc1_stays_readable_and_runtime_promotion_works(self):
        # KBC1 uses int64 constants. Running its arithmetic instructions in
        # the opt-in VM may nevertheless promote intermediate values safely.
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "program.kasa"
            output = pathlib.Path(directory) / "program.kbc"
            source.write_bytes(b"ka 9223372036854775807 + 1\n")
            result = run(["compile", str(source), "-o", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run(["check-bytecode", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            result = run(["run-bytecode", str(output)])
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, b"9223372036854775808\n")

    def test_out_of_range_constant_is_not_silently_serialized_as_kbc1(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "program.kasa"
            output = pathlib.Path(directory) / "program.kbc"
            source.write_bytes(b"ka 18446744073709551616\n")
            result = run(["compile", str(source), "-o", str(output)])
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse(output.exists())

    def test_resource_limit_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "program.kasa"
            source.write_bytes(("ma x = 2\nmpɛn 16400\nma x = x * 2\nawiei\nka x\n").encode())
            # The VM's normal instruction budget can expire first; the
            # explicit size check must trigger before that budget for this loop.
            result = run(["run", str(source)])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"ResourceError:", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
