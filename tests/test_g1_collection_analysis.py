"""Experimental G1 collection analysis: direct pure-Kasa execution only.

Not catalog-pinned, importable, native, KBC, or browser module verification.
"""
from __future__ import annotations

import io
from pathlib import Path

import pytest

from kasa import Interpreter, parse

ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = ROOT / "stdlib/g1/collections.kasa"


def execute(app: str) -> str:
    library = COLLECTIONS.read_text(encoding="utf-8")
    stdout = io.StringIO()
    Interpreter(stdout=stdout).run(parse(library + "\n" + app))
    return stdout.getvalue()


@pytest.mark.parametrize(("literal", "expected"), [
    ("[]", "0"),
    ("[7]", "1"),
    ("[2, 2, 2]", "1"),
    ("[1, 2, 1, 3, 2]", "3"),
    ("[0, -1, 0, -1, 9]", "3"),
    ('["Ama", "Kofi", "Ama"]', "2"),
    ("[nokware, atoro, nokware]", "2"),
])
def test_count_distinct(literal, expected):
    assert execute(f"ka kasa_count_distinct({literal})\n") == expected + "\n"


@pytest.mark.parametrize(("literal", "expected"), [
    ("[]", "nokware"),
    ("[42]", "nokware"),
    ("[8, 8, 8]", "nokware"),
    ("[8, 8, 9]", "atoro"),
    ('["Kasa", "Kasa"]', "nokware"),
    ("[nokware, atoro]", "atoro"),
])
def test_all_equal(literal, expected):
    assert execute(f"ka kasa_all_equal({literal})\n") == expected + "\n"


def test_read_only_and_existing_search_helpers():
    source = (
        "ma values = [4, 5, 4, 6]\n"
        "ka kasa_count_distinct(values)\n"
        "ka kasa_all_equal(values)\n"
        "ka kasa_first_index(values, 4)\n"
        "ka kasa_last_index(values, 4)\n"
        "ka tentɛn(values)\n"
        "ka values[0]\n"
        "ka values[3]\n"
    )
    assert execute(source) == "3\natoro\n0\n2\n4\n4\n6\n"


def test_experimental_only_not_catalog_exported():
    import json
    catalog = json.loads((ROOT / "stdlib/catalog.json").read_text(encoding="utf-8"))
    assert all("kasa_count_distinct" not in entry["exports"] for entry in catalog["modules"])
    assert all("kasa_all_equal" not in entry["exports"] for entry in catalog["modules"])
