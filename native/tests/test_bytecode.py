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

    def test_missing_file(self):
        missing=self.folder/'missing.kbc'
        p=self.command('run-bytecode',missing)
        self.assertEqual(p.returncode,1)
        self.assertIn('Cannot open bytecode file',p.stderr)


if __name__=='__main__':
    unittest.main(verbosity=2)
