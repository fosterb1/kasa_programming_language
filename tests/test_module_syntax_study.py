"""Contract tests for the non-executing import grammar study."""
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "scripts/study_kasa_module_syntax.py"
SPEC = importlib.util.spec_from_file_location("module_syntax_study", PATH)
study = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = study
SPEC.loader.exec_module(study)


def test_two_aliases_and_static_exports():
    declarations = study.parse_declarations(
        "# trial only\nmodule math alias m\nmodule collections alias c\n"
    )
    assert [d.line for d in declarations] == [2, 3]
    assert study.check_access(
        declarations,
        study.parse_export_access("m.kasa_sum"),
        {"math": ["kasa_sum"], "collections": ["kasa_contains"]},
    ) == "math"


@pytest.mark.parametrize("source, message", [
    ("", "No module"),
    ("module math alias m\nmodule collections alias m", "duplicate alias"),
    ("module math alias m\nmodule math alias n", "duplicate module"),
    ("module math alias ka", "reserved alias"),
    ("module ../math alias m", "invalid"),
    ("module math alias m\nka 1", "invalid"),
    ("module math alias 9m", "invalid"),
])
def test_invalid_declarations(source, message):
    with pytest.raises(study.ModuleSyntaxStudyError, match=message):
        study.parse_declarations(source)


@pytest.mark.parametrize("source", [
    "m", "m.", ".kasa_sum", "m.secret()", "m.kasa_sum.extra",
    "m[0]", "m.__class__()", " m.kasa_sum",
])
def test_invalid_member_expression(source):
    with pytest.raises(study.ModuleSyntaxStudyError, match="Expected"):
        study.parse_export_access(source)


def test_missing_export_and_unknown_alias_fail():
    decl = study.parse_declarations("module math alias m")
    with pytest.raises(study.ModuleSyntaxStudyError, match="does not export"):
        study.check_access(decl, study.parse_export_access("m.private"), {"math": ["public"]})
    with pytest.raises(study.ModuleSyntaxStudyError, match="Unknown module alias"):
        study.check_access(decl, study.parse_export_access("c.public"), {"math": ["public"]})


def test_does_not_change_core_language_parser():
    from kasa import parse
    from kasa.core import KasaError
    with pytest.raises(KasaError):
        parse("module math alias m\nka m.kasa_sum([1])")
