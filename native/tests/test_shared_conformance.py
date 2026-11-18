"""Run shared language fixtures against the standalone C++ binary."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BIN = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT / 'build/kasa-native'
sys.argv=sys.argv[:1]
FIXTURES=json.loads((ROOT/'tests/conformance/cases.json').read_text(encoding='utf-8'))


class SharedConformance(unittest.TestCase):
    def run_kasa(self, source, input=''):
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/'test.kasa'
            file.write_text(source, encoding='utf-8')
            return subprocess.run([str(BIN),'run',str(file)], input=input,
                                  capture_output=True,text=True,timeout=6)

    def test_success_cases(self):
        for case in FIXTURES['success']:
            with self.subTest(case=case['id']):
                r=self.run_kasa(case['source'],case.get('input',''))
                self.assertEqual(r.returncode,0,r.stderr)
                self.assertEqual(r.stdout,case['output'])

    def test_error_categories(self):
        for case in FIXTURES['failures']:
            with self.subTest(case=case['id']):
                r=self.run_kasa(case['source'])
                self.assertEqual(r.returncode,1,r.stdout)
                self.assertIn(': '+case['error']+':',r.stderr)


if __name__=='__main__':
    unittest.main(verbosity=2)
