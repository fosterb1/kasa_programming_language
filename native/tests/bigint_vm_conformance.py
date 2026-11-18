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

    def test_kbc2_roundtrips_all_rfc0008_cases(self):
        for case in CASES:
            with self.subTest(name=case["name"]), tempfile.TemporaryDirectory() as directory:
                source = pathlib.Path(directory) / "program.kasa"
                output = pathlib.Path(directory) / "program.kbc"
                source.write_bytes(case["source"].encode("utf-8"))
                result = run(["compile-kbc2", str(source), "-o", str(output)])
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                archive = output.read_bytes()
                self.assertEqual(archive[:6], b"KBC2\\x02\\x00")
                checked = run(["check-bytecode", str(output)])
                self.assertEqual(checked.returncode, 0, checked.stderr)
                executed = run(["run-bytecode", str(output)])
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout.decode("utf-8"), case["expected_stdout"])

    def test_kbc1_cannot_encode_large_literal_but_kbc2_can(self):
        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "program.kasa"
            output = pathlib.Path(directory) / "program.kbc"
            source.write_bytes(b"ka 18446744073709551616\\n")
            self.assertNotEqual(run(["compile", str(source), "-o", str(output)]).returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(run(["compile-kbc2", str(source), "-o", str(output)]).returncode, 0)
            self.assertEqual(run(["run-bytecode", str(output)]).stdout,
                             b"18446744073709551616\\n")

    def test_kbc2_rejects_corrupt_bigint_and_version_magic(self):
        import binascii

        with tempfile.TemporaryDirectory() as directory:
            source = pathlib.Path(directory) / "program.kasa"
            original = pathlib.Path(directory) / "original.kbc"
            changed = pathlib.Path(directory) / "changed.kbc"
            source.write_bytes(b"ka 18446744073709551616\\n")
            self.assertEqual(run(["compile-kbc2", str(source), "-o", str(original)]).returncode, 0)
            base = bytearray(original.read_bytes())
            # KBC1 and KBC2 share a 16-byte header and CRC32 payload checksum.
            # Bigint tag 5 follows the instruction header, location, numeric
            # operand, empty name and is followed by sign and BE length.
            tag = bytes((5, 1, 0, 9, 1))
            location = base.find(tag, 16)
            self.assertGreaterEqual(location, 16)
            def rejected(modify):
                data = bytearray(base)
                modify(data)
                # Recalculate checksum so structural validation is exercised.
                data[12:16] = (binascii.crc32(data[16:]) & 0xffffffff).to_bytes(4, "little")
                changed.write_bytes(data)
                result = run(["check-bytecode", str(changed)])
                self.assertNotEqual(result.returncode, 0, result.stderr)

            rejected(lambda data: data.__setitem__(location+1, 0))  # sign 0
            rejected(lambda data: data.__setitem__(location+4, 0))  # leading zero
            rejected(lambda data: data.__setitem__(location+3, 0))  # length 0
            rejected(lambda data: data.__setitem__(location, 255)) # unknown value tag
            rejected(lambda data: data.__setitem__(4, 1))         # wrong header version
            rejected(lambda data: data.__setitem__(3, ord('1')))  # KBC1 magic / v2 mismatch

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
