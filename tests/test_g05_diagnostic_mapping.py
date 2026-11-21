"""G0.5 mapped diagnostic annotations: fail closed on tampering and ambiguity."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from annotate_g05_diagnostic import SourceMapError, annotate
    from link_kasa_modules_hygienic import link_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def sample():
    mapping = {}
    linked = link_source(
        "fa math firi stdlib: m\nka 1 / 0\n",
        filename="market.kasa", source_map=mapping,
    )
    mapped_row = next(row for row in mapping["lines"] if row["file"] == "market.kasa")
    return linked, mapping, mapped_row["generated_line"]


def test_annotates_exact_generated_path_but_not_fake_column():
    linked, mapping, line = sample()
    native = f"C:\\temp\\linked.kasa:{line}:9: ZeroDivisionError: division by zero"
    annotated = annotate(native, "C:\\temp\\linked.kasa", linked, mapping)
    assert annotated.startswith(native + "\n")
    assert "Kasa source statement: market.kasa:2:1" in annotated
    assert "expression column not mapped" in annotated


def test_other_filename_is_never_rewritten():
    linked, mapping, line = sample()
    native = f"other.kasa:{line}:3: ZeroDivisionError: division by zero"
    assert annotate(native, "linked.kasa", linked, mapping) == native


def test_bad_generated_hash_is_rejected():
    linked, mapping, line = sample()
    with pytest.raises(SourceMapError, match="hash"):
        annotate(f"linked.kasa:{line}:1: NameError: x", "linked.kasa",
                 linked + "# tampered\n", mapping)


def test_malformed_line_map_is_rejected():
    linked, mapping, line = sample()
    mapping["lines"].pop()
    with pytest.raises(SourceMapError, match="line count"):
        annotate(f"linked.kasa:{line}:1: NameError: x", "linked.kasa",
                 linked, mapping)


def test_synthetic_lines_cannot_be_attributed_to_real_source():
    linked, mapping, _ = sample()
    synthetic = next(row for row in mapping["lines"] if row["synthetic"])
    raw = f"linked.kasa:{synthetic['generated_line']}:1: RuntimeError: generated"
    assert annotate(raw, "linked.kasa", linked, mapping) == raw
