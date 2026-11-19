"""Phase 8 exact-pesewa teaching program regression corpus (no new Kasa builtins)."""
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, parse

CORPUS = json.loads((Path(__file__).parent / "conformance_finance_subunits.json").read_text(encoding="utf-8"))
assert CORPUS["units_per_major"] == 100

@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda c: c["name"])
def test_finance_pesewas_python(case):
    stdout = io.StringIO()
    Interpreter(stdout=stdout).run(parse(case["source"]))
    assert stdout.getvalue() == case["expected_stdout"]
