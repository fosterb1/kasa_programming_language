"""G0.5a restricted linker: source hygiene and self-contained semantics."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from link_kasa_modules_hygienic import HygienicLinkError, link_source, write_linked_source
    from run_kasa_modules_experimental import execute_module_source
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa import Interpreter, parse
from kasa.core import KasaError


SOURCE = (
    "fa math firi stdlib: m\n"
    "fa collections firi stdlib: c\n"
    "ma items = [10, 20, 30]\n"
    "ka m.kasa_sum(items)\n"
    "ka c.kasa_contains(items, 20)\n"
)


def _normal_run(source):
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(source))
    return out.getvalue()


def _experimental_run(source):
    out = io.StringIO()
    execute_module_source(source, stdout=out)
    return out.getvalue()


def test_reference_output_matches_prelinked_portable_source():
    linked = link_source(SOURCE)
    assert _normal_run(linked) == "60\nnokware\n"
    assert _normal_run(linked) == _experimental_run(SOURCE)
    assert "fa math" not in linked
    assert "m.kasa_sum" not in linked
    assert "dwumadie __kasa_g05_math_kasa_sum(" in linked
    assert "dwumadie __kasa_g05_collections_kasa_contains(" in linked


def test_app_names_do_not_capture_module_functions():
    source = (
        "fa math firi stdlib: m\n"
        "dwumadie kasa_sum(x)\n sanma 999\nawiei\n"
        "ma kasa_sum = 123\n"
        "ka m.kasa_sum([1, 2, 3])\n"
    )
    assert _normal_run(link_source(source)) == _experimental_run(source) == "6\n"


def test_literals_are_not_string_rewritten():
    source = (
        'fa math firi stdlib: m\n'
        'ka "m.kasa_sum \\" text"\n'
        "ka m.kasa_sum([1, 2])\n"
    )
    assert _normal_run(link_source(source)) == _experimental_run(source)


def test_nested_calls_and_private_functions_keep_name_isolation():
    source = (
        "fa math firi stdlib: m\n"
        "dwumadie demo(x)\n"
        "    sanma m.kasa_sum([x, m.kasa_abs(-2)])\n"
        "awiei\n"
        "ka demo(5)\n"
    )
    assert _normal_run(link_source(source)) == _experimental_run(source) == "7\n"


@pytest.mark.parametrize("source, reason", [
    ("fa math firi stdlib: m\nka m.kasa_sum\n", "Only direct module"),
    ("fa math firi stdlib: m\nma __kasa_g05_math_kasa_sum = 5\n", "reserved internal"),
    ("fa math firi stdlib: m\ndwumadie __kasa_g05_math_kasa_sum()\n sanma 1\nawiei\n", "reserved internal"),
    ("fa math firi stdlib: m\nka m.private(1)\n", "does not export"),
    ("fa math firi stdlib: m\nfa collections firi stdlib: m\nka 1\n", "alias reused"),
])
def test_linker_fails_closed(source, reason):
    with pytest.raises((HygienicLinkError, KasaError), match=reason):
        link_source(source)


def test_no_writes_on_failed_preflight(tmp_path):
    output = ROOT / "build" / "g05-linked" / "only-testing-existing-target.kasa"
    # The writer may refuse before touching the output directory; neither
    # program source nor arbitrary temp files can be overwritten.
    app = tmp_path / "bad.kasa"
    app.write_text("fa math firi stdlib: m\nka m.private(1)\n", encoding="utf-8")
    before = app.read_bytes()
    with pytest.raises(KasaError, match="does not export"):
        write_linked_source(app, output)
    assert app.read_bytes() == before
    assert not output.exists()
