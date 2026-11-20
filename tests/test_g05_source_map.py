"""G0.5 source-map checks: statement origins are exact; columns are not."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from link_kasa_modules_hygienic import link_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def test_original_app_locations_survive_generated_source():
    program = (
        "fa math firi stdlib: m\n"
        "ka m.kasa_abs(-2)\n"
        "ka m.kasa_sum([10, 20])\n"
    )
    mapping = {}
    linked = link_source(program, filename="app.kasa", source_map=mapping)
    assert mapping["schema_version"] == 1
    assert mapping["precision"] == "statement_only"
    assert mapping["generated_sha256"] == hashlib.sha256(linked.encode()).hexdigest()
    assert len(mapping["lines"]) == len(linked.splitlines())
    source_lines = [item for item in mapping["lines"] if item["file"] == "app.kasa"]
    assert [(item["line"], item["column"], item["kind"]) for item in source_lines] == [
        (2, 1, "print"), (3, 1, "print")
    ]
    for item in mapping["lines"]:
        assert item["generated_line"] >= 1
    lib_lines = [item for item in mapping["lines"] if item["file"].endswith("math.kasa")]
    assert lib_lines and any(item["kind"] == "function" for item in lib_lines)


def test_nested_application_statements_get_separate_origins():
    code = (
        "fa math firi stdlib: m\n"
        "dwumadie sample(x)\n"
        "    sɛ x > 0 a\n"
        "        sanma m.kasa_abs(-x)\n"
        "    awiei\n"
        "    sanma 0\n"
        "awiei\n"
        "ka sample(3)\n"
    )
    mapping = {}
    linked = link_source(code, filename="lesson.kasa", source_map=mapping)
    generated = linked.splitlines()
    rows = [item for item in mapping["lines"] if item["file"] == "lesson.kasa"]
    assert [(item["line"], item["kind"]) for item in rows if not item["synthetic"]] == [
        (2, "function"), (3, "if"), (4, "return"), (6, "return"), (8, "print")
    ]
    for item in mapping["lines"]:
        assert generated[item["generated_line"] - 1]
        if item["synthetic"]:
            assert item["precision"] in ("statement", "none")


def test_source_map_is_opt_in_and_does_not_change_generated_bytes():
    code = "fa math firi stdlib: m\nka m.kasa_sum([1, 2])\n"
    plain = link_source(code)
    mapping = {"old": "stale"}
    with_map = link_source(code, filename="demo.kasa", source_map=mapping)
    assert plain == with_map
    assert "old" not in mapping
    assert mapping["lines"][-1]["file"] == "demo.kasa"


def test_synthetic_separator_is_marked_not_a_real_source_line():
    code = "fa math firi stdlib: m\nka 1\n"
    mapping = {}
    link_source(code, source_map=mapping)
    separators = [item for item in mapping["lines"] if item["kind"] == "separator"]
    assert separators and all(item["precision"] == "none" and item["synthetic"] for item in separators)
