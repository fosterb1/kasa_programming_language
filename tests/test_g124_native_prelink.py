"""G1.2.4: opt-in G1 prelink tests; no changes to normal Kasa or G0 defaults."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from kasa import Interpreter, parse
from kasa.core import KasaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from link_kasa_modules_hygienic import HygienicLinkError, link_source
    from preflight_native_modules import preflight
    from run_kasa_modules_experimental import execute_module_source
    from validate_g1_catalog import G1CatalogError
finally:
    sys.path.remove(str(ROOT / "scripts"))


CASES = [
    ("arithmetic", "fa math firi stdlib: m\n"
     "ka m.kasa_total([40, 60, 80, 90])\n"
     "ka m.kasa_average_or([40, 60, 80, 90], 0)\n", "270\n67.5\n"),
    ("distinct", "fa collections firi stdlib: c\n"
     "ka c.kasa_count_distinct([4, 4, 9, 2, 9])\n"
     "ka c.kasa_all_equal([7, 7, 8])\n", "3\natoro\n"),
    ("search", "fa collections firi stdlib: c\n"
     "ka c.kasa_first_index([4, 8, 4], 4)\n"
     "ka c.kasa_last_index([4, 8, 4], 4)\n", "0\n2\n"),
    ("threshold", "fa math firi stdlib: m\n"
     "ka m.kasa_count_above([10, 20, 20, 30], 20)\n"
     "ka m.kasa_min_or([], -1)\n"
     "ka m.kasa_max_or([5, -4, 2], 99)\n", "1\n-1\n5\n"),
]


@pytest.mark.parametrize("case,source,expected", CASES)
def test_g1_hygienic_link_matches_reference(case, source, expected):
    plan = preflight(source, generation="g1")
    assert plan["module_generation"] == "g1"
    assert plan["capabilities_granted"] == []
    linked = link_source(source, generation="g1")
    assert "fa math" not in linked and "fa collections" not in linked
    assert "__kasa_g05_" in linked  # stable synthetic prefix; separate generation
    assert parse(linked)
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(linked))
    assert out.getvalue() == expected, case
    reference = io.StringIO()
    execute_module_source(source, stdout=reference, generation="g1")
    assert reference.getvalue() == expected, case


def test_g0_behavior_unchanged():
    source = "fa math firi stdlib: m\nka m.kasa_sum([1, 2, 3])\n"
    assert link_source(source) == link_source(source, generation="g0")
    with pytest.raises(KasaError, match="does not export"):
        preflight("fa math firi stdlib: m\nka m.kasa_total([1])\n")
    with pytest.raises(KasaError, match="does not export"):
        preflight("fa math firi stdlib: m\nka m.kasa_sum([1])\n", generation="g1")


@pytest.mark.parametrize("source,message", [
    ("fa unknown firi stdlib: x\nka 1\n", "Unknown catalog module"),
    ("fa math firi stdlib: x\nfa math firi stdlib: y\nka 1\n", "more than once"),
    ("fa math firi stdlib: x\nfa collections firi stdlib: x\nka 1\n", "alias reused"),
    ("fa math firi nowhere: m\nka 1\n", "pinned stdlib"),
    ("fa math firi stdlib: m\nka m.kasa_sum([1])\n", "does not export"),
    ("fa math firi stdlib: m\nka 1\nma m = 2\n", "cannot be reassigned"),
    ("fa math firi stdlib: m\nka 1\nfa collections firi stdlib: c\n", "precede statements"),
    ("fa math firi stdlib: m\nka m.kasa_total([1])\nka __kasa_g05_math_kasa_total([1])\n", "reserved internal"),
])
def test_bad_g1_program_rejected(source, message):
    with pytest.raises((KasaError, HygienicLinkError), match=message):
        link_source(source, generation="g1")


def test_unknown_generation_fails_closed():
    with pytest.raises(ValueError, match="generation"):
        preflight("fa math\nka 1\n", generation="g2")


def test_g1_manifest_tampering_rejected(tmp_path):
    root = tmp_path / "repo"
    g1 = root / "stdlib/g1"
    g1.mkdir(parents=True)
    for filename in ("catalog.json", "math.kasa", "collections.kasa"):
        (g1 / filename).write_bytes((ROOT / "stdlib/g1" / filename).read_bytes())
    (g1 / "math.kasa").write_bytes((g1 / "math.kasa").read_bytes() + b"\n# tampered\n")
    with pytest.raises(G1CatalogError, match="hash mismatch"):
        link_source(CASES[0][1], root=root, generation="g1")


def test_g1_cli_is_explicit(tmp_path, capsys):
    from link_g124_native import main
    app = tmp_path / "demo.kasa"
    app.write_text(CASES[0][1], encoding="utf-8")
    assert main([str(app)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert "__kasa_g05_math_kasa_total" in output.out
    assert "fa math" not in output.out
