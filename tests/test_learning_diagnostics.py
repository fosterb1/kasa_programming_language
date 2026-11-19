"""Python-only experimental Twi-first diagnostic teaching cards."""
import sys
from pathlib import Path

from kasa.core import KasaError, Token
from kasa.learning_diagnostics import learning_hint

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playground"))
try:
    from runner import execute_kasa
finally:
    sys.path.remove(str(ROOT / "playground"))


def test_default_playground_error_contract_unchanged():
    result = execute_kasa("ka 1 / 0")
    assert not result["ok"]
    assert "ZeroDivisionError" in result["error"]
    assert "playground.kasa:1:" in result["error"]
    assert "learning_hint" not in result


def test_opt_in_returns_draft_hint_without_changing_location():
    standard = execute_kasa("ka 1 / 0")
    localized = execute_kasa("ka 1 / 0", learner_language="tw")
    assert localized["error"] == standard["error"]
    hint = localized["learning_hint"]
    assert hint["technical_code"] == "ZeroDivisionError"
    assert hint["status"] == "draft_needs_human_review"
    assert hint["language"] == "tw"
    assert "zero" in hint["guidance_en"].lower()


def test_opt_in_name_error_and_syntax_check():
    result = execute_kasa("ka not_defined", learner_language="tw")
    assert result["learning_hint"]["technical_code"] == "NameError"
    checked = execute_kasa("ka (", mode="check", learner_language="tw")
    assert checked["learning_hint"]["technical_code"] == "SyntaxError"


def test_success_and_resource_failure_dont_invent_hints():
    success = execute_kasa('ka "Maakye, Ghana!"', learner_language="tw")
    assert success["ok"] and "learning_hint" not in success
    limit = execute_kasa("#" * 50_001, learner_language="tw")
    assert not limit["ok"]
    assert "learning_hint" not in limit


def test_unknown_error_category_not_misclassified():
    error = KasaError("MadeUpError", "type text is not the category", Token("NAME", "x", 1, 1), "x.kasa")
    assert learning_hint(error) is None


def test_unknown_language_is_rejected_without_execution():
    result = execute_kasa("ka 1", learner_language="not-a-language")
    assert result["ok"] is False
    assert result["output"] == ""
    assert result["error"] == "Unsupported learner language"
