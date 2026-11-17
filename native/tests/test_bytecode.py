"""KBC1 round-trips and adversarial loader checks; no execution of unverified bytes."""
from __future__ import annotations

import pathlib
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
BIN = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT / 'build/kasa-native'
sys.argv = sys.argv[:1]


class BytecodeCases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = pathlib.Path(self.tmp.name)

    def command(self, *argv, input=''):
        return subprocess.run([str(BIN), *map(str, argv)], input=input,
                              capture_output=True, text=True, timeout=5)

    def compile(self, program):
        src = self.folder/'program.kasa'
        src.write_text(program, encoding='utf-8')
        kbc = self.folder/'program.kbc'
        p = self.command('compile', src, '-o', kbc)
        self.assertEqual(p.returncode, 0, p.stderr)
        return src, kbc

    def expect_invalid(self, kbc, contents, diagnostic):
        kbc.write_bytes(contents)
        for cmd in ('check-bytecode', 'run-bytecode', 'disasm-bytecode'):
            with self.subTest(cmd=cmd):
                result = self.command(cmd, kbc)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('Invalid KBC bytecode:', result.stderr)
                self.assertIn(diagnostic, result.stderr)
                self.assertEqual(result.stdout, '')

    @staticmethod
    def checksum(contents):
        return contents[:12] + struct.pack('<I', zlib.crc32(contents[16:])) + contents[16:]

    def test_all_bundled_examples_roundtrip(self):
        for path in sorted([* (ROOT/'examples').glob('*.kasa'), *(ROOT/'native/examples').glob('*.kasa')]):
            with self.subTest(filename=path.name):
                source=path.read_text(encoding='utf-8')
                _, kbc=self.compile(source)
                self.assertEqual(self.command('check-bytecode', kbc).returncode, 0)
                run_compiled=self.command('run-bytecode', kbc)
                run_source=self.command('run', ROOT/path.relative_to(ROOT))
                self.assertEqual(run_compiled.returncode, 0, run_compiled.stderr)
                self.assertEqual(run_compiled.stdout, run_source.stdout)
                disasm=self.command('disasm-bytecode', kbc)
                self.assertIn('CONST', disasm.stdout)

    def test_bytecode_can_accept_input(self):
        _, kbc=self.compile('ka "Hello " + bisa()')
        self.assertEqual(self.command('run-bytecode', kbc, input='Esi\n').stdout, 'Hello Esi\n')

    def test_wrong_magic_and_version(self):
        _, kbc=self.compile('ka 42')
        original=kbc.read_bytes()
        self.expect_invalid(kbc, b'ABCD'+original[4:], 'wrong magic')
        self.expect_invalid(kbc, original[:4]+b'\x02\x00'+original[6:], 'unsupported version')

    def test_integrity_and_truncation(self):
        _, kbc=self.compile('ka 42')
        original=kbc.read_bytes()
        damaged=bytearray(original);damaged[-1]^=1
        self.expect_invalid(kbc,bytes(damaged),'checksum mismatch')
        self.expect_invalid(kbc,original[:-2],'payload length mismatch')

    def test_bad_opcode_with_valid_checksum(self):
        _, kbc=self.compile('ka 42')
        b=bytearray(kbc.read_bytes())
        # 16-byte header + 4-byte chunk instruction count = first opcode.
        b[20]=255
        self.expect_invalid(kbc,self.checksum(b),'invalid opcode')

    def test_stack_underflow_with_valid_checksum(self):
        _, kbc=self.compile('ka 42')
        b=bytearray(kbc.read_bytes())
        b[47]=7  # Change second PRINT into ADD; only one operand exists.
        self.expect_invalid(kbc,self.checksum(b),'operand stack underflow')

    def test_invalid_jump_with_valid_checksum(self):
        _, kbc=self.compile('ka 42')
        b=bytearray(kbc.read_bytes())
        b[20]=19  # Jump opcode, followed by the instruction's number offset.
        b[29:33]=struct.pack('<i',9999)  # 20 opcode, 21..28 source location, 29..32 integer.
        self.expect_invalid(kbc,self.checksum(b),'jump target outside chunk')

    def test_deterministic_bytecode(self):
        source=self.folder/'stable.kasa'
        source.write_text('ka 42\nka "Ghana"', encoding='utf-8')
        left=self.folder/'one.kbc'
        right=self.folder/'two.kbc'
        self.assertEqual(self.command('compile', source, '-o', left).returncode, 0)
        self.assertEqual(self.command('compile', source, '-o', right).returncode, 0)
        self.assertEqual(left.read_bytes(), right.read_bytes())

    def test_source_file_cannot_be_overwritten_via_alias(self):
        source=self.folder/'important.kasa'
        text='ka "Do not overwrite"\n'
        source.write_text(text, encoding='utf-8')
        # A differently spelled path resolving to the same file is not safe.
        alias=self.folder/'.'/'important.kasa'
        result=self.command('compile', source, '-o', alias)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Refusing to overwrite source file', result.stderr)
        self.assertEqual(source.read_text(encoding='utf-8'), text)

    def test_nonzero_reserved_flags_rejected(self):
        _, kbc=self.compile('ka 42')
        original=kbc.read_bytes()
        tampered=original[:6] + b'\\x01\\x00' + original[8:]
        self.expect_invalid(kbc, tampered, 'unsupported flags')

    def test_large_archive_rejected_before_execution(self):
        _, kbc=self.compile('ka 42')
        oversized=b'KBC1' + bytes(8_000_020)
        self.expect_invalid(kbc, oversized, 'file length exceeds limits')

    def test_reject_invalid_boolean_with_recomputed_checksum(self):
        _, kbc=self.compile('ka nokware')
        raw=bytearray(kbc.read_bytes())
        # First chunk begins at 16, first instruction opcode at 20.
        # The tagged Boolean constant is after its fixed fields and empty name.
        # Find the marker for tag 4, Boolean 1 within that first instruction.
        first=raw.find(b'\\x04\\x01', 20)
        self.assertGreater(first, 20, 'Expected serialized Boolean literal')
        raw[first + 1]=2
        self.expect_invalid(kbc,self.checksum(raw),'invalid Boolean constant')

    def test_missing_file(self):
        missing=self.folder/'missing.kbc'
        p=self.command('run-bytecode',missing)
        self.assertEqual(p.returncode,1)
        self.assertIn('Cannot open bytecode file',p.stderr)


if __name__=='__main__':
    unittest.main(verbosity=2)
