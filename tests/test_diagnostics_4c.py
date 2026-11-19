"""Phase 4C.2 — shared diagnostic categories against Python reference interpreter."""
from __future__ import annotations
import io
import json
from pathlib import Path
import pytest
from kasa import Interpreter, KasaError, parse

CORPUS = json.loads((Path(__file__).with_name("conformance_diagnostics_4c.json")).read_text(encoding="utf-8"))

@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda item: item["name"])
def test_python_diagnostic_category(case: dict) -> None:
    with pytest.raises(KasaError) as exc:
        Interpreter(stdout=io.StringIO(),stdin=io.StringIO("")).run(parse(case["source"]))
    assert exc.value.category == case["error_category"]
    assert exc.value.token.line >= 1
    assert exc.value.token.column >= 1

def test_unique_versioned_diagnostic_cases() -> None:
    assert CORPUS["schema_version"] == 1
    assert len(CORPUS["cases"]) >= 9
    assert len({c["name"] for c in CORPUS["cases"]}) == len(CORPUS["cases"])
