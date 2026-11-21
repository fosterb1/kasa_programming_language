"""Experimental G1 numeric analytics in the Python reference runtime only.

Not available from the pinned catalog, native imports, or browser modules.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "stdlib/g1/math.kasa"


def execute(app: str) -> str:
    source = LIBRARY.read_text(encoding="utf-8") + "\n" + app
    output = io.StringIO()
    Interpreter(stdout=output).run(parse(source))
    return output.getvalue()


@pytest.mark.parametrize(("values", "expected"), [
    ("[]", "0"),
    ("[7]", "7"),
    ("[1, 2, 3]", "6"),
    ("[-3, 2, 1]", "0"),
    ("[100, -25, -25]", "50"),
])
def test_total(values, expected):
    assert execute(f"ka kasa_total({values})\n") == expected + "\n"


@pytest.mark.parametrize(("values", "fallback", "expected"), [
    ("[]", "-1", "-1"),
    ("[2, 3]", "0", "2.5"),
    ("[1, 2, 3, 4]", "0", "2.5"),
    ("[-2, -3]", "0", "-2.5"),
])
def test_average_or(values, fallback, expected):
    assert execute(f"ka kasa_average_or({values}, {fallback})\n") == expected + "\n"


@pytest.mark.parametrize(("values", "threshold", "expected"), [
    ("[]", "50", "0"),
    ("[50, 51, 49, 80]", "50", "2"),
    ("[1, 2, 3]", "3", "0"),
    ("[-5, -3, 0, 4]", "-4", "3"),
])
def test_count_above(values, threshold, expected):
    assert execute(f"ka kasa_count_above({values}, {threshold})\n") == expected + "\n"


def test_preserves_inputs_and_existing_min_max():
    app = (
        "ma scores = [10, 20, 30]\n"
        "ka kasa_total(scores)\n"
        "ka kasa_count_above(scores, 10)\n"
        "ka kasa_min_or(scores, -1)\n"
        "ka kasa_max_or(scores, -1)\n"
        "ka tentɛn(scores)\n"
        "ka scores[0]\n"
        "ka scores[2]\n"
    )
    assert execute(app) == "60\n2\n10\n30\n3\n10\n30\n"


def test_not_exported_through_pinned_g0_catalog():
    catalog = json.loads((ROOT / "stdlib/catalog.json").read_text(encoding="utf-8"))
    names = {"kasa_total", "kasa_average_or", "kasa_count_above"}
    assert not any(names.intersection(module["exports"]) for module in catalog["modules"])
